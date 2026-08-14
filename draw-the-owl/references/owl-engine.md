# OWL_ENGINE portable tool-surface broker

Use this layer when the current Target needs capability negotiation, durable continuity, cross-environment artifact resolution, or deterministic revision control. It serves Draw the Owl; it is not the Target and not a universal agent platform.

## Contents

- Session Zero boundary
- Provider-neutral contracts
- Nest
- Portable state envelope
- Local-first MCP surface
- Session observation
- Egg custody and hatching
- Included adapters
- Responsibility line

The executable, dependency-free implementation is in `scripts/owl_engine/`. Run its acceptance suite from the skill directory:

```bash
python3 -m unittest discover -s tests -v
```

Run the real local demonstration in an already-authorized workspace:

```bash
python3 scripts/demo_owl_engine.py /path/to/authorized/workspace
```

Run the local-first egg, sitter, artifact, and hatch demonstration:

```bash
python3 scripts/demo_hatchling.py /path/to/authorized/workspace
```

## Session Zero boundary

Session Zero performs one bounded negotiation before Step 1:

1. Bind the visible Target and, separately, any commissioner directions for how it should be realized.
2. Observe only relevant, already-authorized environments.
3. Probe the capabilities Step 1 actually requires.
4. Extend only a demonstrated gap by registering or wrapping the smallest safe existing tool.
5. If user support is necessary, return one precise action and a reduced Step 1.
6. Freeze the capability receipts and begin Step 1 immediately when READY.

Do not ask for secrets, install speculative infrastructure, or keep interviewing after readiness is decidable. A micro correction with no new capability need bypasses discovery and persistence.

Session Zero returns either:

```text
READY: every required capability has evidence; Step 1 has begun
BLOCKED: one missing capability; one user action or reduced Step 1
```

## Provider-neutral contracts

Every environment adapter implements:

```text
describe() -> environment, authority, locator, limits
probe(requirement) -> capability receipt
invoke(request) -> result and evidence
resolve(artifact reference) -> artifact or unavailable
```

The registry dispatches by environment ID and keeps artifact locators opaque to other environments. Provider-specific paths, credentials, APIs, and execution rules stay inside adapters.

An extension implements:

```text
extend(requirement) -> adapter | capability receipt | unavailable
```

Call it only for a required gap. Prefer registering an already-authorized environment over creating a new abstraction or installing infrastructure.

Capability receipts record:

```yaml
name: human-readable capability
environment: stable environment id
operations: [read, write, execute, render, test, observe, resolve, publish]
status: available | configurable | needs-user | unavailable | forbidden
authority: host or person permitting use
locator: opaque capability reference
evidence: successful probe or known limit
```

Configured is not available until a probe succeeds.

## Nest

A Nest is the smallest authorized setting that can support the next complete Pass. Use it only when work spans sources, tools, or environments. It records:

```yaml
environment: where Current and the next Pass are worked
canvas: the intended carrier for the result
materials: [attributed artifact references]
references: [relevant examples or pattern-commons bearings]
```

Canvas, materials, and references are ordinary task language, not new reasoning handles. Keep environment authority and capability evidence in their existing receipts. Reject a Nest that names an unobserved environment or material. Stop discovery once the Nest and required capabilities are sufficient, then begin Step 1. A Micro correction does not create or inspect a Nest.

## Portable state envelope

`StateEnvelope` stores only inspectable task state:

```yaml
target_id: stable-local-name
revision: opaque-backend-version
target:
  name: visible result name
  identity: any-instance | this-instance
  expected: requested artifact or outcome
  scope: authorized boundary
commission:
  commissioner: user or named stakeholder
  directions:
    - category: method | technique | style | tone | presentation | other
      instruction: concise realization direction
      strength: preference | mandate
      scope: pass | instance | default
current: latest accepted result or opaque artifact reference
keep: [protected quality]
marks: [unresolved feedback]
residuals: [visible limitation]
evidence: [test, receipt, or opaque artifact reference]
environments: [environment receipts]
capabilities: [capability receipts]
nest: optional target-local Nest
last_pass: pass name
step1:
  status: ready | blocked | completed
egg:
  id: stable-local-name
  parent_target_id: target that laid it
  parent_revision: revision at laying
  parent_current: exact Current it continues
  mark: reason Current should change
  expected: bounded completed outcome
  status: laid | incubating | blocked | hatched
sessions:
  owl-session-id:
    host: model host label
    identity_basis: host-event | host-tool-metadata | engine-observed | model-declared
    statistics: observed metrics with basis and coverage
```

Omit empty fields. Never store secrets, hidden reasoning, or conversation transcripts.

Keep `commission` outside `target`. Target records what must remain recognizable; Commission records how the commissioner wants it made or presented. Replacing a Commission does not replace the Target. `OwlEngine.set_commission()` performs that update with the same optimistic revision protection used for Passes.

