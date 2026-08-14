# Deep continuity

Read this reference only when a task requires semantic decomposition, overlapping views, or identity tracking across several media. Do not load it for ordinary edits.

## Purpose

Use a deeper part record when a meaningful requirement must survive movement between conversation, specification, code, test, image, or interface. Keep this structure internal unless exposing it helps the user inspect the work.

```text
Part =
  Name
  + Target role
  + View and path
  + Depth and parent
  + Source or authorship
  + State
  + Continuity condition
  + Evidence status
```

The part carries target meaning. A paragraph, function, layer, frame, or test carries its expression. One meaningful part may appear through several carriers without becoming several parts.

## Decide when something becomes a part

Treat a detail as implicit inside its parent until independent treatment matters. Name it separately only when failing to do so could damage recognition, coherence, authority, evidence, or completion.

Use four states when they help:

- **Implicit:** carried by a parent and not tracked separately.
- **Named:** independently addressable.
- **Active:** being treated now.
- **Residual:** unresolved and deliberately kept visible.

Depth is the number of decompositions from the whole. Depth 0 is the whole; depth 1 contains major parts. Stop decomposing when smaller distinctions no longer affect the target.

## Permit overlapping views

Structural, functional, experiential, visual, behavioral, and evidentiary views may divide the same whole differently. They do not need one universal tree.

Keep one part across views when its target role and continuity condition remain the same. Split it only when the views give it independently meaningful roles or preservation requirements.

## Track continuity across media

Treat two realizations as the same part when:

- source or authorship remains traceable;
- the target role remains the same;
- its continuity condition still holds or was explicitly revised by feedback;
- evidence links the realizations.

Names, locations, carriers, techniques, and states may change. If the mapping is uncertain, keep that uncertainty visible rather than inventing certainty.

Use domain language in the visible result. Do not make the user translate this record into the terms of their own artifact.
