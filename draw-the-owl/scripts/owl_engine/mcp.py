from __future__ import annotations

import json
from typing import Any

from .core import OwlEngine
from .models import TargetBinding
from .session import ObservationBasis
from .state import StateStore


def _object_schema(properties: dict[str, Any], required: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


_STRING = {"type": "string", "minLength": 1}
_STRINGS = {"type": "array", "items": _STRING}


class OwlMcpService:
    """Transport-neutral MCP tool surface over one OWL_ENGINE state store."""

    def __init__(self, store: StateStore) -> None:
        self.engine = OwlEngine(store)

    @property
    def tools(self) -> list[dict[str, Any]]:
        write = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
        return [
            {
                "name": "owl_bind_target",
                "title": "Bind the current target",
                "description": "Create one target-local OWL_ENGINE state envelope before laying an egg.",
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "name": _STRING,
                        "identity": {"type": "string", "enum": ["any-instance", "this-instance"]},
                        "expected": _STRING,
                        "scope": _STRING,
                        "current": {"type": "string"},
                    },
                    ("target_id", "name", "identity", "expected", "scope"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_get_state",
                "title": "Inspect owl and egg state",
                "description": "Read the target, Current, egg, custody, session receipts, and evidence.",
                "inputSchema": _object_schema({"target_id": _STRING}, ("target_id",)),
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "openWorldHint": False,
                },
            },
            {
                "name": "owl_open_session",
                "title": "Register a sitter session",
                "description": (
                    "Register the current model host. Host metadata is used when available; otherwise "
                    "the engine issues a correlation key without claiming full-session visibility."
                ),
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "host": _STRING,
                        "host_session_key": {"type": "string"},
                        "identity_basis": {
                            "type": "string",
                            "enum": [basis.value for basis in ObservationBasis],
                        },
                        "host_started_at": {"type": "string"},
                        "source": {"type": "string"},
                    },
                    ("target_id", "expected_revision", "host"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_observe_session",
                "title": "Record session telemetry",
                "description": (
                    "Record a host event or declared observation with its basis; never upgrades partial "
                    "telemetry into full-session statistics."
                ),
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "session_id": _STRING,
                        "event": {
                            "type": "string",
                            "enum": ["turn-completed", "tool-completed", "compacted", "step-completed"],
                        },
                        "basis": {
                            "type": "string",
                            "enum": [basis.value for basis in ObservationBasis if basis is not ObservationBasis.UNAVAILABLE],
                        },
                        "amount": {"type": "integer", "minimum": 1},
                        "observed_at": {"type": "string"},
                    },
                    ("target_id", "expected_revision", "session_id", "event", "basis"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_lay_egg",
                "title": "Lay a bounded continuation egg",
                "description": (
                    "Derive one egg from the inspectable Current and a real Mark. Do not use as a generic task queue."
                ),
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "egg_id": _STRING,
                        "mark": _STRING,
                        "expected": _STRING,
                        "required_evidence": _STRINGS,
                        "bounds": _STRINGS,
                    },
                    ("target_id", "expected_revision", "egg_id", "mark", "expected"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_claim_egg",
                "title": "Claim egg custody",
                "description": "Let one active session incubate an egg whose parent Current is still intact.",
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "egg_id": _STRING,
                        "session_id": _STRING,
                    },
                    ("target_id", "expected_revision", "egg_id", "session_id"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_release_egg",
                "title": "Release egg custody",
                "description": "Hand an unfinished egg back without pretending that it hatched.",
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "egg_id": _STRING,
                        "session_id": _STRING,
                        "residual": {"type": "string"},
                        "blocked": {"type": "boolean"},
                    },
                    ("target_id", "expected_revision", "egg_id", "session_id"),
                ),
                "annotations": write,
            },
            {
                "name": "owl_hatch_egg",
                "title": "Commit a completed hatch",
                "description": (
                    "Commit a completed Pass only when custody, artifact, named evidence, and semantic "
                    "acceptance are present."
                ),
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "egg_id": _STRING,
                        "session_id": _STRING,
                        "current": _STRING,
                        "artifact": _STRING,
                        "evidence": {
                            "type": "object",
                            "additionalProperties": {"type": "string", "minLength": 1},
                        },
                        "accepted_by": _STRING,
                        "residuals": _STRINGS,
                    },
                    (
                        "target_id",
                        "expected_revision",
                        "egg_id",
                        "session_id",
                        "current",
                        "artifact",
                        "evidence",
                        "accepted_by",
                    ),
                ),
                "annotations": write,
            },
            {
                "name": "owl_close_session",
                "title": "Close a sitter session",
                "description": "Close one engine session while preserving its receipt and the target-local egg.",
                "inputSchema": _object_schema(
                    {
                        "target_id": _STRING,
                        "expected_revision": _STRING,
                        "session_id": _STRING,
                        "reason": {"type": "string"},
                        "observed_at": {"type": "string"},
                    },
                    ("target_id", "expected_revision", "session_id"),
                ),
                "annotations": write,
            },
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        request_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = request_meta or {}
        if name == "owl_bind_target":
            state = self.engine.bind_target(
                TargetBinding(
                    target_id=arguments["target_id"],
                    name=arguments["name"],
                    identity=arguments["identity"],
                    expected=arguments["expected"],
                    scope=arguments["scope"],
                ),
                current=arguments.get("current"),
            )
            return self._result(state.to_dict())
        if name == "owl_get_state":
            state = self.engine.load(arguments["target_id"])
            if state is None:
                raise KeyError(arguments["target_id"])
            return self._result(state.to_dict())
        if name == "owl_open_session":
            host_key = arguments.get("host_session_key")
            basis_value = arguments.get("identity_basis")
            if host_key is None and meta.get("openai/session"):
                host_key = str(meta["openai/session"])
                basis_value = ObservationBasis.HOST_TOOL_METADATA.value
            basis = ObservationBasis(basis_value or ObservationBasis.ENGINE_OBSERVED.value)
            state, receipt = self.engine.open_session(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                host=arguments["host"],
                host_session_key=host_key,
                identity_basis=basis,
                host_started_at=arguments.get("host_started_at"),
                source=arguments.get("source"),
            )
            return self._result(
                {"session": receipt.to_dict(), "state": state.to_dict()}
            )
        if name == "owl_observe_session":
            state = self.engine.observe_session(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                session_id=arguments["session_id"],
                event=arguments["event"],
                basis=ObservationBasis(arguments["basis"]),
                amount=int(arguments.get("amount", 1)),
                observed_at=arguments.get("observed_at"),
            )
            return self._result(state.to_dict())
        if name == "owl_lay_egg":
            state = self.engine.lay_egg(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                egg_id=arguments["egg_id"],
                mark=arguments["mark"],
                expected=arguments["expected"],
                required_evidence=tuple(arguments.get("required_evidence", ())),
                bounds=tuple(arguments.get("bounds", ())),
            )
            return self._result(state.to_dict())
        if name == "owl_claim_egg":
            state = self.engine.claim_egg(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                egg_id=arguments["egg_id"],
                session_id=arguments["session_id"],
            )
            return self._result(state.to_dict())
        if name == "owl_release_egg":
            state = self.engine.release_egg(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                egg_id=arguments["egg_id"],
                session_id=arguments["session_id"],
                residual=arguments.get("residual"),
                blocked=bool(arguments.get("blocked", False)),
            )
            return self._result(state.to_dict())
        if name == "owl_hatch_egg":
            state = self.engine.hatch_egg(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                egg_id=arguments["egg_id"],
                session_id=arguments["session_id"],
                current=arguments["current"],
                artifact=arguments["artifact"],
                evidence=dict(arguments["evidence"]),
                accepted_by=arguments["accepted_by"],
                residuals=tuple(arguments.get("residuals", ())),
            )
            return self._result(state.to_dict())
        if name == "owl_close_session":
            state = self.engine.close_session(
                arguments["target_id"],
                expected_revision=arguments["expected_revision"],
                session_id=arguments["session_id"],
                reason=arguments.get("reason", "session-ended"),
                observed_at=arguments.get("observed_at"),
            )
            return self._result(state.to_dict())
        raise KeyError(name)

    @staticmethod
    def _result(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "structuredContent": data,
            "content": [{"type": "text", "text": json.dumps(data, sort_keys=True)}],
        }


class StdioMcpServer:
    """Small JSON-RPC stdio transport for local-first MCP hosts."""

    def __init__(self, service: OwlMcpService) -> None:
        self.service = service

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")
        if method == "notifications/initialized":
            return None
        try:
            if method == "initialize":
                requested = request.get("params", {}).get("protocolVersion")
                result = {
                    "protocolVersion": requested or "2025-06-18",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "owl-engine", "version": "0.2.0"},
                    "instructions": (
                        "Bind or inspect the Current before laying an egg. Claim one egg before work; "
                        "hatch only with artifact, evidence, and semantic acceptance."
                    ),
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": self.service.tools}
            elif method == "tools/call":
                params = request.get("params", {})
                result = self.service.call_tool(
                    params["name"],
                    dict(params.get("arguments", {})),
                    request_meta=dict(params.get("_meta", {})),
                )
            else:
                raise KeyError(method)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as error:  # MCP must return structured tool/transport errors.
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602 if isinstance(error, (KeyError, ValueError)) else -32603,
                    "message": str(error),
                    "data": {"type": type(error).__name__},
                },
            }
