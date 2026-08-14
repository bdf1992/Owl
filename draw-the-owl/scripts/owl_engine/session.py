from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elapsed_seconds(start: str, end: str) -> float:
    return max(0.0, (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())


class ObservationBasis(str, Enum):
    HOST_EVENT = "host-event"
    HOST_TOOL_METADATA = "host-tool-metadata"
    ENGINE_OBSERVED = "engine-observed"
    MODEL_DECLARED = "model-declared"
    UNAVAILABLE = "unavailable"


@dataclass
class SessionMetric:
    value: int | None = None
    basis: ObservationBasis = ObservationBasis.UNAVAILABLE
    coverage: str = "unavailable"

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "basis": self.basis.value, "coverage": self.coverage}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetric":
        return cls(
            value=data.get("value"),
            basis=ObservationBasis(data.get("basis", "unavailable")),
            coverage=data.get("coverage", "unavailable"),
        )


_EVENT_METRICS = {
    "turn-completed": "turns",
    "tool-completed": "tool_calls",
    "compacted": "compactions",
    "step-completed": "meaningful_steps",
}


def _coverage_for(basis: ObservationBasis) -> str:
    return {
        ObservationBasis.HOST_EVENT: "full-session",
        ObservationBasis.HOST_TOOL_METADATA: "engine-interactions-only",
        ObservationBasis.ENGINE_OBSERVED: "exact-for-engine-events",
        ObservationBasis.MODEL_DECLARED: "declared",
        ObservationBasis.UNAVAILABLE: "unavailable",
    }[basis]


@dataclass
class SessionReceipt:
    session_id: str
    host: str
    identity_basis: ObservationBasis
    engine_first_seen_at: str
    last_seen_at: str
    host_session_key: str | None = None
    host_started_at: str | None = None
    source: str | None = None
    status: str = "active"
    statistics: dict[str, SessionMetric] = field(default_factory=dict)

    @classmethod
    def open(
        cls,
        host: str,
        *,
        host_session_key: str | None = None,
        identity_basis: ObservationBasis = ObservationBasis.ENGINE_OBSERVED,
        host_started_at: str | None = None,
        source: str | None = None,
        observed_at: str | None = None,
    ) -> "SessionReceipt":
        if not host.strip():
            raise ValueError("host cannot be empty")
        if identity_basis is ObservationBasis.UNAVAILABLE and host_session_key is not None:
            raise ValueError("a host session key requires an observation basis")
        now = observed_at or _utc_now()
        metrics = {
            name: SessionMetric()
            for name in ("turns", "tool_calls", "compactions", "meaningful_steps")
        }
        metrics["engine_interactions"] = SessionMetric(
            value=1,
            basis=ObservationBasis.ENGINE_OBSERVED,
            coverage="exact",
        )
        return cls(
            session_id=f"owl-session-{uuid4().hex[:16]}",
            host=host,
            host_session_key=host_session_key,
            identity_basis=identity_basis,
            host_started_at=host_started_at,
            engine_first_seen_at=now,
            last_seen_at=now,
            source=source,
            statistics=metrics,
        )

    def touch(self, observed_at: str | None = None) -> None:
        self.last_seen_at = observed_at or _utc_now()
        metric = self.statistics["engine_interactions"]
        metric.value = (metric.value or 0) + 1

    def observe(
        self,
        event: str,
        *,
        basis: ObservationBasis,
        amount: int = 1,
        observed_at: str | None = None,
    ) -> None:
        if event not in _EVENT_METRICS:
            raise ValueError(f"unsupported session event: {event}")
        if amount < 1:
            raise ValueError("amount must be positive")
        metric = self.statistics[_EVENT_METRICS[event]]
        if metric.basis not in {ObservationBasis.UNAVAILABLE, basis}:
            raise ValueError(
                f"cannot mix {metric.basis.value} and {basis.value} observations for {event}"
            )
        metric.value = (metric.value or 0) + amount
        metric.basis = basis
        metric.coverage = _coverage_for(basis)
        self.last_seen_at = observed_at or _utc_now()

    def close(self, *, reason: str = "session-ended", observed_at: str | None = None) -> None:
        self.status = "closed"
        self.last_seen_at = observed_at or _utc_now()
        self.source = reason

    def to_dict(self) -> dict[str, Any]:
        start = self.host_started_at or self.engine_first_seen_at
        data: dict[str, Any] = {
            "session_id": self.session_id,
            "host": self.host,
            "identity_basis": self.identity_basis.value,
            "engine_first_seen_at": self.engine_first_seen_at,
            "last_seen_at": self.last_seen_at,
            "elapsed_seconds": _elapsed_seconds(start, self.last_seen_at),
            "duration_basis": (
                "host-event" if self.host_started_at is not None else "engine-observed"
            ),
            "status": self.status,
            "statistics": {name: metric.to_dict() for name, metric in self.statistics.items()},
        }
        if self.host_session_key is not None:
            data["host_session_key"] = self.host_session_key
        if self.host_started_at is not None:
            data["host_started_at"] = self.host_started_at
        if self.source is not None:
            data["source"] = self.source
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionReceipt":
        statistics = {
            name: SessionMetric()
            for name in ("turns", "tool_calls", "compactions", "meaningful_steps")
        }
        statistics["engine_interactions"] = SessionMetric(
            value=0,
            basis=ObservationBasis.ENGINE_OBSERVED,
            coverage="exact",
        )
        statistics.update(
            {
                name: SessionMetric.from_dict(metric)
                for name, metric in data.get("statistics", {}).items()
            }
        )
        return cls(
            session_id=data["session_id"],
            host=data["host"],
            host_session_key=data.get("host_session_key"),
            identity_basis=ObservationBasis(data["identity_basis"]),
            host_started_at=data.get("host_started_at"),
            engine_first_seen_at=data["engine_first_seen_at"],
            last_seen_at=data["last_seen_at"],
            source=data.get("source"),
            status=data.get("status", "active"),
            statistics=statistics,
        )
