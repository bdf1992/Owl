# Long-horizon lineage

Use long horizon when an accepted Owl must keep changing across sessions, environments, migrations, or autonomous work without losing its identity.

Do not turn the Owl into an endless task list. Let an accepted Owl lay bounded Eggs. Each Egg carries enough of its parent that another sitter can work independently and later prove what hatched.

## The small loop

```text
Draw Owl
   ↓
Lay Egg
   ↓
Hatch
   ↓
Resemble?
   ↓
Survive required trials?
   ↓
Adopt
   ↓
Lay next Egg
```

These words answer different questions:

- **Hatch:** Did the bounded descendant actually come into existence and do what the Egg promised?
- **Resemblance:** Does the hatch still preserve what mattered about its parent?
- **Trial:** Does it keep doing that in an environment or condition it is expected to survive?
- **Adopt:** Is this hatch trustworthy enough to become the new parent Current?

Hatching proves existence. Adoption proves trustworthy descent.

Do not add animal stages merely to narrate progress. A failed trial is a Mark, not a new creature type.

## What an Egg inherits

An Egg is a bounded expected descendant, not a backlog item. It should retain only what another sitter needs to preserve lineage and judge the result:

```yaml
parent_target_id: who laid it
parent_current: exact parent artifact or description
parent_pass: pass that produced the parent
mark: why a descendant is needed
expected: what should hatch
inherit: [qualities that must still resemble the parent]
bounds: [what may change]
required_evidence: [what proves the hatch exists and works]
required_trials:
  - id: stable trial name
    environment: where or under what condition it must survive
    expected: what must remain true there
```

Prefer existing `keep`, Target, Commission, environment receipts, and capability receipts as the source of inherited constraints. Do not duplicate the whole parent state into every Egg.

## Hatch before trust

A hatch is an inspectable candidate descendant. Require intact lineage, custody, an artifact, the Egg's named hatch evidence, and semantic acceptance that the artifact answers `expected`.

A hatch may become inspectable Current so it can be exercised, repaired, and reviewed. That does **not** mean it is yet trusted to parent the next generation when required trials remain.

If an Egg names no required trials, preserve the current simple behavior: semantic hatch acceptance is enough to adopt it. Long-horizon survival gates are opt-in and additive.

## Trial the actual hatch

A trial receipt belongs to the exact hatch Current it exercised:

```yaml
trial_id: restart
current: exact hatch Current or artifact reference
environment: local-workspace
result: passed | failed | blocked
evidence: opaque receipt or artifact reference
observed_by: source of the judgment
```

Changing the hatch invalidates earlier trial receipts unless the trial explicitly proves the changed artifact. Never carry trial success forward by assumption.

A trial should answer a real environmental question, for example:

- does it survive restart or loss of conversational context?
- does it work with real project data rather than a fixture?
- does it preserve identity across another host, operating system, tool surface, or permission boundary?
- does failure leave enough state to recover?
- does an upgrade preserve old artifacts and open Eggs?
- can another authorized sitter continue without reconstructing hidden context?

The environment exists to let reality disagree with the drawing. Do not manufacture trials that cannot change confidence.

## Adopt only after resemblance and survival

When required trials exist, adoption requires:

1. the hatch still answers the Egg's expected outcome;
2. the named inherited qualities still resemble the parent;
3. every required trial has a passing receipt against the current hatch;
4. a named acceptance source judges the descendant trustworthy enough to continue the lineage.

Record resemblance as a short judgment with evidence, not a percentage similarity score.

```yaml
adoption:
  current: exact adopted Current
  resembles_parent: concise judgment
  evidence: [supporting receipts]
  accepted_by: commissioner, active model, test harness, or named authority
```

Only an adopted hatch should be allowed to parent a new long-horizon Egg.

## Preserve lineage

Do not overwrite the only record of a completed generation when the next Egg is laid. Archive adopted Eggs as a small lineage receipt:

```yaml
lineage:
  - egg_id: prior bounded continuation
    parent_current: where it came from
    adopted_current: what survived
    hatch_evidence: [opaque receipts]
    trial_evidence: [opaque receipts]
    adoption: concise resemblance and acceptance record
```

Lineage is evidence of descent, not a transcript. Keep it compact and inspectable.

Long horizon is therefore not one immortal session. It is a chain of bounded descendants that can survive context loss:

```text
parent Current
   ↓
Egg
   ↓
independent sitter
   ↓
hatch + evidence
   ↓
trials
   ↓
adopted Current
   ↓
next Egg
```

## Know when a new Owl has appeared

Ordinary descendants remain changes to the same Target while identity and the recognition contract still hold.

If accumulated descendants materially change what the result is, what it is for, or how the commissioner recognizes it, do not silently mutate the old Target. Bring the commissioner back at that recognition boundary:

1. What Shapes are now visible?
2. What are those Shapes Parts of?
3. What Features matter?
4. What new Whole are we now agreeing to draw?

Bind the newly recognized Target as a new Owl and preserve its ancestry as evidence. Then it may lay Eggs of its own.

## Migration is a trial of identity

A migration changes how the Owl is carried. It must not silently change which Owl it is.

Treat migration as an environmental trial whenever state, artifact format, repository layout, host, storage backend, or engine schema changes. A successful migration should preserve, as applicable:

- Target identity;
- Commission;
- Current;
- protected qualities;
- unresolved Marks and residuals;
- open Egg custody and expectations;
- lineage;
- interpretable evidence.

A migration that cannot preserve a load-bearing identity constraint is not merely a migration. Expose the loss and redraw or bind a new Target instead.

Schema migration remains deterministic engine work. Semantic resemblance remains a judgment. Do not let a successful JSON/schema conversion stand in for proof that the Owl survived.

## Minimal state extension

The executable engine can grow toward this contract additively:

```yaml
egg:
  # existing parent, Mark, expected, bounds, hatch evidence...
  inherit: [protected quality]
  required_trials: [trial contract]
  trials: [trial receipt]
  adoption: optional adoption receipt

lineage: [archived adopted egg receipts]
```

Existing state files without these fields remain valid. Existing Eggs without `required_trials` retain the current hatch-and-continue behavior. Additive fields should require no destructive migration; the migration tool only needs to preserve them once the runtime schema knows them.

## Long-horizon invariant

> Keep a recognizable lineage alive across bounded acts of creation. Let accepted Owls lay Eggs that can survive sessions and environments. Hatch them against evidence. Trial them where they must live. Preserve resemblance without demanding sameness. Adopt only what can carry the lineage forward. When the descendants become something new, name the new Owl and draw it together.
