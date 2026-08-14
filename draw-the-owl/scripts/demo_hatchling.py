#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from owl_engine import FileStateStore, LocalWorkspaceAdapter, OwlMcpService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local-first MCP-shaped egg from Current through a verified hatch."
    )
    parser.add_argument("workspace", type=Path, help="authorized demo workspace")
    parser.add_argument("--host", default="local-mcp", help="host label for the sitter receipt")
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)

    service = OwlMcpService(FileStateStore(args.workspace / ".owl-state"))
    compute = LocalWorkspaceAdapter(args.workspace, environment_id="hatchling-local")

    bound = service.call_tool(
        "owl_bind_target",
        {
            "target_id": "local-first-hatchling-demo",
            "name": "Local-first Hatchling proof",
            "identity": "this-instance",
            "expected": "one complete artifact produced through the portable MCP surface",
            "scope": "the supplied workspace only",
            "current": "authorized workspace before the Hatchling pass",
        },
    )["structuredContent"]
    laid = service.call_tool(
        "owl_lay_egg",
        {
            "target_id": bound["target_id"],
            "expected_revision": bound["revision"],
            "egg_id": "first-useful-artifact",
            "mark": "the session has not yet produced an inspectable result",
            "expected": "create and resolve hatchling.txt, then execute its proof",
            "required_evidence": ["process", "artifact-resolved"],
            "bounds": ["supplied workspace", "one text artifact"],
        },
    )["structuredContent"]
    opened = service.call_tool(
        "owl_open_session",
        {
            "target_id": bound["target_id"],
            "expected_revision": laid["revision"],
            "host": args.host,
            "source": "local-first-demo",
        },
    )["structuredContent"]
    session_id = opened["session"]["session_id"]
    claimed = service.call_tool(
        "owl_claim_egg",
        {
            "target_id": bound["target_id"],
            "expected_revision": opened["state"]["revision"],
            "egg_id": "first-useful-artifact",
            "session_id": session_id,
        },
    )["structuredContent"]

    written = compute.invoke(
        {
            "operation": "write",
            "path": "hatchling.txt",
            "data": "A model session sat on an egg and left inspectable evidence.\n",
        }
    )
    process = compute.invoke(
        {
            "operation": "execute",
            "argv": [
                sys.executable,
                "-c",
                "from pathlib import Path; assert 'inspectable evidence' in Path('hatchling.txt').read_text()",
            ],
        }
    )
    resolved = compute.resolve(written["artifact"])
    hatched = service.call_tool(
        "owl_hatch_egg",
        {
            "target_id": bound["target_id"],
            "expected_revision": claimed["revision"],
            "egg_id": "first-useful-artifact",
            "session_id": session_id,
            "current": "verified hatchling.txt exists in the authorized workspace",
            "artifact": written["artifact"].locator,
            "evidence": {
                "process": process["evidence"],
                "artifact-resolved": f"resolved:{resolved is not None}",
            },
            "accepted_by": "demo acceptance contract",
        },
    )["structuredContent"]

    print(
        json.dumps(
            {
                "target_id": hatched["target_id"],
                "revision": hatched["revision"],
                "current": hatched["current"],
                "egg": hatched["egg"],
                "session": hatched["sessions"][session_id],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
