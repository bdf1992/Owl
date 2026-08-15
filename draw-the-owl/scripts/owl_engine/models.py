from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityStatus(str, Enum):
    AVAILABLE = "available"
    CONFIGURABLE = "configurable"
    NEEDS_USER = "needs-user"
    UNAVAILABLE = "unavailable"
    FORBIDDEN = "forbidden"


class Readiness(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ArtifactRef:
    environment: str
    key: str

    @property
    def locator(self) -> str:
        return f"owl-artifact://{self.environment}/{self.key}"

    def to_dict(self) -> dict[str, str]:
        return {"environment": self.environment, "locator": self.locator}


@dataclass(frozen=True)
class TargetBinding:
    target_id: str
    name: str
    identity: str
    expected: str
    scope: str
    step1_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.identity not in {"any-instance", "this-instance"}:
            raise ValueError("identity must be any-instance or this-instance")


@dataclass(frozen=True)
class Mark:
    """Feedback, with the one fact prose kept losing: who supplied it.

    A drawer cannot count the commissioner's attention without recording whose
    Mark is whose. `unattributed` is the honest home for feedback stored before
    authorship was tracked — it never resets the attention counter, so an old
    file fails toward asking rather than toward proceeding.
    """

    text: str
    source: str

    SOURCES = ("commissioner", "drawer", "evidence", "unattributed")

    def __post_init__(self) -> None:
        if self.source not in self.SOURCES:
            raise ValueError(f"mark source must be one of {', '.join(self.SOURCES)}")
        if not self.text.strip():
            raise ValueError("mark text cannot be empty")

    @classmethod
    def coerce(cls, value: "Mark | dict[str, str] | str") -> "Mark":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(text=value, source="unattributed")
        return cls(text=value["text"], source=value.get("source", "unattributed"))

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text, "source": self.source}


@dataclass(frozen=True)
class CommissionDirection:
    category: str
    instruction: str
    strength: str = "preference"
    scope: str = "instance"

    def __post_init__(self) -> None:
        categories = {"medium", "method", "technique", "style", "tone", "presentation", "other"}
        if self.category not in categories:
            raise ValueError("unsupported commission category")
        if self.strength not in {"preference", "mandate"}:
            raise ValueError("strength must be preference or mandate")
        if self.scope not in {"pass", "instance", "default"}:
            raise ValueError("scope must be pass, instance, or default")
        if not self.instruction.strip():
            raise ValueError("commission instruction cannot be empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "instruction": self.instruction,
            "strength": self.strength,
            "scope": self.scope,
        }


@dataclass(frozen=True)
class CommissionBrief:
    commissioner: str
    directions: tuple[CommissionDirection, ...] = ()

    def __post_init__(self) -> None:
        if not self.commissioner.strip():
            raise ValueError("commissioner cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "commissioner": self.commissioner,
            "directions": [direction.to_dict() for direction in self.directions],
        }


@dataclass(frozen=True)
class CapabilityRequirement:
    name: str
    operations: frozenset[str]
    reason: str = ""
    user_action: str | None = None
    reduced_step1: str | None = None


@dataclass(frozen=True)
class CapabilityReceipt:
    name: str
    environment: str
    operations: frozenset[str]
    status: CapabilityStatus
    authority: str
    locator: str
    evidence: str

    def satisfies(self, requirement: CapabilityRequirement) -> bool:
        return (
            self.name == requirement.name
            and requirement.operations <= self.operations
            and self.status is CapabilityStatus.AVAILABLE
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "environment": self.environment,
            "operations": sorted(self.operations),
            "status": self.status.value,
            "authority": self.authority,
            "locator": self.locator,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class EnvironmentReceipt:
    id: str
    kind: str
    authority: str
    locator: str
    limits: tuple[str, ...] = ()
    observed_revision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "authority": self.authority,
            "locator": self.locator,
        }
        if self.limits:
            data["limits"] = list(self.limits)
        if self.observed_revision is not None:
            data["observed_revision"] = self.observed_revision
        return data


@dataclass(frozen=True)
class Nest:
    environment: str
    canvas: str
    materials: tuple[ArtifactRef, ...] = ()
    references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.environment.strip():
            raise ValueError("nest environment cannot be empty")
        if not self.canvas.strip():
            raise ValueError("nest canvas cannot be empty")
        if any(not reference.strip() for reference in self.references):
            raise ValueError("nest references cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "environment": self.environment,
            "canvas": self.canvas,
        }
        if self.materials:
            data["materials"] = [material.to_dict() for material in self.materials]
        if self.references:
            data["references"] = list(self.references)
        return data


@dataclass(frozen=True)
class Step1Outcome:
    current: str
    artifacts: tuple[ArtifactRef, ...] = ()
    evidence: tuple[str, ...] = ()
    residuals: tuple[str, ...] = ()
    persisted: bool = False


@dataclass(frozen=True)
class UserSupportRequest:
    missing: str
    reason: str
    action: str
    reduced_step1: str | None


@dataclass
class CapabilitySurface:
    environments: list[EnvironmentReceipt] = field(default_factory=list)
    capabilities: list[CapabilityReceipt] = field(default_factory=list)

    def available_for(self, requirement: CapabilityRequirement) -> CapabilityReceipt | None:
        return next((item for item in self.capabilities if item.satisfies(requirement)), None)

    def receipts_for(self, requirement: CapabilityRequirement) -> list[CapabilityReceipt]:
        return [item for item in self.capabilities if item.name == requirement.name]
