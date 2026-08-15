from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from owl_engine import (  # noqa: E402
    InMemoryStateStore,
    Mark,
    OwlEngine,
    TargetBinding,
)


def bind(engine: OwlEngine, target_id: str = "owl") -> str:
    state = engine.bind_target(
        TargetBinding(
            target_id=target_id,
            name="bounded result",
            identity="any-instance",
            expected="one complete Step 1",
            scope="a single local workspace",
        )
    )
    return state.revision


class MarkAuthorshipTests(unittest.TestCase):
    def test_a_mark_must_name_a_known_source(self) -> None:
        with self.assertRaises(ValueError):
            Mark(text="looks wrong", source="stakeholder")

    def test_bare_strings_load_as_unattributed(self) -> None:
        # State written before Marks carried authorship must not silently
        # acquire commissioner authority on load.
        self.assertEqual("unattributed", Mark.coerce("older feedback").source)


class AttentionCounterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OwlEngine(InMemoryStateStore())
        self.revision = bind(self.engine)

    def draw(self, *marks: Mark) -> None:
        state = self.engine.record_pass(
            "owl",
            expected_revision=self.revision,
            current="a pass",
            marks=marks,
        )
        self.revision = state.revision

    def test_an_unmarked_pass_leaves_the_target_awaiting_the_commissioner(self) -> None:
        self.draw()
        attention = self.engine.attention("owl")
        self.assertTrue(attention["awaiting_commissioner_mark"])
        self.assertEqual(1, attention["passes_since_commissioner_mark"])
        self.assertEqual("engine-observed", attention["basis"])

    def test_the_drawer_cannot_mark_itself_attended_to(self) -> None:
        # The failure this whole mechanism exists for: a drawer supplying its
        # own reaction and proceeding as though the commissioner had spoken.
        self.draw(Mark(text="I think layers are the parts", source="drawer"))
        self.assertTrue(self.engine.attention("owl")["awaiting_commissioner_mark"])

    def test_evidence_does_not_stand_in_for_the_commissioner(self) -> None:
        self.draw(Mark(text="benchmark regressed 8%", source="evidence"))
        self.assertTrue(self.engine.attention("owl")["awaiting_commissioner_mark"])

    def test_a_commissioner_mark_clears_the_count(self) -> None:
        self.draw()
        self.draw()
        self.draw(Mark(text="not layers - roles", source="commissioner"))
        attention = self.engine.attention("owl")
        self.assertFalse(attention["awaiting_commissioner_mark"])
        self.assertEqual(0, attention["passes_since_commissioner_mark"])
        self.assertEqual("not layers - roles", attention["last_commissioner_mark"])

    def test_the_count_reproduces_an_unattended_run(self) -> None:
        # Shapes, then parts, then features, then whole - four passes with the
        # commissioner never asked. The counter is what makes that visible.
        for _ in range(4):
            self.draw(Mark(text="drawer proposal", source="drawer"))
        self.assertEqual(4, self.engine.attention("owl")["passes_since_commissioner_mark"])

    def test_outstanding_marks_are_reported_by_source(self) -> None:
        self.draw(
            Mark(text="the eraser bleeds through", source="commissioner"),
            Mark(text="tests fail on Windows", source="evidence"),
        )
        self.assertEqual(
            {"commissioner": 1, "evidence": 1},
            self.engine.attention("owl")["outstanding_marks_by_source"],
        )

    def test_a_settled_target_stores_no_counter(self) -> None:
        self.draw(Mark(text="good, keep going", source="commissioner"))
        self.assertNotIn("passes_since_commissioner_mark", self.engine.load("owl").to_dict())

    def test_an_overdue_target_stores_the_counter(self) -> None:
        self.draw()
        self.assertEqual(1, self.engine.load("owl").to_dict()["passes_since_commissioner_mark"])


if __name__ == "__main__":
    unittest.main()
