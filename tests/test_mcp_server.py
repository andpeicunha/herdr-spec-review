import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from specreview.ainotes import add_note_to_file
from specreview.mcp_server import handle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(name, arguments=None):
    response = handle(
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": arguments or {}}}
    )
    result = response["result"]
    return result["content"][0]["text"], result["isError"]


class McpServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self.tmp.name)
        subprocess.run(["git", "-C", self.repo, "init", "-q", "-b", "main"], check=True)
        self.change = os.path.join(self.repo, "openspec", "changes", "add-login")
        os.makedirs(self.change)
        self.proposal = os.path.join(self.change, "proposal.md")
        with open(self.proposal, "w", encoding="utf-8") as out:
            out.write("## Why\n\nLogin is missing.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_initialize_and_tools_list(self):
        init = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
        tools = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        self.assertEqual(init["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual(init["result"]["serverInfo"]["name"], "spec-review")
        self.assertIn("Only call open_artifact when the user asks", init["result"]["instructions"])
        self.assertEqual(
            [tool["name"] for tool in tools["result"]["tools"]],
            ["list_open_changes", "list_artifacts", "open_artifact", "pending_notes"],
        )

    def test_notifications_get_no_response_and_unknown_methods_error(self):
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})["error"]["code"], -32601)

    def test_list_open_changes_and_artifacts(self):
        add_note_to_file(self.proposal, 3, 3, "Login is missing.", "Which login?")

        changes, error = call("list_open_changes", {"repo": self.change})
        artifacts, _ = call("list_artifacts", {"change_path": self.change})

        self.assertFalse(error)
        self.assertIn(f"- add-login [main] {self.change} (1 pending note(s))", changes)
        self.assertIn(f"- {self.proposal} (1 pending note(s))", artifacts)

    def test_pending_notes(self):
        add_note_to_file(self.proposal, 3, 3, "Login is missing.", "Which login?")

        text, error = call("pending_notes", {"path": self.proposal})

        self.assertFalse(error)
        self.assertIn('NOTE-001 (lines 3-3) on "Login is missing.": Which login?', text)

    def test_open_artifact_errors(self):
        with patch.dict("os.environ", {}, clear=True):
            text, error = call("open_artifact", {"path": self.proposal})
        self.assertTrue(error)
        self.assertIn("HERDR_PANE_ID", text)

        with patch.dict("os.environ", {"HERDR_PANE_ID": "w1:p1"}):
            text, error = call("open_artifact", {"path": os.path.join(self.repo, "README.md")})
        self.assertTrue(error)
        self.assertIn("File not found", text)

        text, error = call("open_artifact", {})
        self.assertTrue(error)
        self.assertIn("Missing required argument: path", text)

    @patch("specreview.cli.open_reader", return_value=(True, "w1:p9"))
    def test_open_artifact_targets_the_calling_pane(self, open_reader):
        with patch.dict("os.environ", {"HERDR_PANE_ID": "w1:p1"}):
            text, error = call("open_artifact", {"path": self.proposal})

        self.assertFalse(error)
        self.assertEqual(open_reader.call_args.args[0], "w1:p1")
        self.assertEqual(open_reader.call_args.kwargs["artifact"], self.proposal)
        self.assertIn("w1:p9", text)

    def test_stdio_round_trip_through_bin_script(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_open_changes", "arguments": {}}},
        ]
        result = subprocess.run(
            [os.path.join(ROOT, "bin", "spec-review-mcp")],
            input="\n".join(json.dumps(r) for r in requests) + "\n",
            capture_output=True, text=True, cwd=self.change, timeout=20,
        )
        responses = [json.loads(line) for line in result.stdout.splitlines()]

        self.assertEqual([r["id"] for r in responses], [1, 2])
        self.assertIn("add-login [main]", responses[1]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
