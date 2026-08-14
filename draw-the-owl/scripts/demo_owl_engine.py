#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from owl_engine import (  # noqa: E402
    CapabilityRequirement,
    CommissionBrief,
    CommissionDirection,
    FileStateStore,
    LocalWorkspaceAdapter,
    SessionZeroCoordinator,
    Step1Outcome,
    TargetBinding,
)


class AuthorizedWorkspaceExtension:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.adapter: LocalWorkspaceAdapter | None = None

    def extend(self, requirement: CapabilityRequirement):
        if requirement.name not in {"filesystem", "process"}:
            return None
        if self.adapter is None:
            self.adapter = LocalWorkspaceAdapter(self.workspace, environment_id="demo-local")
        return self.adapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Session Zero into a real completed Step 1.")
    parser.add_argument("workspace", type=Path, help="authorized demo workspace")
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=True)
    state_store = FileStateStore(args.workspace / ".owl-state")
    extension = AuthorizedWorkspaceExtension(args.workspace)

    target = TargetBinding(
        target_id="portable-tool-surface-demo",
        name="Session Zero proof",
        identity="any-instance",
        expected="a real Step 1 artifact created after capability validation",
        scope="the supplied workspace only",
        step1_evidence=("resolvable artifact", "successful process probe"),
    )
    requirements = (
        CapabilityRequirement("filesystem", frozenset({"write", "resolve"})),
        CapabilityRequirement("process", frozenset({"execute", "test"})),
    )
    commission = CommissionBrief(
        commissioner="demo user",
        directions=(
            CommissionDirection(
                category="technique",
                instruction="Prefer the smallest locally executable proof.",
            ),
            CommissionDirection(
                category="presentation",
                instruction="Report evidence as structured JSON.",
                strength="mandate",
            ),
        ),
    )

    def step1(registry, surface):
        process = registry.invoke(
            "demo-local",
            {"operation": "execute", "argv": [sys.executable, "-c", "print('probe-ok')"]},
        )
        written = registry.invoke(
            "demo-local",
            {
                "operation": "write",
                "path": "step-1.txt",
                "data": "The first complete slice exists.\n",
            },
        )
        artifact = written["artifact"]
        resolved = registry.resolve(artifact)
        return Step1Outcome(
            current="Step 1 artifact completed",
            artifacts=(artifact,),
            evidence=(process["evidence"], written["evidence"], f"resolved:{resolved is not None}"),
        )

    result = SessionZeroCoordinator(extensions=(extension,), store=state_store).run(
        target,
        requirements,
        step1,
        commission=commission,
        step1_action="Probe Python, write step-1.txt, and resolve its opaque artifact reference.",
    )
    print(
        json.dumps(
            {
                "readiness": result.readiness.value,
                "target": result.state.target,
                "commission": result.state.commission,
                "capabilities": result.state.capabilities,
                "step1": result.state.step1,
                "evidence": result.state.evidence,
                "revision": result.state.revision,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
