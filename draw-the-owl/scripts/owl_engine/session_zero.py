from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from .adapters import Adapter, EnvironmentRegistry
from .models import (
    CapabilityReceipt,
    CapabilityRequirement,
    CapabilityStatus,
    CapabilitySurface,
    CommissionBrief,
    Nest,
    Readiness,
    Step1Outcome,
    TargetBinding,
    UserSupportRequest,
)
from .state import StateEnvelope, StateStore


class Extension(Protocol):
    """A bounded provider for a demonstrated missing capability."""

    def extend(self, requirement: CapabilityRequirement) -> Adapter | CapabilityReceipt | None: ...


Step1 = Callable[[EnvironmentRegistry, CapabilitySurface], Step1Outcome]


@dataclass
class SessionZeroResult:
    readiness: Readiness
    state: StateEnvelope
    surface: CapabilitySurface
    outcome: Step1Outcome | None = None
    support: UserSupportRequest | None = None
    limitations: list[str] = field(default_factory=list)
    discovery_count: int = 0


class SessionZeroCoordinator:
    """Bounded negotiation: bind, observe, extend, validate, freeze, begin."""

    def __init__(
        self,
        registry: EnvironmentRegistry | None = None,
        *,
        extensions: tuple[Extension, ...] = (),
        store: StateStore | None = None,
    ) -> None:
        self.registry = registry or EnvironmentRegistry()
        self.extensions = extensions
        self.store = store
        self.discovery_count = 0
        self._target: TargetBinding | None = None
        self._commission: CommissionBrief | None = None
        self._nest: Nest | None = None
        self._requirements: tuple[CapabilityRequirement, ...] = ()
        self._surface = CapabilitySurface()
        self._step1: Step1 | None = None
        self._fallback: Step1 | None = None
        self._weight = "standard"
        self._step1_action = ""

    def run(
        self,
        target: TargetBinding,
        requirements: tuple[CapabilityRequirement, ...],
        step1: Step1,
        *,
        commission: CommissionBrief | None = None,
        nest: Nest | None = None,
        fallback: Step1 | None = None,
        weight: str = "standard",
        step1_action: str | None = None,
    ) -> SessionZeroResult:
        self._target = target
        self._commission = commission
        self._nest = nest
        self._requirements = requirements
        self._step1 = step1
        self._fallback = fallback
        self._weight = weight
        self._step1_action = step1_action or target.expected

        # A true micro correction with no new capability need stays out of the engine.
        if weight == "micro" and not requirements and self.store is None:
            self._nest = None
            return self._finish(CapabilitySurface(), step1, limitations=[])

        self.discovery_count += 1
        self._surface.environments = self.registry.descriptions()
        for requirement in requirements:
            self._probe_requirement(requirement)
            if self._surface.available_for(requirement) is None:
                self._extend_requirement(requirement)
        return self._evaluate()

    def resume(self, receipts: tuple[CapabilityReceipt, ...]) -> SessionZeroResult:
        if self._target is None or self._step1 is None:
            raise RuntimeError("no blocked Session Zero to resume")
        self._surface.capabilities.extend(receipts)
        return self._evaluate()

    def _probe_requirement(self, requirement: CapabilityRequirement) -> None:
        self._surface.capabilities.extend(self.registry.probe(requirement))

    def _extend_requirement(self, requirement: CapabilityRequirement) -> None:
        for extension in self.extensions:
            result = extension.extend(requirement)
            if result is None:
                continue
            if isinstance(result, CapabilityReceipt):
                self._surface.capabilities.append(result)
            else:
                description = result.describe()
                if not self.registry.contains(description.id):
                    self.registry.register(result)
                    self._surface.environments.append(description)
                self._surface.capabilities.append(result.probe(requirement))
            if self._surface.available_for(requirement) is not None:
                return

    def _evaluate(self) -> SessionZeroResult:
        assert self._target is not None and self._step1 is not None
        self._validate_nest()
        missing: list[CapabilityRequirement] = []
        needs_user: list[tuple[CapabilityRequirement, CapabilityReceipt]] = []
        for requirement in self._requirements:
            if self._surface.available_for(requirement) is not None:
                continue
            receipts = self._surface.receipts_for(requirement)
            user_receipt = next((r for r in receipts if r.status is CapabilityStatus.NEEDS_USER), None)
            if user_receipt is not None:
                needs_user.append((requirement, user_receipt))
            else:
                missing.append(requirement)

        if needs_user:
            requirement, receipt = needs_user[0]
            state = self._freeze(step1_status="blocked", missing=requirement.name)
            return SessionZeroResult(
                readiness=Readiness.BLOCKED,
                state=state,
                surface=self._surface,
                support=UserSupportRequest(
                    missing=requirement.name,
                    reason=requirement.reason or receipt.evidence,
                    action=requirement.user_action or "Grant access through the host's normal mechanism.",
                    reduced_step1=requirement.reduced_step1,
                ),
                discovery_count=self.discovery_count,
            )

        if missing:
            limitations = [
                f"{item.name} unavailable: {item.reason or 'no validated capability'}" for item in missing
            ]
            if self._fallback is not None:
                return self._finish(self._surface, self._fallback, limitations=limitations)
            state = self._freeze(step1_status="blocked", missing=missing[0].name)
            first = missing[0]
            return SessionZeroResult(
                readiness=Readiness.BLOCKED,
                state=state,
                surface=self._surface,
                support=UserSupportRequest(
                    missing=first.name,
                    reason=first.reason or "No validated capability is available.",
                    action=first.user_action or "Choose the reduced Step 1.",
                    reduced_step1=first.reduced_step1,
                ),
                limitations=limitations,
                discovery_count=self.discovery_count,
            )
        return self._finish(self._surface, self._step1, limitations=[])

    def _validate_nest(self) -> None:
        if self._nest is None:
            return
        environments = {item.id for item in self._surface.environments}
        if self._nest.environment not in environments:
            raise ValueError(f"unobserved nest environment: {self._nest.environment}")
        unobserved_materials = sorted(
            {
                material.environment
                for material in self._nest.materials
                if material.environment not in environments
            }
        )
        if unobserved_materials:
            raise ValueError(
                "unobserved nest material environments: " + ", ".join(unobserved_materials)
            )
        unresolved_materials = [
            material.locator
            for material in self._nest.materials
            if self.registry.resolve(material) is None
        ]
        if unresolved_materials:
            raise ValueError("unresolved nest materials: " + ", ".join(unresolved_materials))

    def _freeze(self, *, step1_status: str, missing: str | None = None) -> StateEnvelope:
        assert self._target is not None
        existing = self.store.load(self._target.target_id) if self.store is not None else None
        state = existing or StateEnvelope(
            target_id=self._target.target_id,
            target={
                "name": self._target.name,
                "identity": self._target.identity,
                "expected": self._target.expected,
                "scope": self._target.scope,
            },
        )
        if self._commission is not None:
            state.commission = self._commission.to_dict()
        if self._nest is not None:
            state.nest = self._nest.to_dict()
        state.environments = [item.to_dict() for item in self._surface.environments]
        state.capabilities = [item.to_dict() for item in self._surface.capabilities]
        state.step1 = {
            "status": step1_status,
            "action": self._step1_action,
            "expected_evidence": list(self._target.step1_evidence),
        }
        if missing:
            state.step1["missing"] = missing
        if self.store is not None:
            expected = existing.revision if existing is not None else None
            self.store.save(state, expected_revision=expected)
        return state

    def _finish(
        self,
        surface: CapabilitySurface,
        step: Step1,
        *,
        limitations: list[str],
    ) -> SessionZeroResult:
        state = self._freeze(step1_status="ready")
        outcome = step(self.registry, surface)
        if not (self._weight == "micro" and not self._requirements and self.store is None):
            self._surface.environments = self.registry.descriptions()
            state.environments = [item.to_dict() for item in self._surface.environments]
        state.current = outcome.current
        state.residuals = list(outcome.residuals) + limitations
        state.evidence = list(outcome.evidence) + [item.locator for item in outcome.artifacts]
        state.last_pass = "step-1"
        state.step1 = {
            "status": "completed",
            "action": self._step1_action,
            "result": outcome.current,
        }
        if self.store is not None:
            self.store.save(state, expected_revision=state.revision)
            outcome = Step1Outcome(
                current=outcome.current,
                artifacts=outcome.artifacts,
                evidence=outcome.evidence,
                residuals=outcome.residuals,
                persisted=True,
            )
        return SessionZeroResult(
            readiness=Readiness.READY,
            state=state,
            surface=surface,
            outcome=outcome,
            limitations=limitations,
            discovery_count=self.discovery_count,
        )
