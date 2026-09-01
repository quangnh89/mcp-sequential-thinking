import re
import shutil
import threading
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from .models import ThoughtData, ThoughtStage
from .logging_conf import configure_logging
from .storage_utils import (
    append_thought_to_jsonl,
    count_thoughts_in_jsonl,
    load_thoughts_from_file,
    load_thoughts_from_jsonl,
    prepare_thoughts_for_serialization,
    rewrite_jsonl,
    save_thoughts_to_file,
)

logger = configure_logging("sequential-thinking.storage")

# A session namespace is used as a directory name, so it is validated the same
# way ``branch_id`` is: a conservative charset, no separators, no dot-segments.
NAMESPACE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
DEFAULT_NAMESPACE = "default"


class ThoughtStorage:
    """Storage manager for thought data."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the storage manager.

        Args:
            storage_dir: Directory to store thought data files. If None, uses a default directory.
        """
        if storage_dir is None:
            # Use user's home directory by default
            home_dir = Path.home()
            self.storage_dir = home_dir / ".mcp_sequential_thinking"
        else:
            self.storage_dir = Path(storage_dir)

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Default session file (schema v2, append-only JSONL). The legacy v1
        # JSON file is only read once for migration.
        self.current_session_file = self.storage_dir / "current_session.jsonl"
        self.legacy_session_file = self.storage_dir / "current_session.json"
        self.lock_file = self.storage_dir / "current_session.lock"

        # Exports/imports are confined to a dedicated subdirectory so an export
        # can never clobber the session file (or its lock file). Created lazily
        # by export_session.
        self.export_dir = self.storage_dir / "exports"

        # Thread safety
        self._lock = threading.RLock()
        self.thought_history: List[ThoughtData] = []

        # Load existing session if available
        self._load_session()

    @staticmethod
    def _ensure_within(base: Path, candidate: str) -> Path:
        """Resolve ``candidate`` and ensure it stays inside ``base``.

        Confines model-controlled export/import paths to the storage directory
        so a path like ``/etc/passwd`` or ``../../foo`` cannot escape it
        (CWE-22 / CWE-73).

        Args:
            base: The directory the path must stay within (e.g. storage_dir).
            candidate: The caller-supplied path (may be absolute or relative).

        Returns:
            Path: The resolved, contained path (safe to open).

        Raises:
            ValueError: If the resolved path is outside ``base``.
        """
        base_r = base.resolve()
        candidate_path = Path(candidate)
        if candidate_path.is_absolute():
            resolved = candidate_path.resolve()
        else:
            resolved = (base_r / candidate_path).resolve()

        try:
            resolved.relative_to(base_r)
        except ValueError:
            # Log the full resolved base server-side, but keep it out of the
            # client-facing message (it would leak the user's home directory).
            logger.error(f"Rejected path '{candidate}': resolves outside '{base_r}'")
            raise ValueError(
                f"Path '{candidate}' resolves outside the allowed export directory. "
                "Export/import paths must stay within the storage area."
            )
        return resolved

    def _load_session(self) -> None:
        """Load thought history from the current session file if it exists.

        If no v2 JSONL session exists but a legacy v1 JSON session does, the
        v1 file is migrated to JSONL once (lossless, idempotent).
        """
        with self._lock:
            if not self.current_session_file.exists() and self.legacy_session_file.exists():
                self._migrate_v1_session()
                return

            # backup_on_corruption=True: this is our own session file, so a
            # corrupt or invalid file is backed up (or a truncated final line
            # dropped) and we recover rather than crashing the server on startup.
            self.thought_history = load_thoughts_from_jsonl(
                self.current_session_file, self.lock_file, backup_on_corruption=True
            )

    def _migrate_v1_session(self) -> None:
        """Migrate a legacy v1 JSON session file to the v2 JSONL format.

        The v1 file is loaded (with the usual corruption recovery), rewritten
        as JSONL, and then renamed to ``current_session.json.migrated-to-v2``
        so a second start only finds the JSONL file.
        """
        thoughts = load_thoughts_from_file(
            self.legacy_session_file, self.lock_file, backup_on_corruption=True
        )
        rewrite_jsonl(
            self.current_session_file,
            self.lock_file,
            prepare_thoughts_for_serialization(thoughts),
        )
        # On corruption the v1 file was already renamed to a .bak backup.
        if self.legacy_session_file.exists():
            migrated = self.legacy_session_file.with_name("current_session.json.migrated-to-v2")
            self.legacy_session_file.rename(migrated)
            logger.info(
                f"Migrated v1 session ({len(thoughts)} thoughts) to "
                f"{self.current_session_file}; original kept at {migrated}"
            )
        self.thought_history = thoughts

    def add_thought(self, thought: ThoughtData) -> None:
        """Add a thought to the history and append it to the session file.

        Args:
            thought: The thought data to add
        """
        # Memory update AND file append run under the lock so disk order
        # always matches memory order (RLock makes reentrancy harmless).
        with self._lock:
            self.thought_history.append(thought)
            append_thought_to_jsonl(
                self.current_session_file, self.lock_file, thought.to_dict(include_id=True)
            )

    def get_all_thoughts(self) -> List[ThoughtData]:
        """Get all thoughts in the current session.

        Returns:
            List[ThoughtData]: All thoughts in the current session
        """
        with self._lock:
            # Return a copy to avoid external modification
            return list(self.thought_history)

    def get_thoughts_by_stage(self, stage: ThoughtStage) -> List[ThoughtData]:
        """Get all thoughts in a specific stage.

        Args:
            stage: The thinking stage to filter by

        Returns:
            List[ThoughtData]: Thoughts in the specified stage
        """
        with self._lock:
            return [t for t in self.thought_history if t.stage == stage]

    def clear_history(self) -> None:
        """Clear the thought history and rewrite the session file."""
        with self._lock:
            self.thought_history.clear()
            rewrite_jsonl(self.current_session_file, self.lock_file, [])

    def export_session(self, file_path: str) -> None:
        """Export the current session to a file.

        Args:
            file_path: Path to save the exported session. Relative paths are
                resolved against the ``exports/`` subdirectory of the storage
                directory; the result must stay inside it.

        Raises:
            ValueError: If file_path resolves outside the export directory.
        """
        # Confine the caller-controlled path to export_dir before any file I/O,
        # so an export can never overwrite the session or lock file.
        file_path_obj = self._ensure_within(self.export_dir, file_path)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        with self._lock:
            # Use utility function to prepare thoughts for serialization
            thoughts_with_ids = prepare_thoughts_for_serialization(self.thought_history)
            
            # Create export-specific metadata
            metadata = {
                "exportedAt": datetime.now().isoformat(),
                "metadata": {
                    "totalThoughts": len(self.thought_history),
                    "stages": {
                        stage.value: len([t for t in self.thought_history if t.stage == stage])
                        for stage in ThoughtStage
                    }
                }
            }
        
        lock_file = file_path_obj.with_suffix('.lock')

        # Use utility function to save with proper locking
        save_thoughts_to_file(file_path_obj, thoughts_with_ids, lock_file, metadata)

    def import_session(self, file_path: str) -> None:
        """Import a session from a file.

        Args:
            file_path: Path to the file to import. Relative paths are resolved
                against the ``exports/`` subdirectory of the storage directory;
                the result must stay inside it.

        Raises:
            ValueError: If file_path resolves outside the export directory,
                if the file is not valid JSON, or if it contains semantically
                invalid thought data. In all error cases the input file and the
                current session are left untouched.
            FileNotFoundError: If the file doesn't exist.
            KeyError: If the file doesn't contain a 'thoughts' key.
        """
        # Confine the caller-controlled path to export_dir before any file I/O.
        file_path_obj = self._ensure_within(self.export_dir, file_path)
        lock_file = file_path_obj.with_suffix('.lock')

        # load_thoughts_from_file returns [] for missing files (recovery
        # behaviour for the server's own session file). For an import that
        # would silently wipe the current session, so reject explicitly.
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Import file not found: {file_path}")

        # Use utility function to load thoughts. backup_on_corruption defaults to
        # False, so a malformed/invalid input file raises instead of renaming the
        # caller's file or silently wiping the current session.
        thoughts = load_thoughts_from_file(file_path_obj, lock_file)

        with self._lock:
            self.thought_history = thoughts
            rewrite_jsonl(
                self.current_session_file,
                self.lock_file,
                prepare_thoughts_for_serialization(thoughts),
            )


