---
name: draw-the-owl
description: "Turn a rough request or exploratory mark into a complete, inspectable result, then redraw that same target from feedback without drifting into another project. Use when the user asks to draw the owl or the rest of it, make the whole thing, move past planning, build an end-to-end slice, preserve a particular result across corrections, continue an adopted artifact, make inkblots and discover what earns attention, or honor commissioner preferences and mandated methods or styles. Apply to prose, code, research, design, systems, games, decisions, and conceptual work. Scale the reply to the edit: a tiny correction may be tiny; a substantial pass may show its construction, media, history, evidence, and current feel. Treat ambiguous follow-ups as changes to the current target unless replacement or combination is explicit. Do not use for diagnosis or review only, or when execution exceeds user authority."
---

# Draw the Owl

Turn an incomplete request into a complete attempt. Put that attempt between participants early enough to inspect, mark, and redraw. Keep drawing the same thing once it has earned recognition unless the user explicitly replaces or combines it.

> Draw shapes. Draw parts. Draw features. Draw the rest of the fucking owl—not an Unfinished Horse.

The metaphor governs completion and continuity. It is not a vocabulary the user must learn, and the Owl is not necessarily an owl-shaped subject. Treat it as a bounded artifact seeking consequential attention from a stakeholder through a pattern commons: the shared examples, forms, and expectations that make the artifact recognizable and judgeable. Sometimes that recognition contract is known before drawing; sometimes the drawing helps discover it.

Do not literalize *owl*, *drawing*, *feathers*, *ink*, or similar metaphor words unless the user actually wants owl imagery. When asked what Owl to draw or sketch, identify or propose the attention-bearing artifact in the current work. An icon or mascot may support that artifact, but it does not replace it.

## Use the four-handle kernel

Keep only four handles active during ordinary work:

- **Target:** the result the request is trying to obtain; during open exploration, the field or question constraining the marks until a particular result earns recognition.
- **Current:** the latest accepted or inspectable result, including what must be preserved.
- **Mark:** feedback, a constraint, evidence, or a discovered reason to change Current.
- **Pass:** a complete new attempt at the authorized scope.

Use ordinary domain language for everything else. Say *function*, *paragraph*, *wing*, *test*, or *screen* instead of inventing generic part names. Name a part separately only when treating it independently could change recognition, correctness, authority, or completion.

Do not make the user or model maintain a taxonomy in order to do the work. Load [deep-continuity.md](references/deep-continuity.md) only when the task genuinely requires deep decomposition, overlapping views, or identity tracking across media.

## Choose the right beginning

Before the target is understood, “owl” is only a placeholder. Use either beginning without making the user select a formal mode:

- **Owl-first:** When the intended artifact and its recognition contract are already visible, bind the placeholder to the actual thing the user wants. After binding a *binary agent*, say *binary agent*, not *owl*.
- **Inkblot-first:** When the user wants to make marks and see what emerges, do not force an early target, stakeholder questionnaire, or requirements interview. Make a complete exploratory artifact within the available field. Offer only a few plausible readings as invitations, not conclusions. Treat attraction, rejection, surprise, and association as Marks. Bind the Target only after something earns attention.

An inkblot is a Pass, not preparation for a later Pass. It may be ambiguous, but it must be substantive enough to inspect and react to. Keep it connected to any supplied materials, constraints, or pattern commons rather than substituting arbitrary noise.

Ask for clarification only when different answers would materially change the result. If the request already supplies enough shape, infer the remaining ordinary details and draw. A named example is a reference unless the user asks for that particular instance.

Distinguish two identity promises:

- **Any instance:** make any result that fits the request.
- **This instance:** preserve the adopted artifact, source, and explicitly protected qualities.

Specificity alone does not mean *this instance*. Once the user adopts a result, treat later ambiguous feedback as Marks on that result. Require an explicit request to replace it or combine it with another target.

## Make the unknown smaller

When the target, cause, or next move is unclear, make the unknown smaller in the greediest, laziest, cleverest way you know how.

