from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_ROOT / "SKILL.md"
ENGINE_MD = SKILL_ROOT / "references" / "owl-engine.md"

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from owl_engine.models import CommissionDirection  # noqa: E402
import check_install  # noqa: E402


def commission_categories() -> set[str]:
    """The categories the engine will actually accept."""
    accepted = set()
    for candidate in re.findall(r"[a-z]+", ENGINE_MD.read_text(encoding="utf-8")):
        try:
            CommissionDirection(category=candidate, instruction="probe")
        except ValueError:
            continue
        accepted.add(candidate)
    return accepted


class CommissionVocabularyTests(unittest.TestCase):
    """The prose and the enum must name the same things.

    SKILL.md once listed `medium` as a Commission direction while the engine
    rejected it — and `medium` is the skill's own headline example. Prose that
    the tool cannot record is prose that quietly lies.
    """

    def test_skill_prose_matches_the_engine_enum(self) -> None:
        source = SKILL_MD.read_text(encoding="utf-8")
        sentence = re.search(
            r"Treat explicit direction about (.+?) as the \*\*Commission\*\*", source
        )
        self.assertIsNotNone(sentence, "the Commission sentence moved or was reworded")
        listed = {
            word.strip().removeprefix("or ").strip()
            for word in sentence.group(1).split(",")
        }
        # `other` is the engine's catch-all and deliberately absent from prose.
        self.assertEqual(commission_categories() - {"other"}, listed)

    def test_the_engine_contract_lists_every_accepted_category(self) -> None:
        row = re.search(r"- category: (.+)", ENGINE_MD.read_text(encoding="utf-8"))
        self.assertIsNotNone(row)
        documented = {value.strip() for value in row.group(1).split("|")}
        self.assertEqual(commission_categories(), documented)

    def test_the_headline_example_is_recordable(self) -> None:
        # "Replacing watercolor with charcoal" is how SKILL.md explains the
        # Commission. The engine has to be able to store that direction.
        direction = CommissionDirection(category="medium", instruction="charcoal, not watercolor")
        self.assertEqual("medium", direction.to_dict()["category"])


class InstalledSkillTests(unittest.TestCase):
    def test_the_installed_skill_matches_this_repository(self) -> None:
        install = check_install.DEFAULT_INSTALL
        if not install.is_dir():
            self.skipTest(f"no installed skill at {install}")
        missing, differing, extra = check_install.compare(install)
        self.assertEqual(
            ([], [], []),
            (missing, differing, extra),
            f"the active skill is stale; run: python3 {SKILL_ROOT / 'scripts' / 'check_install.py'}",
        )


if __name__ == "__main__":
    unittest.main()