def normalize_namespace(value: str) -> str:
    """Normalize and validate a session namespace.

    Args:
        value: The caller-supplied namespace (any case, surrounding whitespace ok).

    Returns:
        str: The normalized namespace, safe to use as a single path component.

    Raises:
        ValueError: If the namespace is empty or outside NAMESPACE_PATTERN.
    """
    normalized = (value or "").strip().lower()
    if not NAMESPACE_PATTERN.match(normalized):
        raise ValueError(
            f"Invalid session namespace {value!r}. Use 1-64 characters from "
            "[a-z0-9_.-], starting with a letter or digit - e.g. 'storport'."
        )
    return normalized


class StorageRegistry:
    """One ``ThoughtStorage`` per session namespace.

    The server process is shared by every agent that talks to it, so a single
    store means one agent's thoughts land in another agent's summary,
    back-references and related-thought echoes. The registry gives each
    namespace its own directory under ``<root>/spaces/<namespace>``, which is a
    plain ``ThoughtStorage`` - the session file, its lock and the ``exports/``
    guard all come along unchanged.

    Stores are created lazily on first use and cached, so listing or restarting
    never has to load a namespace nobody asked for.
    """

    SPACES_DIRNAME = "spaces"

    def __init__(self, root: Optional[str] = None):
        """Initialize the registry.

        Args:
            root: Storage root (``MCP_STORAGE_DIR``). If None, uses the same
                default directory a bare ``ThoughtStorage`` would.
        """
        if root is None:
            self.root = Path.home() / ".mcp_sequential_thinking"
        else:
            self.root = Path(root)

        self.spaces_dir = self.root / self.SPACES_DIRNAME
        self.spaces_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._stores: Dict[str, ThoughtStorage] = {}

        # A store written by an older (single-store) release lives directly in
        # the root; adopt it as the "default" namespace so no history is lost.
        self._migrate_flat_store()

    def get(self, namespace: str) -> ThoughtStorage:
        """Return the store for ``namespace``, creating it on first use.

        Args:
            namespace: Session namespace (validated by ``normalize_namespace``).

        Returns:
            ThoughtStorage: The store owning that namespace's history.
        """
        key = normalize_namespace(namespace)
        with self._lock:
            store = self._stores.get(key)
            if store is None:
                store = ThoughtStorage(str(self.spaces_dir / key))
                self._stores[key] = store
                logger.info(f"Opened thinking session '{key}' at {store.storage_dir}")
            return store

    def list_namespaces(self) -> List[Dict[str, Any]]:
        """List every namespace on disk, not just the ones loaded this run.

        Returns:
            List[Dict[str, Any]]: One entry per namespace with ``session``,
            ``thoughts``, ``updatedAt`` (ISO 8601, None if never written) and
            ``loaded`` (whether this process holds it in memory), sorted by name.
        """
        with self._lock:
            loaded = dict(self._stores)

        entries: List[Dict[str, Any]] = []
        for path in sorted(self.spaces_dir.iterdir() if self.spaces_dir.exists() else []):
            if not path.is_dir():
                continue

            name = path.name
            session_file = path / "current_session.jsonl"
            store = loaded.get(name)
            if store is not None:
                count = len(store.get_all_thoughts())
            else:
                count = count_thoughts_in_jsonl(session_file, path / "current_session.lock")

            updated_at = (
                datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()
                if session_file.exists()
                else None
            )
            entries.append(
                {
                    "session": name,
                    "thoughts": count,
                    "updatedAt": updated_at,
                    "loaded": store is not None,
                }
            )

        return entries

    def _migrate_flat_store(self) -> None:
        """Move a pre-namespace store from the root into ``spaces/default/``.

        Idempotent: it runs only when the root still holds a session file and
        ``spaces/default`` has none. The original is left behind renamed, the
        same way ``_migrate_v1_session`` keeps the v1 file.
        """
        flat_session = self.root / "current_session.jsonl"
        flat_legacy = self.root / "current_session.json"
        source = flat_session if flat_session.exists() else flat_legacy
        if not source.exists():
            return

        target_dir = self.spaces_dir / DEFAULT_NAMESPACE
        if (target_dir / source.name).exists():
            return

        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / source.name)

        # The exports of that store belong to the same namespace.
        flat_exports = self.root / "exports"
        if flat_exports.is_dir() and not (target_dir / "exports").exists():
            shutil.copytree(flat_exports, target_dir / "exports")

        migrated = source.with_name(source.name + ".migrated-to-spaces")
        source.rename(migrated)
        # The old lock file guards a path that no longer exists.
        flat_lock = self.root / "current_session.lock"
        if flat_lock.exists():
            flat_lock.unlink()

        logger.info(
            f"Migrated the pre-namespace store into {target_dir}; the original is kept at {migrated}"
        )
