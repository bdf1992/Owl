# OWL

OWL is the home of **Draw the Owl** and **OWL_ENGINE**.

Draw the Owl turns a rough request or exploratory mark into a complete, inspectable result, then redraws that same target from feedback without drifting into another project.

OWL_ENGINE keeps the deterministic work out of the model's prose: target identity, commission, current artifact, marks, evidence, environment observations, sessions, and bounded continuation.

The [complete example gallery](examples/) supplies a small pattern commons: three dependency-free browser tools that make, revise, preserve, and export a real result.

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
examples/
├── magic-calendar/          # Calendar with a useful derived suggestion
├── sketch-app/              # Drawing, history, persistence, and PNG export
└── ui-design-space/         # Parameter space compiled into a token system
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

Expected: 28 tests pass. The JavaScript syntax check is skipped only when Node is unavailable.

Run the demonstrations:

```bash
python3 draw-the-owl/scripts/demo_owl_engine.py
python3 draw-the-owl/scripts/demo_hatchling.py
```

Open the complete examples without a build step:

```bash
python3 -m http.server --directory examples 8000
```

Then visit `http://localhost:8000`.

## Scope boundary

This repository extends the existing Draw the Owl skill. It is not a universal agent platform, a replacement methodology, or the Chartwright Assemblies project.

The governing engine principle is:

> Broad tool surface; narrow purpose.

Every capability must help draw the current Target faithfully. Rules are retained only when they remain natural for a human, shared between participants, direct for the model, true to actual work, and faithful to the premise.
