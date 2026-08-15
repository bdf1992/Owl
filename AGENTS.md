# Repository guidance

Treat `draw-the-owl/SKILL.md` as the behavioral source of truth, `draw-the-owl/references/owl-engine.md` as the engine contract, and `draw-the-owl/references/long-horizon.md` as the lineage, environmental-trial, adoption, and migration contract for work that must survive across sessions or environments.

Preserve these invariants:

- Make a complete, inspectable result rather than substituting a plan.
- Keep Target, Current, Mark, and Pass as the ordinary four-handle kernel.
- Keep Commission separate from Target identity.
- Keep OWL_ENGINE local-first, capability-based, and honest about unavailable evidence.
- Keep long-horizon work as a lineage of bounded descendants, not an endless task queue.
- Do not turn OWL into a universal agent platform or merge Chartwright Assemblies into it.
- Prefer small, sharp language over new taxonomy.

After a change, run:

```bash
python3 -m unittest discover -s draw-the-owl/tests -v
```

When the skill itself changes, also validate the installable `draw-the-owl/` directory with the host skill validator.

