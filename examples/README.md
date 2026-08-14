# Complete example gallery

These examples are small enough to understand in one sitting and complete enough to use. Each one takes a recognizable request through the same end-to-end product loop:

1. enter or make something;
2. see the result immediately;
3. revise it without starting over;
4. keep the work between visits;
5. export a durable artifact.

Open [`index.html`](index.html) to enter the gallery, or open any example directly. No build step, package install, account, or network connection is required.

| Example | Complete outcome | Patterns demonstrated |
|---|---|---|
| [Magic Calendar](magic-calendar/index.html) | Plan events and reveal the next lightly scheduled focus opening | Derived suggestions, date navigation, form validation, local persistence, JSON export |
| [Sketch App](sketch-app/index.html) | Draw, erase, undo, redo, resume, and export a PNG | Pointer input, command history, responsive canvas, keyboard shortcuts, local persistence |
| [UI Design Space](ui-design-space/index.html) | Explore a bounded design space and produce a reusable token system | Tokens as source of truth, live component proof, preset comparison, policy derivation, JSON/CSS export |

## Common pattern contract

Every example keeps these behaviors visible in the interface:

- **One primary result.** The calendar, drawing, or component preview dominates the page.
- **Immediate feedback.** Input changes the result without an apply step.
- **Reversible edits.** Destructive actions ask first; drawing history supports undo and redo.
- **Local-first state.** Work is stored in `localStorage` when the browser permits it, with an honest status when it does not.
- **Portable output.** Each example exports a standard artifact: JSON, PNG, or design-token files.
- **Keyboard and screen-reader basics.** Native controls, visible focus, semantic landmarks, and live status messages are used throughout.
- **No hidden service.** The examples make no network calls and require no backend.

These are reference implementations, not a shared framework. Repetition between the files is intentional: each example remains inspectable and portable on its own.

