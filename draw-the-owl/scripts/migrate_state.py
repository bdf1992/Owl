#!/usr/bin/env python3
"""Upgrade *.owl.json state files to the schema StateEnvelope currently expects.

StateEnvelope.from_dict does cls(**data): a file written by an older skill
version that still carries a field this version renamed or removed raises a
bare TypeError instead of loading. This walks a state directory, drops fields
the current schema no longer knows, backs up anything it touches, and leaves
already-current files alone.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from owl_engine.state import StateEnvelope  # noqa: E402

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_dir", type=Path, help="directory containing *.owl.json files")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing them")
    args = parser.parse_args(argv)

    if not args.state_dir.is_dir():
        print(f"no such directory: {args.state_dir}", file=sys.stderr)
        return 2

    files = sorted(args.state_dir.glob("*.owl.json"))
    if not files:
        print(f"no *.owl.json files found in {args.state_dir}")
        return 0

    exit_code = 0
    for path in files:
        report = migrate_file(path, dry_run=args.dry_run)
        if report.status == "skipped":
            exit_code = 1
            print(f"SKIP           {path.name}: {report.reason}")
        elif report.status == "unchanged":
            print(f"OK             {path.name}: already current")
        else:
            verb = "WOULD UPGRADE" if args.dry_run else "UPGRADED"
            note = f" (dropped {', '.join(report.dropped)})" if report.dropped else ""
            print(f"{verb:<14} {path.name}{note}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
