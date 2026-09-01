# Changelog

## [Unreleased] - fork (binary-analysis-2 / quangnh89)

Everything below this heading is fork-only and has no upstream counterpart. Keep it
separate so `master` can still fast-forward from arben-adm and this branch rebases on top.

### Added
- **Session namespaces.** The history is no longer one store per process: each thinking
  session gets its own store under `<MCP_STORAGE_DIR>/spaces/<session>/`, and which one a
  call lands in is resolved PER REQUEST - the tool's new `session` argument first, then the
  `X-Thinking-Session` header, then `?session=` on the URL, then `MCP_DEFAULT_SESSION`.
  One shared HTTP server can now serve several analysis targets at once without their
  chains, summaries, `revisionOf` echoes and related-thought lookups mixing; `clear_history`
  and `import_session` likewise stop at the session boundary. `SESSION_REQUIRED` (default
  on) refuses a call that names no session rather than merging it into a shared store.
  A 0.7.0 store in the storage root is migrated once into `spaces/default/`.
- **`list_sessions` tool.** Lists the sessions on disk with thought counts and last-updated
  times - the way to notice that a misspelled session name opened a new, empty store.
- **Network transports.** `TRANSPORT_TYPE` (`stdio` | `sse` | `streamable-http`, default
  `stdio`) selects how the server is exposed, and `MCP_HOST` / `MCP_PORT` (default
  `127.0.0.1:8804`) bind the two network ones. Upstream only ever calls `mcp.run()`, which
  is stdio-only; this fork runs as a long-lived HTTP MCP shared by several agent sessions.
  An unrecognized `TRANSPORT_TYPE` falls back to `stdio` rather than failing to start.
- **Windows launcher layer** for the bundled-install flow: `run_server.bat` (reads `.env`
  via `load_env.bat`, validates `VENV_PATH`, launches `python -m mcp_sequential_thinking.server`),
  `load_env.bat`, `.env.example`, and `requirements.txt` mirroring `[project].dependencies`.

### Changed
- `mcp` dependency floor raised to `>=1.28.0` (kept `<2.0.0`): the version this fork has
  verified for the `streamable-http` transport.
- `.gitignore` also excludes `.env` and the runtime session/export files, so a bundle built
  from tracked files alone can never carry machine paths or recorded thoughts.

## [0.6.1] - 2026-08-23

### Fixed
- `uvx mcp-sequential-thinking` failed with `ModuleNotFoundError: No module
  named 'mcp.server.fastmcp'` because the `mcp` dependency had no upper bound
  and `uvx` (unlike a `uv.lock`-pinned install) re-resolves against the
  published index, pulling in `mcp` 2.0.0, which removed `mcp.server.fastmcp`.
  The dependency is now pinned to `mcp>=1.2.0,<2.0.0`. The `[cli]` extra was
  also dropped since nothing in this project uses `mcp.cli`, `mcp dev`, or
  `mcp install`; it only pulled in unused packages (`typer`, `rich`, etc.).
  (#27)

## [0.6.0] - 2026-07-03

### Added
- **Thought revisions and branching**: `process_thought` accepts new optional
  parameters `is_revision`, `revises_thought_number`, `branch_from_thought` and
  `branch_id` to revise an earlier thought or fork an alternative line of
  reasoning. Cross-field validation enforces consistent usage. Analysis output
  reports `isRevision`/`revisedThought`/`branchId` (plus a `revisionOf` snippet
  for revisions), and `generate_summary` gains a `branches` object and a
  `revisionCount`. Progress metrics are based on mainline thoughts only, so
  revisions and branches no longer inflate completion beyond 100%.
- **Append-only JSONL session format (schema v2)**: the session now lives in
  `current_session.jsonl` (header record + one thought per line). `process_thought`
  is O(1) per call instead of rewriting the full history, and the file doubles as
  an audit trail. A truncated final line (interrupted write) is dropped on load
  instead of invalidating the whole session. Existing v1 `current_session.json`
  files are migrated automatically and losslessly on first start; the original is
  kept as `current_session.json.migrated-to-v2`.
- JSON exports now carry a top-level `"version": 2` field. Legacy v0.5.0 exports
  (no version field) remain importable.
- CI workflow (GitHub Actions): test matrix on Linux/Windows with Python 3.10
  and 3.12, running pytest and mypy on every push and pull request.
- Release workflow publishing to PyPI via Trusted Publishing when a GitHub
  release is published (requires one-time Trusted Publisher setup on pypi.org).
- Dependabot configuration for pip and GitHub Actions dependencies.
- `SECURITY.md` with a private disclosure contact.

### Changed
- **Package renamed** from `sequential-thinking` to `mcp-sequential-thinking` for the PyPI
  release (the old name is occupied by a third-party fork). The console script
  `mcp-sequential-thinking` and the import package `mcp_sequential_thinking` are unchanged.
- **Breaking:** `export_session` and `import_session` are now confined to the
  `exports/` subdirectory of the storage directory (relative paths resolve to
  `~/.mcp_sequential_thinking/exports/` by default). This prevents an export from
  overwriting the active session file or its lock file.

### Fixed
- `import_session` no longer silently replaces the active session with an empty
  one when the given file is a valid JSON file without a `thoughts` key, or when
  the file does not exist. Both cases now raise and leave the session untouched.
- Path-validation errors returned to the MCP client no longer leak the absolute
  storage path (e.g. the user's home directory); the full path is only logged
  server-side.
- `mypy` now passes cleanly: added missing type annotations in `analysis.py`
  (`stages`, `percent_complete`) and `server.py` (`main() -> None`), and removed
  duplicate `import os` / `import sys` in the `__main__` block of `server.py`.

## Version 0.5.0 (Unreleased)

### Code Quality Improvements

#### 1. Reduced Code Duplication in Storage Layer
- Created a new `storage_utils.py` module with shared utility functions
- Implemented reusable functions for file operations and serialization
- Standardized error handling and backup creation
- Improved consistency across serialization operations
- Optimized resource management with cleaner context handling

#### 2. API and Data Structure Improvements
- Added explicit parameter for ID inclusion in `to_dict()` method
- Created utility module with snake_case/camelCase conversion functions
- Eliminated flag-based solution in favor of explicit method parameters
- Improved readability with clearer, more explicit list comprehensions
- Eliminated duplicate calculations in analysis methods

## Version 0.4.0

### Major Improvements

#### 1. Serialization & Validation with Pydantic
- Converted `ThoughtData` from dataclass to Pydantic model
- Added automatic validation with field validators
- Maintained backward compatibility with existing code

#### 2. Thread-Safety in Storage Layer
- Added file locking with `portalocker` to prevent race conditions
- Added thread locks to protect shared data structures
- Made all methods thread-safe

#### 3. Fixed Division-by-Zero in Analysis
- Added proper error handling in `generate_summary` method
- Added safe calculation of percent complete with default values

#### 4. Case-Insensitive Stage Comparison
- Updated `ThoughtStage.from_string` to use case-insensitive comparison
- Improved user experience by accepting any case for stage names

#### 5. Added UUID to ThoughtData
- Added a unique identifier to each thought for better tracking
- Maintained backward compatibility with existing code

#### 6. Consolidated Logging Setup
- Created a central logging configuration in `logging_conf.py`
- Standardized logging across all modules

#### 7. Improved Package Entry Point
- Cleaned up the path handling in `run_server.py`
- Removed redundant code

### New Dependencies
- Added `portalocker` for file locking
- Added `pydantic` for data validation

## Version 0.3.0

Initial release with basic functionality:
- Sequential thinking process with defined stages
- Thought storage and retrieval
- Analysis and summary generation
