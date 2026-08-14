from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Protocol


@dataclass
class StateEnvelope:
    target_id: str
    target: dict[str, Any]
    revision: str | None = None
    current: str | None = None
    keep: list[str] = field(default_factory=list)
    marks: list[str] = field(default_factory=list)
    residuals: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    environments: list[dict[str, Any]] = field(default_factory=list)
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    nest: dict[str, Any] = field(default_factory=dict)
    last_pass: str | None = None
    step1: dict[str, Any] | None = None
    commission: dict[str, Any] = field(default_factory=dict)
    egg: dict[str, Any] = field(default_factory=dict)
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value not in (None, [], {})}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateEnvelope":
        return cls(**data)


class StateConflict(RuntimeError):
    def __init__(self, target_id: str, expected: str | None, actual: str | None) -> None:
        self.target_id = target_id
        self.expected = expected
        self.actual = actual
        super().__init__(f"stale write for {target_id}: expected {expected!r}, current {actual!r}")

    @property
    def recovery(self) -> dict[str, str | None]:
        return {
            "action": "reload-current-state-and-reapply-the-mark",
            "target_id": self.target_id,
            "expected_revision": self.expected,
            "current_revision": self.actual,
        }


class StateStore(Protocol):
    def load(self, target_id: str) -> StateEnvelope | None: ...

    def save(self, state: StateEnvelope, expected_revision: str | None = None) -> str: ...


class InMemoryStateStore:
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def load(self, target_id: str) -> StateEnvelope | None:
        with self._lock:
            data = self._states.get(target_id)
            return None if data is None else StateEnvelope.from_dict(json.loads(json.dumps(data)))

    def save(self, state: StateEnvelope, expected_revision: str | None = None) -> str:
        with self._lock:
            existing = self._states.get(state.target_id)
            actual = None if existing is None else str(existing["revision"])
            if actual != expected_revision:
                raise StateConflict(state.target_id, expected_revision, actual)
            revision = "1" if actual is None else str(int(actual) + 1)
            state.revision = revision
            self._states[state.target_id] = json.loads(json.dumps(state.to_dict()))
            return revision


class FileStateStore:
    """Atomic JSON state store for a single authorized local workspace."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _path(self, target_id: str) -> Path:
        safe = "".join(char if char.isalnum() or char in "-_" else "_" for char in target_id)
        if not safe:
            raise ValueError("target_id has no safe filename characters")
        return self.directory / f"{safe}.owl.json"

    def load(self, target_id: str) -> StateEnvelope | None:
        path = self._path(target_id)
        if not path.exists():
            return None
        return StateEnvelope.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, state: StateEnvelope, expected_revision: str | None = None) -> str:
        with self._lock:
            path = self._path(state.target_id)
            existing = self.load(state.target_id)
            actual = None if existing is None else existing.revision
            if actual != expected_revision:
                raise StateConflict(state.target_id, expected_revision, actual)
            revision = "1" if actual is None else str(int(actual) + 1)
            state.revision = revision
            fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(state.to_dict(), handle, indent=2, sort_keys=True)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, path)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)
            return revision
