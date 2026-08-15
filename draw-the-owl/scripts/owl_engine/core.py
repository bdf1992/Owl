from __future__ import annotations

from dataclasses import replace
from typing import Any

from .egg import Egg, EggStatus
from .models import CommissionBrief, Mark, TargetBinding
from .session import ObservationBasis, SessionReceipt
from .state import StateEnvelope, StateStore


class OwlEngine:
    """Small state facade for passes after Session Zero."""

    def __init__(self, store: StateStore) -> None:
        self.store = store

    def load(self, target_id: str) -> StateEnvelope | None:
        return self.store.load(target_id)

    def bind_target(
        self,
        target: TargetBinding,
        *,
        current: str | None = None,
        commission: CommissionBrief | None = None,
    ) -> StateEnvelope:
        if self.store.load(target.target_id) is not None:
            raise ValueError(f"target already exists: {target.target_id}")
        state = StateEnvelope(
            target_id=target.target_id,
            target={
                "name": target.name,
                "identity": target.identity,
                "expected": target.expected,
                "scope": target.scope,
            },
            current=current,
            commission={} if commission is None else commission.to_dict(),
        )
        self.store.save(state)
        return state

    def set_commission(
        self,
        target_id: str,
        *,
        expected_revision: str,
        commission: CommissionBrief,
    ) -> StateEnvelope:
        state = self.store.load(target_id)
        if state is None:
            raise KeyError(target_id)
        updated = replace(state, commission=commission.to_dict())
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def record_pass(
        self,
        target_id: str,
        *,
        expected_revision: str,
        current: str,
        marks: tuple[Mark | dict[str, str] | str, ...] = (),
        keep: tuple[str, ...] = (),
        residuals: tuple[str, ...] = (),
        evidence: tuple[str, ...] = (),
        pass_name: str = "pass",
    ) -> StateEnvelope:
        state = self.store.load(target_id)
        if state is None:
            raise KeyError(target_id)
        supplied = [Mark.coerce(mark) for mark in marks]
        # engine-observed: making a Pass is what increments this, so the drawer
        # cannot report itself as attended-to without the commissioner acting.
        from_commissioner = [mark for mark in supplied if mark.source == "commissioner"]
        updated = replace(
            state,
            current=current,
            marks=[mark.to_dict() for mark in supplied],
            keep=list(keep),
            residuals=list(state.residuals) + list(residuals),
            evidence=list(evidence),
            last_pass=pass_name,
            passes_since_commissioner_mark=(
                0 if from_commissioner else state.passes_since_commissioner_mark + 1
            ),
            last_commissioner_mark=(
                from_commissioner[-1].text if from_commissioner else state.last_commissioner_mark
            ),
        )
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def attention(self, target_id: str) -> dict[str, Any]:
        """Answer whether this target is waiting on the commissioner.

        A pull, not a push: the engine has no loop and cannot nag. Every Pass
        consults it, so the answer arrives where it matters. The count is
        `engine-observed` — never derived from turns, tokens, or tool volume,
        which the engine can only take on the model's word.
        """
        state = self._require_state(target_id)
        outstanding: dict[str, int] = {}
        for raw in state.marks:
            mark = Mark.coerce(raw)
            outstanding[mark.source] = outstanding.get(mark.source, 0) + 1
        pending = state.passes_since_commissioner_mark
        return {
            "target_id": target_id,
            "awaiting_commissioner_mark": pending > 0,
            "passes_since_commissioner_mark": pending,
            "last_commissioner_mark": state.last_commissioner_mark,
            "outstanding_marks_by_source": outstanding,
            "basis": ObservationBasis.ENGINE_OBSERVED.value,
        }

    def open_session(
        self,
        target_id: str,
        *,
        expected_revision: str,
        host: str,
        host_session_key: str | None = None,
        identity_basis: ObservationBasis = ObservationBasis.ENGINE_OBSERVED,
        host_started_at: str | None = None,
        source: str | None = None,
        observed_at: str | None = None,
    ) -> tuple[StateEnvelope, SessionReceipt]:
        state = self._require_state(target_id)
        receipt = SessionReceipt.open(
            host,
            host_session_key=host_session_key,
            identity_basis=identity_basis,
            host_started_at=host_started_at,
            source=source,
            observed_at=observed_at,
        )
        sessions = dict(state.sessions)
        sessions[receipt.session_id] = receipt.to_dict()
        updated = replace(state, sessions=sessions)
        self.store.save(updated, expected_revision=expected_revision)
        return updated, receipt

    def observe_session(
        self,
        target_id: str,
        *,
        expected_revision: str,
        session_id: str,
        event: str,
        basis: ObservationBasis,
        amount: int = 1,
        observed_at: str | None = None,
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        receipt = self._require_session(state, session_id)
        if receipt.status != "active":
            raise ValueError(f"session is not active: {session_id}")
        receipt.touch(observed_at)
        receipt.observe(event, basis=basis, amount=amount, observed_at=observed_at)
        return self._save_session(state, receipt, expected_revision)

    def close_session(
        self,
        target_id: str,
        *,
        expected_revision: str,
        session_id: str,
        reason: str = "session-ended",
        observed_at: str | None = None,
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        receipt = self._require_session(state, session_id)
        receipt.touch(observed_at)
        receipt.close(reason=reason, observed_at=observed_at)
        egg_data = state.egg
        if state.egg:
            egg = Egg.from_dict(state.egg)
            if egg.status is EggStatus.INCUBATING and egg.sitter_session_id == session_id:
                egg.sitter_session_id = None
                egg.status = EggStatus.LAID
                egg.residuals.append(f"session closed before hatch: {reason}")
                egg_data = egg.to_dict()
        sessions = dict(state.sessions)
        sessions[session_id] = receipt.to_dict()
        updated = replace(state, egg=egg_data, sessions=sessions)
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def lay_egg(
        self,
        target_id: str,
        *,
        expected_revision: str,
        egg_id: str,
        mark: str,
        expected: str,
        required_evidence: tuple[str, ...] = (),
        bounds: tuple[str, ...] = (),
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        if state.current is None or not state.current.strip():
            raise ValueError("an egg requires an inspectable Current")
        if state.egg and state.egg.get("status") != EggStatus.HATCHED.value:
            raise ValueError("an unresolved egg already exists")
        egg = Egg(
            egg_id=egg_id,
            parent_target_id=target_id,
            parent_revision=expected_revision,
            parent_current=state.current,
            parent_pass=state.last_pass,
            mark=mark,
            expected=expected,
            required_evidence=required_evidence,
            bounds=bounds,
        )
        updated = replace(state, egg=egg.to_dict())
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def claim_egg(
        self,
        target_id: str,
        *,
        expected_revision: str,
        egg_id: str,
        session_id: str,
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        receipt = self._require_session(state, session_id)
        if receipt.status != "active":
            raise ValueError(f"session is not active: {session_id}")
        egg = self._require_egg(state, egg_id)
        if egg.status is EggStatus.HATCHED:
            raise ValueError("a hatched egg cannot be claimed")
        if egg.sitter_session_id not in {None, session_id}:
            raise ValueError(f"egg is already claimed by {egg.sitter_session_id}")
        if state.current != egg.parent_current or state.last_pass != egg.parent_pass:
            raise ValueError("egg lineage is stale; Current changed after the egg was laid")
        egg.sitter_session_id = session_id
        egg.status = EggStatus.INCUBATING
        receipt.touch()
        sessions = dict(state.sessions)
        sessions[session_id] = receipt.to_dict()
        updated = replace(state, egg=egg.to_dict(), sessions=sessions)
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def release_egg(
        self,
        target_id: str,
        *,
        expected_revision: str,
        egg_id: str,
        session_id: str,
        residual: str | None = None,
        blocked: bool = False,
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        egg = self._require_egg(state, egg_id)
        if egg.sitter_session_id != session_id:
            raise ValueError("only the current sitter can release the egg")
        egg.sitter_session_id = None
        egg.status = EggStatus.BLOCKED if blocked else EggStatus.LAID
        if residual:
            egg.residuals.append(residual)
        receipt = self._require_session(state, session_id)
        receipt.touch()
        sessions = dict(state.sessions)
        sessions[session_id] = receipt.to_dict()
        updated = replace(state, egg=egg.to_dict(), sessions=sessions)
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def hatch_egg(
        self,
        target_id: str,
        *,
        expected_revision: str,
        egg_id: str,
        session_id: str,
        current: str,
        artifact: str,
        evidence: dict[str, str],
        accepted_by: str,
        residuals: tuple[str, ...] = (),
    ) -> StateEnvelope:
        state = self._require_state(target_id)
        egg = self._require_egg(state, egg_id)
        if egg.status is not EggStatus.INCUBATING or egg.sitter_session_id != session_id:
            raise ValueError("the active sitter must incubate the egg before hatching")
        missing = [name for name in egg.required_evidence if not evidence.get(name)]
        if missing:
            raise ValueError(f"missing hatch evidence: {', '.join(missing)}")
        if not current.strip() or not artifact.strip() or not accepted_by.strip():
            raise ValueError("hatching requires Current, an artifact, and semantic acceptance")
        egg.status = EggStatus.HATCHED
        egg.hatch = {
            "current": current,
            "artifact": artifact,
            "evidence": dict(evidence),
            "accepted_by": accepted_by,
        }
        egg.residuals.extend(residuals)
        receipt = self._require_session(state, session_id)
        receipt.touch()
        receipt.observe("step-completed", basis=ObservationBasis.ENGINE_OBSERVED)
        sessions = dict(state.sessions)
        sessions[session_id] = receipt.to_dict()
        updated = replace(
            state,
            current=current,
            evidence=list(state.evidence) + list(evidence.values()) + [artifact],
            residuals=list(state.residuals) + list(residuals),
            last_pass=f"hatch:{egg_id}",
            egg=egg.to_dict(),
            sessions=sessions,
        )
        self.store.save(updated, expected_revision=expected_revision)
        return updated

    def _require_state(self, target_id: str) -> StateEnvelope:
        state = self.store.load(target_id)
        if state is None:
            raise KeyError(target_id)
        return state

    @staticmethod
    def _require_session(state: StateEnvelope, session_id: str) -> SessionReceipt:
        data = state.sessions.get(session_id)
        if data is None:
            raise KeyError(session_id)
        return SessionReceipt.from_dict(data)

    @staticmethod
    def _require_egg(state: StateEnvelope, egg_id: str) -> Egg:
        if not state.egg or state.egg.get("id") != egg_id:
            raise KeyError(egg_id)
        return Egg.from_dict(state.egg)

    def _save_session(
        self,
        state: StateEnvelope,
        receipt: SessionReceipt,
        expected_revision: str,
    ) -> StateEnvelope:
        sessions = dict(state.sessions)
        sessions[receipt.session_id] = receipt.to_dict()
        updated = replace(state, sessions=sessions)
        self.store.save(updated, expected_revision=expected_revision)
        return updated
