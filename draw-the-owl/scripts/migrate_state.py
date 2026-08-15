#!/usr/bin/env python3
"""Bootstrap and upgrade *.owl.json state files for a local OWL_ENGINE workspace.

`migrate` handles schema drift: StateEnvelope.from_dict does cls(**data), so a
file written by an older skill version that still carries a field this version
renamed or removed raises a bare TypeError instead of loading. This walks a
state directory, drops fields the current schema no longer knows, backs up
anything it touches, and leaves already-current files alone.

`seed` handles the other end: binding the first target in a workspace that has
no state file yet, through the same OwlEngine.bind_target path the engine
itself uses, so a freshly seeded file is never a hand-built approximation of
one.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from owl_engine.core import OwlEngine  # noqa: E402
from owl_engine.models import TargetBinding  # noqa: E402
from owl_engine.state import FileStateStore, StateEnvelope  # noqa: E402

KNOWN_FIELDS = {f.name for f in dataclasses.fields(StateEnvelope)}
REQUIRED_FIELDS = {
    f.name
    for f in dataclasses.fields(StateEnvelope)
    if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING  # type: ignore[misc]
}


@dataclasses.dataclass
class MigrationReport:
    path: Path
    status: str  # "upgraded", "unchanged", "skipped"
    dropped: list[str] = dataclasses.field(default_factory=list)
    reason: str | None = None


def migrate_payload(raw: dict, *, target_id_hint: str) -> tuple[dict, list[str]]:
    dropped = sorted(key for key in raw if key not in KNOWN_FIELDS)
    cleaned = {key: value for key, value in raw.items() if key in KNOWN_FIELDS}
    cleaned.setdefault("target_id", target_id_hint)
    missing = sorted(REQUIRED_FIELDS - cleaned.keys())
    if missing:
        raise ValueError(f"missing required field(s) {missing}; needs a manual fix, not a migration")
    return cleaned, dropped


def migrate_file(path: Path, *, dry_run: bool) -> MigrationReport:
    raw = json.loads(path.read_text(encoding="utf-8"))
    target_id_hint = path.name[: -len(".owl.json")] if path.name.endswith(".owl.json") else path.stem

    try:
        cleaned, dropped = migrate_payload(raw, target_id_hint=target_id_hint)
    except ValueError as error:
        return MigrationReport(path=path, status="skipped", reason=str(error))

    if not dropped:
        return MigrationReport(path=path, status="unchanged")

    # Round-trip through the dataclass so a shape that still doesn't fit fails loudly here.
    upgraded = StateEnvelope.from_dict(cleaned).to_dict()

    if not dry_run:
        backup = path.with_name(path.name + ".bak")
        if not backup.exists():
            backup.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        path.write_text(json.dumps(upgraded, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return MigrationReport(path=path, status="upgraded", dropped=dropped)


def seed_target(
    state_dir: Path,
    *,
    target_id: str,
    name: str,
    identity: str,
    expected: str,
    scope: str,
    current: str | None = None,
) -> StateEnvelope:
    engine = OwlEngine(FileStateStore(state_dir))
    return engine.bind_target(
        TargetBinding(target_id=target_id, name=name, identity=identity, expected=expected, scope=scope),
        current=current,
    )


def _run_migrate(state_dir: Path, *, dry_run: bool) -> int:
    if not state_dir.is_dir():
        print(f"no such directory: {state_dir}", file=sys.stderr)
        return 2

    files = sorted(state_dir.glob("*.owl.json"))
    if not files:
        print(f"no *.owl.json files found in {state_dir}")
        return 0

    exit_code = 0
    for path in files:
        report = migrate_file(path, dry_run=dry_run)
        if report.status == "skipped":
            exit_code = 1
            print(f"SKIP           {path.name}: {report.reason}")
        elif report.status == "unchanged":
            print(f"OK             {path.name}: already current")
        else:
            verb = "WOULD UPGRADE" if dry_run else "UPGRADED"
            note = f" (dropped {', '.join(report.dropped)})" if report.dropped else ""
            print(f"{verb:<14} {path.name}{note}")

    return exit_code


def _run_seed(args: argparse.Namespace) -> int:
    try:
        state = seed_target(
            args.state_dir,
            target_id=args.target_id,
            name=args.name,
            identity=args.identity,
            expected=args.expected,
            scope=args.scope,
            current=args.current,
        )
    except ValueError as error:
        print(f"SKIP           {args.target_id}: {error}", file=sys.stderr)
        return 1

    print(f"SEEDED         {args.target_id}.owl.json (revision {state.revision})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    migrate_parser = subparsers.add_parser("migrate", help="upgrade existing *.owl.json files to the current schema")
    migrate_parser.add_argument("state_dir", type=Path, help="directory containing *.owl.json files")
    migrate_parser.add_argument("--dry-run", action="store_true", help="report changes without writing them")

    seed_parser = subparsers.add_parser("seed", help="bind a fresh target and write its first state file")
    seed_parser.add_argument("state_dir", type=Path, help="directory to hold the new *.owl.json file")
    seed_parser.add_argument("target_id", help="filename-safe id for the target")
    seed_parser.add_argument("--name", required=True, help="the result the request is trying to obtain")
    seed_parser.add_argument("--identity", required=True, choices=["any-instance", "this-instance"])
    seed_parser.add_argument("--expected", required=True, help="what a complete Pass looks like")
    seed_parser.add_argument("--scope", required=True, help="the authorized boundary of this target")
    seed_parser.add_argument("--current", help="an existing Current to adopt instead of starting blank")

    args = parser.parse_args(argv)

    if args.command == "migrate":
        return _run_migrate(args.state_dir, dry_run=args.dry_run)
    return _run_seed(args)


if __name__ == "__main__":
    raise SystemExit(main())
