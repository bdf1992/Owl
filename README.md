# OWL

OWL is the home of **Draw the Owl** and **OWL_ENGINE**.

Draw the Owl turns a rough request or exploratory mark into a complete, inspectable result, then redraws that same target from feedback without drifting into another project.

OWL_ENGINE keeps the deterministic work out of the model's prose: target identity, commission, current artifact, marks, evidence, environment observations, sessions, and bounded continuation.

> Draw shapes. Draw parts. Draw features. Draw the rest of the fucking owl—not an Unfinished Horse.

## What is here

```text
draw-the-owl/
├── SKILL.md                 # Core behavior and four-handle kernel
├── agents/openai.yaml       # Skill interface metadata
├── assets/                  # Draw the Owl and OWL_ENGINE icons
├── references/              # Deep continuity and engine contracts
├── scripts/
│   ├── owl_engine/          # State, environments, sessions, eggs, and MCP
│   ├── owl_mcp_server.py    # Local-first MCP entry point
│   └── demo_*.py            # Executable demonstrations
└── tests/                   # Acceptance tests
```

The ordinary reasoning surface stays small:

- **Target** — the result being sought.
- **Current** — the latest accepted or inspectable result.
- **Mark** — feedback, evidence, or a reason to change Current.
- **Pass** — a complete new attempt at the authorized scope.

The **Commission** records how the commissioner wants the Target realized. It is intentionally separate from Target identity.

## Verify

Requires Python 3.11 or newer. The current implementation uses only the standard library.

```bash
python3 -m unittest discover -s draw-the-owl/tests -v
```

Expected: 22 tests pass.

Run the demonstrations:

```bash
python3 draw-the-owl/scripts/demo_owl_engine.py
python3 draw-the-owl/scripts/demo_hatchling.py
```

## Scope boundary

This repository extends the existing Draw the Owl skill. It is not a universal agent platform, a replacement methodology, or the Chartwright Assemblies project.

The governing engine principle is:

> Broad tool surface; narrow purpose.

Every capability must help draw the current Target faithfully. Rules are retained only when they remain natural for a human, shared between participants, direct for the model, true to actual work, and faithful to the premise.

