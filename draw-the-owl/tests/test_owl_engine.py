from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from owl_engine import (  # noqa: E402
    ArtifactRef,
    CapabilityReceipt,
    CapabilityRequirement,
    CapabilityStatus,
    CommissionBrief,
    CommissionDirection,
    EnvironmentRegistry,
    FileStateStore,
    InMemoryStateStore,
    LocalWorkspaceAdapter,
    Nest,
    OwlEngine,
    Readiness,
    SessionZeroCoordinator,
    StateConflict,
    StateEnvelope,
    Step1Outcome,
    TargetBinding,
    VirtualEnvironmentAdapter,
)


def target(target_id: str = "target") -> TargetBinding:
    return TargetBinding(
        target_id=target_id,
        name="bounded result",
        identity="any-instance",
        expected="one complete Step 1",
        scope="test scope",
        step1_evidence=("inspectable outcome",),
    )


class CountingVirtualAdapter(VirtualEnvironmentAdapter):
    def __init__(self, environment_id: str) -> None:
        super().__init__(environment_id)
        self.descriptions = 0
        self.probes = 0

    def describe(self):
        self.descriptions += 1
        return super().describe()

    def probe(self, requirement):
        self.probes += 1
        return super().probe(requirement)


class NeedsUserAdapter(VirtualEnvironmentAdapter):
    def probe(self, requirement):
        return CapabilityReceipt(
            name=requirement.name,
            environment=self.environment_id,
            operations=requirement.operations,
            status=CapabilityStatus.NEEDS_USER,
            authority="user-controlled login",
            locator=f"owl-capability://{self.environment_id}/{requirement.name}",
            evidence="interactive login is incomplete",
        )


class LocalExtension:
    def __init__(self, root: Path) -> None:
        self.adapter = LocalWorkspaceAdapter(root, environment_id="extended-local")
        self.calls = 0

    def extend(self, requirement):
        self.calls += 1
        return self.adapter