A host may supply commissioner defaults to a new Target, but this target-local envelope does not claim to be a global preference service. Mandates remain subject to authority, safety, factual honesty, and Target feasibility. Preserve an unresolved conflict as a visible residual rather than silently discarding either side.

`InMemoryStateStore` supports process-local state. `FileStateStore` writes atomic JSON in one authorized local workspace. Both reject stale expected revisions with `StateConflict`, which exposes the current revision and the recovery action `reload-current-state-and-reapply-the-mark`. A host may substitute any backend with equivalent `load` and optimistic `save` behavior.

With no state store, claim no persistence. With several environments, retain separate environment IDs, evidence attribution, and opaque artifact references. Never infer that a path or credential crosses an environment boundary.

## Local-first MCP surface

Use MCP as the common tool boundary, not as the source of truth. Keep the core and `FileStateStore` local by default. A local model host may run the included stdio server directly:

```bash
python3 scripts/owl_mcp_server.py --state-dir /authorized/workspace/.owl-state
```

`OwlMcpService` is transport-neutral. A host may mount the same service behind an authorized streamable-HTTP adapter or narrow tunnel for a web model. The skill does not claim that such a remote deployment exists until its adapter is installed and probed.

The surface exposes focused tools to:

- bind or inspect one target;
- register and observe a sitter session;
- lay an egg from Current and a Mark;
- claim or release custody;
- hatch only with an artifact, named evidence, and semantic acceptance;
- close a session without deleting its receipt or the egg; closing automatically releases an unhatched egg for the next sitter.

Do not send transcripts, hidden reasoning, credentials, or broad conversation context through these tools. Keep artifacts local or opaque unless the Target explicitly requires cross-environment transfer.

## Session observation

Treat telemetry as capability-scoped evidence. Every stored statistic records its basis and coverage:

| Basis | What it proves |
|---|---|
| `host-event` | The host supplied a lifecycle event; full-session coverage may be claimed for that metric. |
| `host-tool-metadata` | Tool calls can be correlated within a host session; unrelated turns remain unobserved. |
| `engine-observed` | The engine directly counted its own calls or transitions. |
| `model-declared` | The active model reported a value the host did not expose. |
| `unavailable` | No evidence exists; retain this instead of estimating. |

Store `engine_first_seen_at` separately from a real host start time. Without a host start event, report elapsed engine contact rather than session length. Count meaningful steps only from explicit drawing transitions; never derive them from token count, turns, or tool volume.

A host adapter may implement:

```text
describe() -> host and telemetry capability receipt
open(receipt) -> engine session
observe(event) -> updated basis-scoped statistics
snapshot() -> current session receipt
close(reason) -> final receipt
```

MCP-only hosts can still work correctly. The first engine call opens an engine-observed session when no native key exists. Richer hosts may add lifecycle events without changing the egg or state contracts.

## Egg custody and hatching

An egg is not a backlog item. Lay one only when an inspectable Current and a real Mark define a bounded continuation. Store its parent Current, parent Pass, and revision so unrelated state writes do not break lineage while a changed artifact does.

Use this lifecycle:

```text
laid -> incubating -> hatched
          |    |
          |    +-> blocked
          +------> laid by explicit release
```

Only one active session may hold custody. A released or blocked egg persists for another authorized session. If its sitter closes before hatching, return the egg to `laid` and preserve the closure reason as a residual so dead sessions cannot strand it. Refuse a claim when Current or its last Pass changed after laying; require the new Current to lay a new egg instead of silently rebasing the old one.

A hatch requires all of:

1. intact lineage from the stored parent Current;
2. custody by the submitting active session;
3. a non-empty artifact reference;
4. receipts for every named evidence requirement;
5. an explicit semantic acceptance source.

The engine verifies the deterministic gates and records the acceptance source. The active model or commissioner judges whether the artifact actually answers the expected outcome. Session statistics describe the sitter; they never prove the hatch.

## Included adapters

- `LocalWorkspaceAdapter` is real. It confines paths to one authorized root and executes argument arrays without a shell when execution is enabled.
- `VirtualEnvironmentAdapter` is a deterministic container/VM test double. It owns an isolated artifact namespace and never resolves host paths.
- `EnvironmentRegistry` composes zero, one, or many adapters without changing core logic.

Cloud services, connected apps, browsers, MCP tools, publishing systems, and production container runtimes remain provider adapters supplied by their host. They are intentionally not faked as real integrations here.

## Responsibility line

The engine owns target identity, the separate Commission, Current references, protected qualities, unresolved Marks, capability and environment receipts, evidence locators, optimistic revisions, resumable state, Step 1 readiness, egg lineage and custody, and basis-scoped session receipts.

The language model owns interpretation, creative and technical judgment, what to make, how feedback changes the result, and whether the completed Pass answers the Target.

Apply the 5-Lens Filter to changes. In particular, reject any engine feature whose Session Zero costs more than the Step 1 it enables.
