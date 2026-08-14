from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "examples"
EXAMPLE_PATHS = {
    "magic-calendar": EXAMPLES_ROOT / "magic-calendar" / "index.html",
    "sketch-app": EXAMPLES_ROOT / "sketch-app" / "index.html",
    "ui-design-space": EXAMPLES_ROOT / "ui-design-space" / "index.html",
}


class DocumentShape(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.links: list[str] = []
        self.title_depth = 0
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        if tag == "title":
            self.title_depth += 1
        if tag == "a":
            attributes = dict(attrs)
            if attributes.get("href"):
                self.links.append(str(attributes["href"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title += data


class CompleteExampleTests(unittest.TestCase):
    def test_gallery_links_resolve(self) -> None:
        gallery_path = EXAMPLES_ROOT / "index.html"
        parser = DocumentShape()
        parser.feed(gallery_path.read_text(encoding="utf-8"))
        linked_examples = {
            (EXAMPLES_ROOT / link).resolve()
            for link in parser.links
            if link.endswith("index.html")
        }
        self.assertEqual(set(EXAMPLE_PATHS.values()), linked_examples)
        for path in linked_examples:
            self.assertTrue(path.is_file(), path)

    def test_example_pages_have_document_landmarks(self) -> None:
        for name, path in EXAMPLE_PATHS.items():
            with self.subTest(example=name):
                parser = DocumentShape()
                parser.feed(path.read_text(encoding="utf-8"))
                self.assertTrue(parser.title.strip())
                self.assertIn("main", parser.tags)
                self.assertIn("script", parser.tags)
                self.assertIn("button", parser.tags)

    def test_examples_have_no_remote_runtime_dependencies(self) -> None:
        remote_attribute = re.compile(r"(?:src|href)=[\"']https?://", re.IGNORECASE)
        network_call = re.compile(r"\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(")
        for name, path in EXAMPLE_PATHS.items():
            source = path.read_text(encoding="utf-8")
            with self.subTest(example=name):
                self.assertIsNone(remote_attribute.search(source))
                self.assertIsNone(network_call.search(source))

    def test_every_example_persists_and_exports_work(self) -> None:
        for name, path in EXAMPLE_PATHS.items():
            source = path.read_text(encoding="utf-8")
            with self.subTest(example=name):
                self.assertIn("localStorage", source)
                self.assertRegex(source, r"download\s*=")
                self.assertIn("role=\"status\"", source)

    def test_each_example_reaches_its_specific_outcome(self) -> None:
        calendar = EXAMPLE_PATHS["magic-calendar"].read_text(encoding="utf-8")
        sketch = EXAMPLE_PATHS["sketch-app"].read_text(encoding="utf-8")
        design_space = EXAMPLE_PATHS["ui-design-space"].read_text(encoding="utf-8")
        self.assertIn("revealOpening", calendar)
        self.assertIn("reserveProposal", calendar)
        self.assertIn("pointerdown", sketch)
        self.assertIn("const undo", sketch)
        self.assertIn("const tokens", design_space)
        self.assertIn("Derived policy", design_space)

    @unittest.skipUnless(shutil.which("node"), "Node is optional; browser syntax is checked when available")
    def test_inline_scripts_pass_javascript_syntax_check(self) -> None:
        script_pattern = re.compile(r"<script>(.*?)</script>", re.DOTALL)
        for name, path in EXAMPLE_PATHS.items():
            source = path.read_text(encoding="utf-8")
            scripts = script_pattern.findall(source)
            self.assertTrue(scripts, name)
            for script in scripts:
                with self.subTest(example=name):
                    result = subprocess.run(
                        ["node", "--check"],
                        input=script,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
