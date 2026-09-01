import os
import sys
from typing import List, Optional  # Optional still needed for ctx: Optional[Context]

from mcp.server.fastmcp import Context, FastMCP

# Use absolute imports when running as a script
try:
    # When installed as a package
    from .analysis import ThoughtAnalyzer
    from .logging_conf import configure_logging
    from .models import ThoughtData, ThoughtStage
    from .storage import StorageRegistry, normalize_namespace
except ImportError:
    # When run directly
    from mcp_sequential_thinking.analysis import ThoughtAnalyzer
    from mcp_sequential_thinking.logging_conf import configure_logging
    from mcp_sequential_thinking.models import ThoughtData, ThoughtStage
    from mcp_sequential_thinking.storage import StorageRegistry, normalize_namespace

logger = configure_logging("sequential-thinking.server")


# TRANSPORT_TYPE: stdio (default) | sse | streamable-http. MCP_HOST/MCP_PORT are
# only used for the two network transports (see .env.example).
mcp = FastMCP(
    "sequential-thinking",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8804")),
)

storage_dir = os.environ.get("MCP_STORAGE_DIR", None)
registry = StorageRegistry(storage_dir)

# One server process serves every agent, so which store a call lands in is
# decided per REQUEST, not per process: the `session` argument wins, then the
# HTTP header, then the query string on the URL, then MCP_DEFAULT_SESSION.
# SESSION_REQUIRED (default on) makes an unresolved namespace an error instead
# of a silent merge into "default" - the failure this whole mechanism exists to
# prevent. Set SESSION_REQUIRED=0 for a single-user server where that is noise.
SESSION_HEADER = "X-Thinking-Session"
SESSION_QUERY_PARAM = "session"
DEFAULT_SESSION_ENV = os.environ.get("MCP_DEFAULT_SESSION", "")
SESSION_REQUIRED = os.environ.get("SESSION_REQUIRED", "1").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)

_NO_SESSION_MESSAGE = (
    "No thinking session resolved. Every call must name the store it writes to, so "
    "two targets analyzed at the same time never share one history. Fix it in any of "
    f"these ways: pass session=\"<target>\" on the call (e.g. the ida-mcp database id); "
    f"add ?{SESSION_QUERY_PARAM}=<target> to the server URL or the {SESSION_HEADER} "
    "header in your MCP client config; or set MCP_DEFAULT_SESSION on the server."
)


def _http_request(ctx: Optional[Context]):
    """Return the HTTP request behind this call, or None.

    Present for the sse / streamable-http transports (the MCP SDK passes the
    Starlette Request through to the tool's request context) and absent for
    stdio, where there is no request to carry a header or query string.
    """
    if ctx is None:
        return None
    try:
        # Context.request_context raises when the tool runs outside a request.
        return getattr(ctx.request_context, "request", None)
    except (ValueError, AttributeError):
        return None


def _resolve_session(session: Optional[str], ctx: Optional[Context]) -> str:
    """Resolve which session namespace this call operates on.

    Args:
        session: The tool's explicit `session` argument, if the caller passed one.
        ctx: MCP context, used to reach the HTTP header / query string.

    Returns:
        str: The normalized namespace.

    Raises:
        ValueError: If nothing names a session and SESSION_REQUIRED is on, or if
            the name that was given is not a valid namespace.
    """
    candidates = [session]

    request = _http_request(ctx)
    if request is not None:
        headers = getattr(request, "headers", None)
        if headers is not None:
            candidates.append(headers.get(SESSION_HEADER))
        query_params = getattr(request, "query_params", None)
        if query_params is not None:
            candidates.append(query_params.get(SESSION_QUERY_PARAM))

    candidates.append(DEFAULT_SESSION_ENV)

    for candidate in candidates:
        if candidate and candidate.strip():
            return normalize_namespace(candidate)

    if SESSION_REQUIRED:
        raise ValueError(_NO_SESSION_MESSAGE)
    return "default"