Look for the cheapest move that rules out the most: a question, example, comparison, sketch, story, or test. Learn how people who know the domain talk about it; their words often mark useful differences and common causes. Check the big, common possibilities before hunting tiny ones.

See the situation as a story. What was true before? What changed? What acted on what? What was expected? What happened instead? What evidence remains? A good story helps reveal the next useful question.

Use metaphor the same way: to help you notice something. Keep what fits. Drop what does not. The thing is never required to obey the metaphor.

If the thing is in danger, stabilize it first. Keep it alive, stop damage, or contain spread as needed, but do not confuse that with understanding the cause or making the final fix.

A good probe makes the unknown smaller and the next probe easier. Change the thing only enough to learn until you know enough to act. Then stop probing and draw the Pass.

## Honor the commission without redefining the Owl

Treat explicit direction about medium, method, technique, style, tone, or presentation as the **Commission**: how the commissioner wants the Target realized. Keep it separate from Target identity. Replacing watercolor with charcoal can substantially redraw an artifact without changing which artifact it is.

Use the Commission only when supplied; do not turn it into a fifth always-active handle or a required questionnaire. Distinguish:

- **Preference:** optimize for it when compatible with the Target and other requirements.
- **Mandate:** treat it as an acceptance constraint unless authority, safety, factual honesty, or the Target makes it impossible.

Respect the stated scope: this Pass, this adopted instance until changed, or a commissioner default. Apply a default to a new Target only when the user or a real persistent store supplies it; never invent cross-session memory.

When direction conflicts with another requirement, first seek a realization that satisfies both. If none exists, expose the conflict and its consequence rather than silently dropping the Commission or redefining the Target. A change to the Commission is normally a Mark on realization, not a new Target; treat it as a Target change only when it alters what the result must be or do to remain recognizable.

## Make a complete pass

1. Locate Current and the new Mark. Describe them only as much as needed to prevent drift.
2. Choose media and techniques that fit the actual work and apply the current Commission. Name them when they affect interpretation, review, reproduction, or handoff.
3. Make the complete result now. If the full-scale result is too large, make the smallest end-to-end slice that reaches a real outcome and label its limits.
4. Check that the result answers the Target, incorporates the Mark, preserves required continuity, and represents evidence honestly.

Do not substitute a plan, taxonomy, backlog, architecture list, fragments, or pseudocode unless that is the requested result. Do not count tool calls, formatting actions, or incidental files as meaningful work.

When a local patch would leave the whole incoherent, redraw the whole. When the defect is genuinely local, patch it locally. Remove obsolete structure instead of accumulating exceptions.

For substantial work spanning sources, tools, or environments, establish the smallest **Nest** that can support the next Pass: where Current lives, which canvas will carry the result, and which authorized materials and capabilities are available. Use relevant examples from the pattern commons without making the user classify the Target. Stop preparing as soon as a complete Pass is possible, then draw. Micro work skips the Nest entirely.

## Scale the visible response

Match presentation weight to the size and risk of the work:

| Weight | Use when | Visible return |
|---|---|---|
| **Micro** | Typo, small code fix, local wording or style correction | Corrected result or diff, plus any material caveat |
| **Standard** | A meaningful redraw with limited scope | Current/Mark briefly, complete result prominently, concise check |
| **Studio** | New artifact, major redraw, multimodal work, or continuity-sensitive change | An authored sequence showing construction, result, history, and review |
| **Resumable** | Long session, several environments, or work that must survive context loss | Standard or Studio return plus external state handled by `OWL_ENGINE` or a sidecar |

Do not force numbered sections, a visual, a part count, a vibe report, or a signature onto Micro work. Do not use a tiny reply to hide a large or risky change.

For Studio work, choose as many natural sections as the artifact needs. Do not reserve a section number for the final result. Lead with or clearly foreground the result whenever doing so improves contact.

## Use visuals when they carry evidence

Provide an actual visual when the user requests one, the artifact is visual, the task is explicitly multimodal, or construction/history is materially easier to inspect visually. A screenshot, render, diagram, annotated diff, trace, or version strip may qualify.

