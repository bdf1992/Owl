from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EggStatus(str, Enum):
    LAID = "laid"
    INCUBATING = "incubating"
    BLOCKED = "blocked"
    HATCHED = "hatched"


@dataclass
class Egg:
    egg_id: str
    parent_target_id: str
    parent_revision: str
    parent_current: str
    parent_pass: str | None
    mark: str
    expected: str
    required_evidence: tuple[str, ...] = ()
    bounds: tuple[str, ...] = ()
    status: EggStatus = EggStatus.LAID
    sitter_session_id: str | None = None
    residuals: list[str] = field(default_factory=list)
    hatch: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in {
            "egg_id": self.egg_id,
            "parent_target_id": self.parent_target_id,
            "parent_revision": self.parent_revision,
            "parent_current": self.parent_current,
            "mark": self.mark,
            "expected": self.expected,
        }.items():
            if not value.strip():
                raise ValueError(f"{label} cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.egg_id,
            "parent_target_id": self.parent_target_id,
            "parent_revision": self.parent_revision,
            "parent_current": self.parent_current,
            "mark": self.mark,
            "expected": self.expected,
            "status": self.status.value,
        }
        if self.parent_pass is not None:
            data["parent_pass"] = self.parent_pass
        if self.required_evidence:
            data["required_evidence"] = list(self.required_evidence)
        if self.bounds:
            data["bounds"] = list(self.bounds)
        if self.sitter_session_id is not None:
            data["sitter_session_id"] = self.sitter_session_id
        if self.residuals:
            data["residuals"] = list(self.residuals)
        if self.hatch:
            data["hatch"] = dict(self.hatch)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Egg":
        return cls(
            egg_id=data["id"],
            parent_target_id=data["parent_target_id"],
            parent_revision=data["parent_revision"],
            parent_current=data["parent_current"],
            parent_pass=data.get("parent_pass"),
            mark=data["mark"],
            expected=data["expected"],
            required_evidence=tuple(data.get("required_evidence", ())),
            bounds=tuple(data.get("bounds", ())),
            status=EggStatus(data.get("status", "laid")),
            sitter_session_id=data.get("sitter_session_id"),
            residuals=list(data.get("residuals", ())),
            hatch=dict(data.get("hatch", {})),
        )