@mcp.tool()
async def process_thought(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    stage: str,
    tags: Optional[List[str]] = None,
    axioms_used: Optional[List[str]] = None,
    assumptions_challenged: Optional[List[str]] = None,
    is_revision: bool = False,
    revises_thought_number: Optional[int] = None,
    branch_from_thought: Optional[int] = None,
    branch_id: Optional[str] = None,
    session: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict:
    """Add a sequential thought with its metadata.

    Args:
        thought: The content of the thought
        thought_number: The sequence number of this thought
        total_thoughts: The total expected thoughts in the sequence
        next_thought_needed: Whether more thoughts are needed after this one
        stage: The thinking stage (Problem Definition, Research, Analysis, Synthesis, Conclusion)
        tags: Optional keywords or categories for the thought
        axioms_used: Optional list of principles or axioms used in this thought
        assumptions_challenged: Optional list of assumptions challenged by this thought
        is_revision: Whether this thought revises an earlier thought
        revises_thought_number: The number of the earlier thought being revised (required if is_revision is true)
        branch_from_thought: The thought number this thought branches from, to explore an alternative path
        branch_id: Identifier for the branch (letters, digits, '-', '_'; max 64 chars; requires branch_from_thought)
        session: The thinking session this thought belongs to - one store per analysis
            target, e.g. the ida-mcp database id ("storport"). Thoughts, summaries and
            back-references never cross a session boundary. Falls back to the server
            URL / header / MCP_DEFAULT_SESSION when omitted.
        ctx: Optional MCP context object

    Returns:
        dict: Analysis of the processed thought
    """
    # Normalize optional list arguments (avoid mutable default arguments).
    tags = tags or []
    axioms_used = axioms_used or []
    assumptions_challenged = assumptions_challenged or []

    try:
        namespace = _resolve_session(session, ctx)
        storage = registry.get(namespace)

        # Log the request
        logger.info(
            f"[{namespace}] Processing thought #{thought_number}/{total_thoughts} in stage '{stage}'"
        )

        # Report progress if context is available
        if ctx:
            await ctx.report_progress(thought_number - 1, total_thoughts)

        # Convert stage string to enum
        thought_stage = ThoughtStage.from_string(stage)

        # Create thought data object with defaults for optional fields
        thought_data = ThoughtData(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            stage=thought_stage,
            tags=tags,
            axioms_used=axioms_used,
            assumptions_challenged=assumptions_challenged,
            is_revision=is_revision,
            revises_thought_number=revises_thought_number,
            branch_from_thought=branch_from_thought,
            branch_id=branch_id,
        )

        # Store (validation already happened during ThoughtData construction)
        storage.add_thought(thought_data)

        # Get all thoughts for analysis
        all_thoughts = storage.get_all_thoughts()

        # Analyze the thought
        analysis = ThoughtAnalyzer.analyze_thought(thought_data, all_thoughts)

        # Name the store this landed in, so a caller can see at once that its
        # thought went where it meant it to go.
        analysis["thoughtAnalysis"]["context"]["session"] = namespace

        # Log success
        logger.info(f"[{namespace}] Successfully processed thought #{thought_number}")

        return analysis
    except Exception as e:
        logger.error(f"Error processing thought: {str(e)}")

        return {"error": str(e), "status": "failed"}


@mcp.tool()
def generate_summary(session: Optional[str] = None, ctx: Optional[Context] = None) -> dict:
    """Generate a summary of one session's thinking process.

    Args:
        session: The thinking session to summarize (see process_thought). Only that
            session's chains are counted - stages, timeline, branches and
            percentComplete never mix in another target's work.
        ctx: Optional MCP context object

    Returns:
        dict: Summary of the thinking process
    """
    try:
        namespace = _resolve_session(session, ctx)
        storage = registry.get(namespace)

        logger.info(f"[{namespace}] Generating thinking process summary")

        # Get all thoughts
        all_thoughts = storage.get_all_thoughts()

        # Generate summary
        summary = ThoughtAnalyzer.generate_summary(all_thoughts)
        if isinstance(summary.get("summary"), dict):
            summary["summary"]["session"] = namespace
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {"error": str(e), "status": "failed"}


@mcp.tool()
def clear_history(session: Optional[str] = None, ctx: Optional[Context] = None) -> dict:
    """Clear one session's thought history.

    Scoped to a single session, so it can no longer wipe another target's work -
    but every agent working on THIS target shares this history, so an orchestrator
    running subagents still has no safe moment to call it.

    Args:
        session: The thinking session to wipe (see process_thought).
        ctx: Optional MCP context object

    Returns:
        dict: Status message
    """
    try:
        namespace = _resolve_session(session, ctx)
        storage = registry.get(namespace)

        logger.info(f"[{namespace}] Clearing thought history")
        storage.clear_history()
        return {
            "status": "success",
            "message": f"Thought history cleared for session '{namespace}'",
            "session": namespace,
        }
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return {"error": str(e), "status": "failed"}


@mcp.tool()
def export_session(
    file_path: str, session: Optional[str] = None, ctx: Optional[Context] = None
) -> dict:
    """Export one thinking session to a file.

    Args:
        file_path: Path to save the exported session. Resolved inside that
            session's own ``exports/`` directory on the server host.
        session: The thinking session to export (see process_thought).
        ctx: Optional MCP context object

    Returns:
        dict: Status message
    """
    try:
        namespace = _resolve_session(session, ctx)
        storage = registry.get(namespace)

        logger.info(f"[{namespace}] Exporting session to {file_path}")
        storage.export_session(file_path)
        return {
            "status": "success",
            "message": f"Session '{namespace}' exported to {file_path}",
            "session": namespace,
        }
    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}")
        return {"error": str(e), "status": "failed"}


