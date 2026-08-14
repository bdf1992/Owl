from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from .models import (
    ArtifactRef,
    CapabilityReceipt,
    CapabilityRequirement,
    CapabilityStatus,
    EnvironmentReceipt,
)


class Adapter(ABC):
    """The provider-neutral environment boundary used by the engine core."""

    @abstractmethod
    def describe(self) -> EnvironmentReceipt: ...

    @abstractmethod
    def probe(self, requirement: CapabilityRequirement) -> CapabilityReceipt: ...

    @abstractmethod
    def invoke(self, request: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def resolve(self, reference: ArtifactRef) -> Any | None: ...


class EnvironmentRegistry:
    def __init__(self, adapters: tuple[Adapter, ...] = ()) -> None:
        self._adapters: dict[str, Adapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: Adapter) -> None:
        description = adapter.describe()
        if description.id in self._adapters:
            raise ValueError(f"environment already registered: {description.id}")
        self._adapters[description.id] = adapter

    def contains(self, environment_id: str) -> bool:
        return environment_id in self._adapters

    def descriptions(self) -> list[EnvironmentReceipt]:
        return [adapter.describe() for adapter in self._adapters.values()]

    def probe(self, requirement: CapabilityRequirement) -> list[CapabilityReceipt]:
        return [adapter.probe(requirement) for adapter in self._adapters.values()]

    def invoke(self, environment_id: str, request: dict[str, Any]) -> dict[str, Any]:
        return self._adapters[environment_id].invoke(request)

    def resolve(self, reference: ArtifactRef) -> Any | None:
        adapter = self._adapters.get(reference.environment)
        return None if adapter is None else adapter.resolve(reference)


class LocalWorkspaceAdapter(Adapter):
    """A real, root-confined local filesystem and process adapter."""

    def __init__(
        self,
        root: str | Path,
        *,
        environment_id: str = "local",
        authority: str = "host-authorized workspace",
        allow_execute: bool = True,
    ) -> None:
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"workspace does not exist: {self.root}")
        self.environment_id = environment_id
        self.authority = authority
        self.allow_execute = allow_execute

    def describe(self) -> EnvironmentReceipt:
        limits = () if self.allow_execute else ("process execution disabled",)
        return EnvironmentReceipt(
            id=self.environment_id,
            kind="local",
            authority=self.authority,
            locator=f"owl-env://{self.environment_id}",
            limits=limits,
        )

    def probe(self, requirement: CapabilityRequirement) -> CapabilityReceipt:
        supported = {
            "filesystem": frozenset({"read", "write", "observe", "resolve"}),
            "process": frozenset({"execute", "test", "observe"}) if self.allow_execute else frozenset(),
        }
        operations = supported.get(requirement.name, frozenset())
        available = requirement.operations <= operations
        evidence = (
            f"validated against workspace {self.root}"
            if available
            else f"{requirement.name} with {sorted(requirement.operations)} is not exposed"
        )
        return CapabilityReceipt(
            name=requirement.name,
            environment=self.environment_id,
            operations=operations,
            status=CapabilityStatus.AVAILABLE if available else CapabilityStatus.UNAVAILABLE,
            authority=self.authority,
            locator=f"owl-capability://{self.environment_id}/{requirement.name}",
            evidence=evidence,
        )

    def _path(self, value: str) -> Path:
        candidate = (self.root / value).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise PermissionError("path escapes authorized workspace")
        return candidate

    def invoke(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = request.get("operation")
        if operation == "read":
            path = self._path(str(request["path"]))
            return {"data": path.read_text(encoding="utf-8"), "evidence": f"read:{path.name}"}
        if operation == "write":
            path = self._path(str(request["path"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(request["data"]), encoding="utf-8")
            reference = ArtifactRef(self.environment_id, path.relative_to(self.root).as_posix())
            return {"artifact": reference, "evidence": f"wrote:{reference.locator}"}
        if operation == "observe":
            path = self._path(str(request.get("path", ".")))
            return {"exists": path.exists(), "kind": "directory" if path.is_dir() else "file"}
        if operation == "execute":
            if not self.allow_execute:
                raise PermissionError("process execution is disabled")
            argv = request.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(part, str) for part in argv):
                raise ValueError("execute requires a non-empty argv string list")
            completed = subprocess.run(
                argv,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=float(request.get("timeout", 30)),
                check=False,
                shell=False,
            )
            return {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "evidence": f"process-exit:{completed.returncode}",
            }
        raise ValueError(f"unsupported local operation: {operation}")

    def resolve(self, reference: ArtifactRef) -> Path | None:
        if reference.environment != self.environment_id:
            return None
        path = self._path(reference.key)
        return path if path.exists() else None


class VirtualEnvironmentAdapter(Adapter):
    """An isolated VM/container test double with its own artifact namespace."""

    def __init__(
        self,
        environment_id: str,
        *,
        execute: Callable[[list[str]], tuple[int, str]] | None = None,
        authority: str = "test-double authority",
    ) -> None:
        self.environment_id = environment_id
        self.authority = authority
        self._files: dict[str, str] = {}
        self._execute = execute or (lambda argv: (0, json.dumps({"argv": argv})))
        self._revision = 0

    def describe(self) -> EnvironmentReceipt:
        return EnvironmentReceipt(
            id=self.environment_id,
            kind="virtual",
            authority=self.authority,
            locator=f"owl-env://{self.environment_id}",
            limits=("simulated isolation; no host path resolution",),
            observed_revision=str(self._revision),
        )

    def probe(self, requirement: CapabilityRequirement) -> CapabilityReceipt:
        supported = {
            "filesystem": frozenset({"read", "write", "observe", "resolve"}),
            "process": frozenset({"execute", "test", "observe"}),
        }
        operations = supported.get(requirement.name, frozenset())
        available = requirement.operations <= operations
        return CapabilityReceipt(
            name=requirement.name,
            environment=self.environment_id,
            operations=operations,
            status=CapabilityStatus.AVAILABLE if available else CapabilityStatus.UNAVAILABLE,
            authority=self.authority,
            locator=f"owl-capability://{self.environment_id}/{requirement.name}",
            evidence="isolated adapter probe succeeded" if available else "capability not modeled",
        )

    def invoke(self, request: dict[str, Any]) -> dict[str, Any]:
        operation = request.get("operation")
        key = str(request.get("path", ""))
        if key.startswith("/") or ".." in key.split("/"):
            raise PermissionError("virtual paths must remain opaque and relative")
        if operation == "write":
            self._files[key] = str(request["data"])
            self._revision += 1
            reference = ArtifactRef(self.environment_id, key)
            return {"artifact": reference, "evidence": f"virtual-write:{reference.locator}"}
        if operation == "read":
            return {"data": self._files[key], "evidence": f"virtual-read:{key}"}
        if operation == "observe":
            return {"exists": key in self._files}
        if operation == "execute":
            argv = request.get("argv")
            if not isinstance(argv, list) or not all(isinstance(part, str) for part in argv):
                raise ValueError("execute requires an argv string list")
            exit_code, stdout = self._execute(argv)
            return {"exit_code": exit_code, "stdout": stdout, "stderr": "", "evidence": f"virtual-exit:{exit_code}"}
        raise ValueError(f"unsupported virtual operation: {operation}")

    def resolve(self, reference: ArtifactRef) -> str | None:
        if reference.environment != self.environment_id:
            return None
        return self._files.get(reference.key)