class OwlEngineAcceptanceTests(unittest.TestCase):
    def test_session_zero_freezes_commission_outside_target(self):
        commission = CommissionBrief(
            commissioner="commissioner",
            directions=(
                CommissionDirection("style", "Prefer sparse, sturdy presentation."),
                CommissionDirection(
                    "method",
                    "Use the supplied schema.",
                    strength="mandate",
                    scope="pass",
                ),
            ),
        )
        result = SessionZeroCoordinator().run(
            target("commissioned"),
            (),
            lambda registry, surface: Step1Outcome(current="commissioned result"),
            commission=commission,
        )
        self.assertNotIn("commission", result.state.target)
        self.assertEqual(result.state.commission, commission.to_dict())

    def test_commission_can_change_without_changing_target(self):
        store = InMemoryStateStore()
        original_target = {"name": "recognizable artifact", "identity": "this-instance"}
        state = StateEnvelope(target_id="styled", target=original_target)
        store.save(state)
        engine = OwlEngine(store)

        first = engine.set_commission(
            "styled",
            expected_revision=state.revision,
            commission=CommissionBrief(
                "commissioner",
                (CommissionDirection("style", "Prefer restrained editorial design."),),
            ),
        )
        self.assertEqual(first.target, original_target)
        self.assertEqual(first.commission["directions"][0]["strength"], "preference")

        passed = engine.record_pass(
            "styled",
            expected_revision=first.revision,
            current="same artifact in editorial style",
        )
        self.assertEqual(passed.commission, first.commission)

        changed = engine.set_commission(
            "styled",
            expected_revision=passed.revision,
            commission=CommissionBrief(
                "commissioner",
                (
                    CommissionDirection(
                        "technique",
                        "Use semantic HTML.",
                        strength="mandate",
                    ),
                ),
            ),
        )
        self.assertEqual(changed.target, original_target)
        self.assertEqual(changed.commission["directions"][0]["instruction"], "Use semantic HTML.")

    def test_zero_environment_claims_no_persistence(self):
        coordinator = SessionZeroCoordinator()
        result = coordinator.run(
            target("zero"),
            (),
            lambda registry, surface: Step1Outcome(
                current="bounded conversational result",
                evidence=("returned directly",),
            ),
        )
        self.assertEqual(result.readiness, Readiness.READY)
        self.assertEqual(result.state.environments, [])
        self.assertIsNone(result.state.revision)
        self.assertFalse(result.outcome.persisted)

    def test_single_local_environment_is_extended_validated_and_used(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extension = LocalExtension(root)
            coordinator = SessionZeroCoordinator(
                extensions=(extension,),
                store=FileStateStore(root / ".state"),
            )

            def step1(registry, surface):
                written = registry.invoke(
                    "extended-local",
                    {"operation": "write", "path": "result.txt", "data": "complete"},
                )
                executed = registry.invoke(
                    "extended-local",
                    {"operation": "execute", "argv": [sys.executable, "-c", "print('ok')"]},
                )
                self.assertIsNotNone(registry.resolve(written["artifact"]))
                return Step1Outcome(
                    current="local result",
                    artifacts=(written["artifact"],),
                    evidence=(executed["evidence"],),
                )

            result = coordinator.run(
                target("local"),
                (
                    CapabilityRequirement("filesystem", frozenset({"write", "resolve"})),
                    CapabilityRequirement("process", frozenset({"execute", "test"})),
                ),
                step1,
                step1_action="Write and resolve result.txt, then execute the process probe.",
            )
            self.assertEqual(result.readiness, Readiness.READY)
            self.assertEqual((root / "result.txt").read_text(), "complete")
            self.assertTrue(result.outcome.persisted)
            self.assertEqual(
                result.state.step1["action"],
                "Write and resolve result.txt, then execute the process probe.",
            )
            self.assertGreaterEqual(extension.calls, 1)

    def test_virtual_environment_does_not_assume_host_paths(self):
        virtual = VirtualEnvironmentAdapter(
            "vm-1",
            execute=lambda argv: (0, "virtual:" + " ".join(argv)),
        )
        registry = EnvironmentRegistry((virtual,))

        def step1(registry, surface):
            written = registry.invoke(
                "vm-1", {"operation": "write", "path": "inside/result", "data": "vm-data"}
            )
            executed = registry.invoke("vm-1", {"operation": "execute", "argv": ["build"]})
            self.assertEqual(registry.resolve(written["artifact"]), "vm-data")
            return Step1Outcome(
                current="virtual result",
                artifacts=(written["artifact"],),
                evidence=(executed["evidence"],),
            )

        result = SessionZeroCoordinator(registry).run(
            target("virtual"),
            (
                CapabilityRequirement("filesystem", frozenset({"write", "resolve"})),
                CapabilityRequirement("process", frozenset({"execute"})),
            ),
            step1,
        )
        self.assertEqual(result.readiness, Readiness.READY)
        self.assertIn("simulated isolation", result.surface.environments[0].limits[0])
        self.assertEqual(result.state.environments[0]["observed_revision"], "1")
        with self.assertRaises(PermissionError):
            virtual.invoke({"operation": "write", "path": "/host/path", "data": "no"})

    def test_multiple_environments_keep_artifacts_attributed(self):
        with tempfile.TemporaryDirectory() as temporary:
            local = LocalWorkspaceAdapter(temporary, environment_id="host")
            virtual = VirtualEnvironmentAdapter("container")
            registry = EnvironmentRegistry((local, virtual))

            def step1(registry, surface):
                host = registry.invoke("host", {"operation": "write", "path": "host.txt", "data": "h"})
                guest = registry.invoke(
                    "container", {"operation": "write", "path": "guest.txt", "data": "g"}
                )
                self.assertIsInstance(registry.resolve(host["artifact"]), Path)
                self.assertEqual(registry.resolve(guest["artifact"]), "g")
                return Step1Outcome(
                    current="distributed result",
                    artifacts=(host["artifact"], guest["artifact"]),
                    evidence=("host:observed", "container:observed"),
                )

            result = SessionZeroCoordinator(registry).run(
                target("multi"),
                (CapabilityRequirement("filesystem", frozenset({"write", "resolve"})),),
                step1,
            )
            self.assertEqual(result.readiness, Readiness.READY)
            self.assertEqual(
                {artifact.environment for artifact in result.outcome.artifacts}, {"host", "container"}
            )

    def test_nest_sources_material_across_environments_and_begins_step1(self):
        archive = VirtualEnvironmentAdapter("archive")
        studio = VirtualEnvironmentAdapter("studio")
        registry = EnvironmentRegistry((archive, studio))
        source = registry.invoke(
            "archive",
            {"operation": "write", "path": "brief.txt", "data": "make the whole poster"},
        )["artifact"]
        nest = Nest(
            environment="studio",
            canvas="poster.txt",
            materials=(source,),
            references=("restrained editorial poster",),
        )

        def step1(registry, surface):
            brief = registry.resolve(source)
            drawn = registry.invoke(
                "studio",
                {
                    "operation": "write",
                    "path": nest.canvas,
                    "data": f"complete poster from: {brief}",
                },
            )
            return Step1Outcome(
                current="complete poster",
                artifacts=(drawn["artifact"],),
                evidence=("source resolved with environment attribution",),
            )

        result = SessionZeroCoordinator(registry).run(
            target("nested"),
            (CapabilityRequirement("filesystem", frozenset({"write", "resolve"})),),
            step1,
            nest=nest,
        )
        self.assertEqual(result.readiness, Readiness.READY)
        self.assertEqual(result.state.nest["environment"], "studio")
        self.assertEqual(result.state.nest["canvas"], "poster.txt")
        self.assertEqual(result.state.nest["materials"][0]["environment"], "archive")
        self.assertEqual(result.state.nest["references"], ["restrained editorial poster"])
        self.assertEqual(result.outcome.current, "complete poster")
        self.assertEqual(
            registry.resolve(result.outcome.artifacts[0]),
            "complete poster from: make the whole poster",
        )

    def test_nest_refuses_unobserved_environment(self):
        coordinator = SessionZeroCoordinator(
            EnvironmentRegistry((VirtualEnvironmentAdapter("observed"),))
        )
        with self.assertRaisesRegex(ValueError, "unobserved nest environment"):
            coordinator.run(
                target("unobserved-nest"),
                (),
                lambda registry, surface: Step1Outcome(current="should not draw"),
                nest=Nest(environment="imagined", canvas="result.txt"),
            )

    def test_nest_refuses_unresolved_material(self):
        observed = VirtualEnvironmentAdapter("observed")
        coordinator = SessionZeroCoordinator(EnvironmentRegistry((observed,)))
        missing = ArtifactRef("observed", "missing.txt")
        with self.assertRaisesRegex(ValueError, "unresolved nest materials"):
            coordinator.run(
                target("missing-material"),
                (),
                lambda registry, surface: Step1Outcome(current="should not draw"),
                nest=Nest(
                    environment="observed",
                    canvas="result.txt",
                    materials=(missing,),
                ),
            )

    def test_user_support_resumes_without_rediscovery(self):
        adapter = NeedsUserAdapter("signed-service")
        coordinator = SessionZeroCoordinator(EnvironmentRegistry((adapter,)))
        requirement = CapabilityRequirement(
            "filesystem",
            frozenset({"read"}),
            reason="Step 1 must read the supplied source",
            user_action="Complete the service login in the host UI.",
            reduced_step1="Draft only from the visible request.",
        )
        result = coordinator.run(
            target("support"),
            (requirement,),
            lambda registry, surface: Step1Outcome(current="source-backed result"),
        )
        self.assertEqual(result.readiness, Readiness.BLOCKED)
        self.assertEqual(result.support.action, "Complete the service login in the host UI.")
        count = result.discovery_count

        granted = CapabilityReceipt(
            name="filesystem",
            environment="signed-service",
            operations=frozenset({"read"}),
            status=CapabilityStatus.AVAILABLE,
            authority="user completed host login",
            locator="owl-capability://signed-service/filesystem",
            evidence="post-login probe succeeded",
        )
        resumed = coordinator.resume((granted,))
        self.assertEqual(resumed.readiness, Readiness.READY)
        self.assertEqual(resumed.discovery_count, count)

    def test_unavailable_capability_selects_smaller_step1(self):
        virtual = VirtualEnvironmentAdapter("limited")
        result = SessionZeroCoordinator(EnvironmentRegistry((virtual,))).run(
            target("degraded"),
            (
                CapabilityRequirement(
                    "image-renderer",
                    frozenset({"render"}),
                    reason="the preferred Step 1 is a rendered image",
                    reduced_step1="Produce a complete textual wireframe.",
                ),
            ),
            lambda registry, surface: Step1Outcome(current="rendered image"),
            fallback=lambda registry, surface: Step1Outcome(
                current="complete textual wireframe",
                residuals=("image rendering remains unavailable",),
            ),
        )
        self.assertEqual(result.readiness, Readiness.READY)
        self.assertEqual(result.outcome.current, "complete textual wireframe")
        self.assertIn("image-renderer unavailable", result.limitations[0])
        self.assertIn("image-renderer unavailable", result.state.residuals[-1])

    def test_concurrency_conflict_refuses_stale_write(self):
        store = InMemoryStateStore()
        state = StateEnvelope(target_id="shared", target={"name": "shared owl"})
        store.save(state)
        first = store.load("shared")
        stale = store.load("shared")
        engine = OwlEngine(store)
        updated = engine.record_pass(
            "shared", expected_revision=first.revision, current="worker one", pass_name="pass-1"
        )
        self.assertEqual(updated.revision, "2")
        with self.assertRaises(StateConflict) as caught:
            engine.record_pass(
                "shared", expected_revision=stale.revision, current="worker two", pass_name="pass-2"
            )
        self.assertEqual(caught.exception.recovery["current_revision"], "2")
        self.assertEqual(caught.exception.recovery["action"], "reload-current-state-and-reapply-the-mark")

    def test_micro_correction_skips_discovery_state_and_ceremony(self):
        adapter = CountingVirtualAdapter("unused")
        coordinator = SessionZeroCoordinator(EnvironmentRegistry((adapter,)))
        initial_descriptions = adapter.descriptions
        result = coordinator.run(
            target("micro"),
            (),
            lambda registry, surface: Step1Outcome(current="typo fixed"),
            weight="micro",
        )
        self.assertEqual(result.outcome.current, "typo fixed")
        self.assertEqual(result.discovery_count, 0)
        self.assertEqual(adapter.descriptions, initial_descriptions)
        self.assertEqual(adapter.probes, 0)
        self.assertIsNone(result.state.revision)
        self.assertEqual(result.state.nest, {})


if __name__ == "__main__":
    unittest.main()
