import asyncio
import os
import tempfile
import unittest

# The server module builds its storage registry at import time and is imported
# once for the whole module, so the throwaway storage directory is owned here
# rather than by either test class - a per-class temp dir would be deleted out
# from under the registry the moment the first class finished.
# MCP_DEFAULT_SESSION stands in for the per-deployment default a real client
# sets in its URL/header, so the first class's calls need no `session` argument.
_TMP = None
_SERVER = None


def setUpModule():
    global _TMP, _SERVER
    _TMP = tempfile.TemporaryDirectory()
    os.environ["MCP_STORAGE_DIR"] = _TMP.name
    os.environ["MCP_DEFAULT_SESSION"] = "test-default"
    from mcp_sequential_thinking import server  # noqa: E402
    _SERVER = server


def tearDownModule():
    _TMP.cleanup()
    os.environ.pop("MCP_STORAGE_DIR", None)
    os.environ.pop("MCP_DEFAULT_SESSION", None)


class TestProcessThought(unittest.TestCase):
    """Test cases for the process_thought server tool."""

    @classmethod
    def setUpClass(cls):
        cls.server = _SERVER

    def setUp(self):
        self.server.registry.get("test-default").clear_history()

    def test_process_thought_returns_analysis(self):
        """Awaiting process_thought (ctx=None) returns analysis without raising
        or emitting an unawaited-coroutine RuntimeWarning."""
        result = asyncio.run(
            self.server.process_thought(
                thought="A first thought",
                thought_number=1,
                total_thoughts=2,
                next_thought_needed=True,
                stage="Analysis",
                ctx=None,
            )
        )

        self.assertIsInstance(result, dict)
        self.assertIn("thoughtAnalysis", result)

    def test_process_thought_omitting_optional_lists(self):
        """Calling without the optional list args still returns analysis
        (regression for mutable-default replacement)."""
        result = asyncio.run(
            self.server.process_thought(
                thought="Another thought",
                thought_number=1,
                total_thoughts=1,
                next_thought_needed=False,
                stage="Conclusion",
            )
        )

        self.assertIsInstance(result, dict)
        self.assertIn("thoughtAnalysis", result)

    def test_process_thought_revision_returns_revision_of(self):
        """A revision thought reports revisionOf with a snippet of the
        revised mainline thought."""
        asyncio.run(
            self.server.process_thought(
                thought="Original take on the problem",
                thought_number=1,
                total_thoughts=3,
                next_thought_needed=True,
                stage="Problem Definition",
            )
        )

        result = asyncio.run(
            self.server.process_thought(
                thought="Sharper framing of the problem",
                thought_number=2,
                total_thoughts=3,
                next_thought_needed=True,
                stage="Problem Definition",
                is_revision=True,
                revises_thought_number=1,
            )
        )

        block = result["thoughtAnalysis"]["analysis"]
        self.assertTrue(block["isRevision"])
        self.assertEqual(block["revisedThought"], 1)
        self.assertEqual(block["revisionOf"]["thoughtNumber"], 1)
        self.assertIn("Original take", block["revisionOf"]["snippet"])

    def test_process_thought_invalid_revision_params_fail_gracefully(self):
        """Validation errors surface as {'status': 'failed'} instead of raising."""
        result = asyncio.run(
            self.server.process_thought(
                thought="Bad revision",
                thought_number=1,
                total_thoughts=1,
                next_thought_needed=False,
                stage="Conclusion",
                is_revision=True,  # missing revises_thought_number
            )
        )

        self.assertEqual(result.get("status"), "failed")
        self.assertIn("error", result)


class _FakeContext:
    """Stand-in for the MCP Context over an HTTP transport.

    Only the two things the server reads are modelled: the Starlette request
    reachable at ``ctx.request_context.request`` (with its headers and query
    string), and the progress callback ``process_thought`` awaits.
    """

    class _Request:
        def __init__(self, headers, query_params):
            self.headers = headers
            self.query_params = query_params

    class _RequestContext:
        def __init__(self, request):
            self.request = request

    def __init__(self, headers=None, query_params=None):
        self.request_context = self._RequestContext(
            self._Request(headers or {}, query_params or {})
        )

    async def report_progress(self, *args, **kwargs):
        return None