Do not manufacture a decorative diagram merely to satisfy the skill. For a typo or local logic fix, the corrected text, code diff, or test result is usually the right evidence.

## Sketch, ink, and color only when useful

Use these as ordinary artistic descriptions, not required states:

- **Sketch:** structure remains intentionally reversible.
- **Ink:** freeze the structure for the current pass.
- **Color:** realize the accepted structure to the finish required by the Target.

Keep sketching while structural improvement matters. Ink when the structure works and more sketching would churn. If coloring exposes a structural defect, return to the sketch rather than painting over it. A sketch can be complete when a sketch is what the user requested.

## Externalize session bookkeeping

Do not ask the language model to maintain `n/N`, stage counters, visual-diff ledgers, or rigid signature fields in prose.

When persistent state would materially help, prefer `OWL_ENGINE`. It stores target identity, the Commission as a separate realization contract, current artifact, protected qualities, Marks, evidence, environment observations, and the next useful action outside the conversational response. It works with zero, one, or many local, virtual, and cloud environments through capability-based adapters. For cross-host work, use its local-first MCP surface as the common tool boundary and treat host session telemetry as an optional capability. Keep an egg target-local: it is a bounded continuation derived from Current, not a generic task or a fifth reasoning handle. Read [owl-engine.md](references/owl-engine.md) only when implementing, integrating, or using that state layer. Use the executable core in `scripts/owl_engine/`; validate changes with `python3 -m unittest discover -s tests -v` from the skill directory.

If no engine exists, use a small sidecar or backmatter record only for Resumable work. Keep it machine-readable and out of the user's way. Never pretend a state tool exists.

## Review without changing creatures

Treat ambiguous follow-ups as a detail, correction, changed emphasis, variant, or change of medium before treating them as a new project. Ask:

1. Can this Mark be integrated into Current?
2. Is the user correcting the rendering rather than replacing the Target?
3. What is the smallest coherent redraw that addresses it?

If those answers preserve the Target, continue the same drawing. If a pass changes the Target without authorization, return to the last recognizable Current and redraw from there.

Judge *this instance* by required identity and recognition, not by percentages of unchanged words, pixels, or components. Source lineage can remain intact while the result has stopped being recognizable; report that uncertainty plainly.

## Sign only when signing performs work

Sign a substantial artifact when attribution, method, evidence, handoff, or version identity matters. Use a natural one-line signature or the artifact's native metadata. For example:

`Drawn by Codex from Bdo's Marks · Markdown + semantic compression · evidence: validated locally`

Do not require a signature on minor conversational corrections. Do not imply the user authored agent-made choices, or that the agent originated user-provided Marks.

Offer a concise impression of the whole when it helps review—such as settled, brittle, sparse, lively, or overworked. Identify it as the assistant's impression, not the user's feeling and not evidence.

## Calibrate every rule with the 5-Lens Filter

Retain a rule only when it passes all five lenses simultaneously:

- **Human:** natural and readable for a person inspecting the work.
- **Shared:** creates an immediate common model between person and agent.
- **Model:** direct enough to guide behavior without attention-heavy bookkeeping.
- **Actual:** matches how the artifact is really edited, tested, reviewed, or delivered.
- **Meta:** preserves the premise—draw the complete Target and faithfully redraw that same Target—instead of making the skill administer, explain, or optimize itself.

If a rule fails a lens, simplify it, make it conditional, move it to an on-demand reference or deterministic tool, or delete it. Do not preserve ceremonial structure merely because it is internally consistent.

Apply the filter when adding, changing, or challenging a rule, not as a required visible checklist on every Pass. Make the filter pass itself: use Meta to expose premise drift once, then stop. If recursive self-auditing delays the result or adds more ceremony than it removes, Meta has failed and must be compressed.

## Close on five invariants

Before presenting a Pass, verify only these essentials:

- it is a result rather than preparation for a future result;
- it answers the current Target or exploratory field at the stated scope and honors the compatible Commission;
- it incorporates the relevant Mark;
- it preserves this instance unless replacement was explicit;
- it states consequential limits, uncertainty, and evidence honestly.

Everything else is optional and should earn its token cost from the work.
