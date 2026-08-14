from __future__ import annotations

import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from owl_engine import (  # noqa: E402
    InMemoryStateStore,
    ObservationBasis,
    OwlEngine,
    OwlMcpService,
    StdioMcpServer,
    TargetBinding,
)


def binding(target_id: str = "hatchling") -> TargetBinding:
    return TargetBinding(
        target_id=target_id,
        name="Useful CLI",
        identity="this-instance",
        expected="a verified CLI improvement",
        scope="the authorized fixture",
    )


class HatchlingAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OwlEngine(InMemoryStateStore())

    def test_egg_requires_an_inspectable_current(self):
        state = self.engine.bind_target(binding("empty"))
        with self.assertRaisesRegex(ValueError, "inspectable Current"):
            self.engine.lay_egg(
                "empty",
                expected_revision=state.revision,
                egg_id="missing-current",
                mark="there is a gap",
                expected="close the gap",
            )

    def test_stale_parent_current_prevents_claim(self):
        state = self.engine.bind_target(binding("stale"), current="CLI revision one")
        state = self.engine.lay_egg(
            "stale",
            expected_revision=state.revision,
            egg_id="json",
            mark="README promises JSON",
            expected="CLI emits JSON",
        )
        state = self.engine.record_pass(
            "stale",
            expected_revision=state.revision,
            current="CLI revision two",
            pass_name="unrelated-pass",
        )
        state, session = self.engine.open_session(
            "stale",
            expected_revision=state.revision,
            host="claude-code",
        )
        with self.assertRaisesRegex(ValueError, "lineage is stale"):
            self.engine.claim_egg(
                "stale",
                expected_revision=state.revision,
                egg_id="json",
                session_id=session.session_id,
            )

    def test_session_metrics_preserve_observation_basis(self):
        state = self.engine.bind_target(binding("stats"), current="working artifact")
        state, session = self.engine.open_session(
            "stats",
            expected_revision=state.revision,
            host="claude-code",
            host_session_key="native-123",
            identity_basis=ObservationBasis.HOST_EVENT,
            host_started_at="2026-08-14T01:00:00+00:00",
            observed_at="2026-08-14T01:00:02+00:00",
        )
        state = self.engine.observe_session(
            "stats",
            expected_revision=state.revision,
            session_id=session.session_id,
            event="turn-completed",
            basis=ObservationBasis.HOST_EVENT,
            amount=2,
            observed_at="2026-08-14T01:01:00+00:00",
        )
        receipt = state.sessions[session.session_id]
        self.assertEqual(receipt["statistics"]["turns"]["value"], 2)
        self.assertEqual(receipt["statistics"]["turns"]["coverage"], "full-session")
        self.assertEqual(receipt["elapsed_seconds"], 60.0)
        self.assertEqual(
            receipt["statistics"]["engine_interactions"]["coverage"], "exact"
        )
        self.assertEqual(receipt["statistics"]["tool_calls"]["coverage"], "unavailable")

    def test_release_allows_cross_session_handoff_and_real_hatch(self):
        state = self.engine.bind_target(binding("handoff"), current="CLI without JSON")
        state = self.engine.lay_egg(
            "handoff",
            expected_revision=state.revision,
            egg_id="json-output",
            mark="README promises --json",
            expected="CLI emits valid JSON",
            required_evidence=("tests", "artifact-resolved"),
            bounds=("three files", "preserve config changes"),
        )
        state, first = self.engine.open_session(
            "handoff", expected_revision=state.revision, host="claude-code"
        )
        state = self.engine.claim_egg(
            "handoff",
            expected_revision=state.revision,
            egg_id="json-output",
            session_id=first.session_id,
        )
        state = self.engine.release_egg(
            "handoff",
            expected_revision=state.revision,
            egg_id="json-output",
            session_id=first.session_id,
            residual="desktop inspection is still needed",
        )
        state, second = self.engine.open_session(
            "handoff", expected_revision=state.revision, host="claude-desktop"
        )
        state = self.engine.claim_egg(
            "handoff",
            expected_revision=state.revision,
            egg_id="json-output",
            session_id=second.session_id,
        )
        state = self.engine.hatch_egg(
            "handoff",
            expected_revision=state.revision,
            egg_id="json-output",
            session_id=second.session_id,
            current="CLI with verified JSON output",
            artifact="owl-artifact://local/src/cli.py",
            evidence={"tests": "pytest:8-passed", "artifact-resolved": "resolved:true"},
            accepted_by="active model against the bound expected outcome",
        )
        self.assertEqual(state.egg["status"], "hatched")
        self.assertEqual(state.current, "CLI with verified JSON output")
        self.assertEqual(state.egg["hatch"]["accepted_by"], "active model against the bound expected outcome")
        self.assertIn("desktop inspection is still needed", state.egg["residuals"])
        self.assertEqual(
            state.sessions[second.session_id]["statistics"]["meaningful_steps"]["value"],
            1,
        )

    def test_closing_a_sitter_releases_the_unhatched_egg(self):
        state = self.engine.bind_target(binding("closed"), current="inspectable Current")
        state = self.engine.lay_egg(
            "closed",
            expected_revision=state.revision,
            egg_id="continuation",
            mark="one bounded gap remains",
            expected="close the gap with evidence",
        )
        state, session = self.engine.open_session(
            "closed", expected_revision=state.revision, host="claude-code"
        )
        state = self.engine.claim_egg(
            "closed",
            expected_revision=state.revision,
            egg_id="continuation",
            session_id=session.session_id,
        )
        state = self.engine.close_session(
            "closed",
            expected_revision=state.revision,
            session_id=session.session_id,
            reason="host-stop",
        )
        self.assertEqual(state.egg["status"], "laid")
        self.assertNotIn("sitter_session_id", state.egg)
        self.assertIn("session closed before hatch: host-stop", state.egg["residuals"])

    def test_mcp_correlates_chatgpt_calls_without_claiming_turn_coverage(self):
        service = OwlMcpService(InMemoryStateStore())
        bound = service.call_tool(
            "owl_bind_target",
            {
                "target_id": "web",
                "name": "Web-carried target",
                "identity": "this-instance",
                "expected": "one verified pass",
                "scope": "authorized app data",
                "current": "inspectable web artifact",
            },
        )["structuredContent"]
        opened = service.call_tool(
            "owl_open_session",
            {
                "target_id": "web",
                "expected_revision": bound["revision"],
                "host": "chatgpt-web",
            },
            request_meta={"openai/session": "anonymous-conversation-key"},
        )["structuredContent"]
        receipt = opened["session"]
        self.assertEqual(receipt["host_session_key"], "anonymous-conversation-key")
        self.assertEqual(receipt["identity_basis"], "host-tool-metadata")
        self.assertEqual(receipt["statistics"]["turns"]["coverage"], "unavailable")
        self.assertEqual(receipt["statistics"]["engine_interactions"]["value"], 1)

    def test_stdio_server_exposes_local_first_mcp_tools(self):
        server = StdioMcpServer(OwlMcpService(InMemoryStateStore()))
        initialized = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "owl-engine")
        listed = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertIn("owl_lay_egg", names)
        self.assertIn("owl_hatch_egg", names)
        self.assertIsNone(
            server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        )

    def test_stdio_entry_point_answers_a_real_json_rpc_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            request = json.dumps(
                {"jsonrpc": "2.0", "id": 7, "method": "tools/list"}
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "owl_mcp_server.py"),
                    "--state-dir",
                    str(Path(temporary) / "state"),
                ],
                input=request + "\n",
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["id"], 7)
            self.assertIn(
                "owl_open_session",
                {tool["name"] for tool in response["result"]["tools"]},
            )

    def test_local_first_demo_creates_and_hatches_real_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "demo_hatchling.py"),
                    temporary,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["egg"]["status"], "hatched")
            self.assertTrue((Path(temporary) / "hatchling.txt").exists())
            self.assertTrue((Path(temporary) / ".owl-state").is_dir())


if __name__ == "__main__":
    unittest.main()