class TestSessionNamespaces(unittest.TestCase):
    """The store a call lands in is decided per request, not per process."""

    @classmethod
    def setUpClass(cls):
        cls.server = _SERVER

    def setUp(self):
        # The module read its env at import time; these tests drive the two
        # switches directly so they do not depend on import order.
        self._required = self.server.SESSION_REQUIRED
        self._default_env = self.server.DEFAULT_SESSION_ENV
        self.server.SESSION_REQUIRED = True
        self.server.DEFAULT_SESSION_ENV = ""

    def tearDown(self):
        self.server.SESSION_REQUIRED = self._required
        self.server.DEFAULT_SESSION_ENV = self._default_env

    def _thought(self, text, number, total, session=None, ctx=None, **kwargs):
        return asyncio.run(
            self.server.process_thought(
                thought=text,
                thought_number=number,
                total_thoughts=total,
                next_thought_needed=True,
                stage="Analysis",
                session=session,
                ctx=ctx,
                **kwargs,
            )
        )

    def test_two_sessions_do_not_see_each_other(self):
        """Summaries, and the analysis of a call, only ever count one session."""
        self._thought("Storport thought", 1, 1, session="storport")
        self._thought("Bfs thought one", 1, 2, session="bfs")
        result = self._thought("Bfs thought two", 2, 2, session="bfs")

        self.assertEqual(result["thoughtAnalysis"]["context"]["session"], "bfs")
        self.assertEqual(result["thoughtAnalysis"]["context"]["thoughtHistoryLength"], 2)

        storport = self.server.generate_summary(session="storport")["summary"]
        bfs = self.server.generate_summary(session="bfs")["summary"]
        self.assertEqual(storport["totalThoughts"], 1)
        self.assertEqual(bfs["totalThoughts"], 2)
        self.assertEqual(storport["session"], "storport")

    def test_back_reference_does_not_cross_sessions(self):
        """A revision resolves against its own session, not a same-numbered
        thought another target left behind."""
        self._thought("Other target's first thought", 1, 2, session="other-target")
        self._thought("My first thought", 1, 2, session="mine")

        result = self._thought(
            "Correcting my first thought",
            2,
            2,
            session="mine",
            is_revision=True,
            revises_thought_number=1,
        )

        self.assertIn("My first thought", result["thoughtAnalysis"]["analysis"]["revisionOf"]["snippet"])

    def test_clear_history_is_scoped_to_one_session(self):
        self._thought("Kept", 1, 1, session="keep-me")
        self._thought("Wiped", 1, 1, session="wipe-me")

        self.server.clear_history(session="wipe-me")

        self.assertEqual(
            self.server.generate_summary(session="keep-me")["summary"]["totalThoughts"], 1
        )
        self.assertEqual(
            self.server.generate_summary(session="wipe-me")["summary"], "No thoughts recorded yet"
        )

    def test_header_and_query_resolve_the_session(self):
        """An HTTP client that configures the session once still gets isolation."""
        by_header = self._thought(
            "From a header", 1, 1, ctx=_FakeContext(headers={"X-Thinking-Session": "hdr-target"})
        )
        by_query = self._thought(
            "From a query string", 1, 1, ctx=_FakeContext(query_params={"session": "qry-target"})
        )

        self.assertEqual(by_header["thoughtAnalysis"]["context"]["session"], "hdr-target")
        self.assertEqual(by_query["thoughtAnalysis"]["context"]["session"], "qry-target")

    def test_explicit_argument_beats_header(self):
        result = self._thought(
            "Explicit wins",
            1,
            1,
            session="argument-target",
            ctx=_FakeContext(headers={"X-Thinking-Session": "header-target"}),
        )

        self.assertEqual(result["thoughtAnalysis"]["context"]["session"], "argument-target")

    def test_missing_session_is_refused_when_required(self):
        """Nothing is written when no session is named - the silent merge into
        a shared store is exactly what this mechanism prevents."""
        before = self.server.list_sessions()["sessions"]
        result = self._thought("Homeless thought", 1, 1)
        after = self.server.list_sessions()["sessions"]

        self.assertEqual(result.get("status"), "failed")
        self.assertIn("No thinking session resolved", result["error"])
        self.assertEqual(before, after)

    def test_missing_session_falls_back_when_not_required(self):
        self.server.SESSION_REQUIRED = False

        result = self._thought("Tolerated thought", 1, 1)

        self.assertEqual(result["thoughtAnalysis"]["context"]["session"], "default")

    def test_invalid_session_name_is_refused(self):
        result = self._thought("Traversal attempt", 1, 1, session="../../etc")

        self.assertEqual(result.get("status"), "failed")
        self.assertIn("Invalid session namespace", result["error"])

    def test_list_sessions_reports_what_is_on_disk(self):
        self._thought("One", 1, 1, session="listed-a")
        self._thought("Two", 1, 2, session="listed-b")
        self._thought("Three", 2, 2, session="listed-b")

        listed = {s["session"]: s for s in self.server.list_sessions()["sessions"]}

        self.assertEqual(listed["listed-a"]["thoughts"], 1)
        self.assertEqual(listed["listed-b"]["thoughts"], 2)
        self.assertIsNotNone(listed["listed-b"]["updatedAt"])


if __name__ == "__main__":
    unittest.main()