@mcp.tool()
def import_session(
    file_path: str, session: Optional[str] = None, ctx: Optional[Context] = None
) -> dict:
    """Import a thinking session from a file, REPLACING that session's history.

    Scoped to a single session, but within it this is as destructive as
    clear_history: the current history is replaced, not merged.

    Args:
        file_path: Path to the file to import, inside that session's ``exports/``.
        session: The thinking session to import into (see process_thought).
        ctx: Optional MCP context object

    Returns:
        dict: Status message
    """
    try:
        namespace = _resolve_session(session, ctx)
        storage = registry.get(namespace)

        logger.info(f"[{namespace}] Importing session from {file_path}")
        storage.import_session(file_path)
        return {
            "status": "success",
            "message": f"Session '{namespace}' imported from {file_path}",
            "session": namespace,
        }
    except Exception as e:
        logger.error(f"Error importing session: {str(e)}")
        return {"error": str(e), "status": "failed"}


@mcp.tool()
def list_sessions() -> dict:
    """List the thinking sessions this server holds.

    Use it to check which store a target's chain actually landed in - a
    misspelled session name creates a new, empty store rather than an error.

    Returns:
        dict: ``sessions``, each with session name, thought count, last-updated
        timestamp and whether it is loaded in memory.
    """
    try:
        sessions = registry.list_namespaces()
        logger.info(f"Listing {len(sessions)} thinking session(s)")
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return {"error": str(e), "status": "failed"}


def main() -> None:
    """Entry point for the MCP server."""
    logger.info("Starting Sequential Thinking MCP server")

    # Ensure UTF-8 encoding for stdin/stdout
    if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    if hasattr(sys.stdin, "buffer") and sys.stdin.encoding != "utf-8":
        import io

        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", line_buffering=True)

    # Flush stdout to ensure no buffered content remains
    sys.stdout.flush()

    # Run the MCP server
    transport = os.environ.get("TRANSPORT_TYPE", "stdio").strip().lower()
    if transport not in ("stdio", "sse", "streamable-http"):
        transport = "stdio"
    mcp.run(transport=transport)


if __name__ == "__main__":
    # When running the script directly, ensure we're in the right directory.
    # Add the parent directory to sys.path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Print debug information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    logger.info(f"Parent directory added to path: {parent_dir}")

    # Run the server
    main()
