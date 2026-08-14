from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import migrate_state  # noqa: E402
from owl_engine.state import FileStateStore, StateEnvelope  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def write_raw(directory: Path, target_id: str, payload: dict) -> Path:
    path = directory / f"{target_id}.owl.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class MigrateStateAcceptanceTests(unittest.TestCase):
    def test_drops_obsolete_field_and_backs_up_the_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = write_raw(
                state_dir,
                "legacy-target",
                {
                    "target_id": "legacy-target",
                    "target": {"name": "legacy owl"},
                    "revision": "3",
                    "vibe_report": "overworked",  # field removed by a later schema
                },
            )

            report = migrate_state.migrate_file(path, dry_run=False)

            self.assertEqual(report.status, "upgraded")
            self.assertEqual(report.dropped, ["vibe_report"])
            backup = path.with_name(path.name + ".bak")
            self.assertTrue(backup.exists())
            self.assertIn("vibe_report", json.loads(backup.read_text(encoding="utf-8")))

            upgraded = StateEnvelope.from_dict(json.loads(path.read_text(encoding="utf-8")))
            self.assertNotIn("vibe_report", upgraded.to_dict())
            self.assertEqual(upgraded.target_id, "legacy-target")

    def test_dry_run_reports_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = write_raw(
                state_dir,
                "preview-target",
                {"target_id": "preview-target", "target": {}, "stale_field": True},
            )
            original_bytes = path.read_bytes()

            report = migrate_state.migrate_file(path, dry_run=True)

            self.assertEqual(report.status, "upgraded")
            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertFalse(path.with_name(path.name + ".bak").exists())

    def test_already_current_file_is_left_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = write_raw(
                state_dir,
                "current-target",
                {"target_id": "current-target", "target": {"name": "current owl"}},
            )
            original_bytes = path.read_bytes()

            report = migrate_state.migrate_file(path, dry_run=False)

            self.assertEqual(report.status, "unchanged")
            self.assertEqual(path.read_bytes(), original_bytes)

    def test_missing_required_field_is_skipped_not_fabricated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = write_raw(state_dir, "broken-target", {"revision": "1"})

            report = migrate_state.migrate_file(path, dry_run=False)

            self.assertEqual(report.status, "skipped")
            self.assertIn("target", report.reason)

    def test_cli_walks_a_directory_and_signals_skips_via_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            write_raw(state_dir, "ok-target", {"target_id": "ok-target", "target": {}, "extra": 1})
            write_raw(state_dir, "broken-target", {"revision": "1"})

            exit_code = migrate_state.main(["migrate", str(state_dir)])

            self.assertEqual(exit_code, 1)
            self.assertTrue((state_dir / "ok-target.owl.json.bak").exists())

    def test_legacy_fixture_upgrades_to_the_checked_in_golden_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = state_dir / "legacy-target.owl.json"
            path.write_text((FIXTURES / "legacy-target.owl.json").read_text(encoding="utf-8"), encoding="utf-8")

            report = migrate_state.migrate_file(path, dry_run=False)

            self.assertEqual(report.status, "upgraded")
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                load_fixture("legacy-target.upgraded.owl.json"),
            )


class SeedTargetAcceptanceTests(unittest.TestCase):
    def test_seed_target_binds_through_the_real_engine(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)

            state = migrate_state.seed_target(
                state_dir,
                target_id="pattern-commons-example",
                name="Pattern Commons Example",
                identity="any-instance",
                expected="A fresh OWL_ENGINE target ready for its first Pass.",
                scope="documentation example only; not a real Draw the Owl session",
            )

            self.assertEqual(state.to_dict(), load_fixture("seeded-example.owl.json"))
            reloaded = FileStateStore(state_dir).load("pattern-commons-example")
            self.assertEqual(reloaded.to_dict(), load_fixture("seeded-example.owl.json"))

    def test_seed_target_refuses_to_clobber_an_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            migrate_state.seed_target(
                state_dir,
                target_id="dup-target",
                name="First binding",
                identity="any-instance",
                expected="one complete Step 1",
                scope="a single local workspace",
            )

            with self.assertRaises(ValueError):
                migrate_state.seed_target(
                    state_dir,
                    target_id="dup-target",
                    name="Second binding",
                    identity="any-instance",
                    expected="one complete Step 1",
                    scope="a single local workspace",
                )

    def test_cli_seed_writes_a_state_file_and_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)

            exit_code = migrate_state.main(
                [
                    "seed",
                    str(state_dir),
                    "cli-seeded",
                    "--name",
                    "CLI Seeded Target",
                    "--identity",
                    "any-instance",
                    "--expected",
                    "one complete Step 1",
                    "--scope",
                    "a single local workspace",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((state_dir / "cli-seeded.owl.json").exists())

    def test_cli_seed_reports_failure_via_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            migrate_state.seed_target(
                state_dir,
                target_id="dup-target",
                name="First binding",
                identity="any-instance",
                expected="one complete Step 1",
                scope="a single local workspace",
            )

            exit_code = migrate_state.main(
                [
                    "seed",
                    str(state_dir),
                    "dup-target",
                    "--name",
                    "Second binding",
                    "--identity",
                    "any-instance",
                    "--expected",
                    "one complete Step 1",
                    "--scope",
                    "a single local workspace",
                ]
            )

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
