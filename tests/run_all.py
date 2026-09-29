#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "scripts" / "cache_manager.py"
EXTRACT = ROOT / "scripts" / "extract_text.py"


def run(script: Path, *args: str) -> dict:
    process = subprocess.run(["python3", str(script), *args], check=True, text=True, capture_output=True)
    return json.loads(process.stdout)


class CacheTests(unittest.TestCase):
    def test_direction_coverage_and_staleness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); file = root / "note.md"; file.write_text("alpha topic", encoding="utf-8")
            run(CACHE, "init", "--root", str(root))
            self.assertEqual(run(CACHE, "inspect", "--root", str(root), "--path", "note.md", "--direction", "alpha")[0]["status"], "uncached")
            run(CACHE, "record", "--root", str(root), "--path", "note.md", "--direction", "alpha", "--intent", "alpha", "--keyword", "alpha", "--evidence", "L1::alpha topic", "--method", "text", "--confidence", "high")
            self.assertEqual(run(CACHE, "inspect", "--root", str(root), "--path", "note.md", "--direction", "alpha")[0]["status"], "fresh-covered")
            self.assertEqual(run(CACHE, "inspect", "--root", str(root), "--path", "note.md", "--direction", "beta")[0]["status"], "fresh-uncovered")
            file.write_text("changed", encoding="utf-8")
            self.assertEqual(run(CACHE, "inspect", "--root", str(root), "--path", "note.md")[0]["status"], "stale")

    def test_foreign_index_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); cache = root / ".cache"; cache.mkdir(); index = cache / "file2intent.md"; index.write_text("foreign\n")
            run(CACHE, "init", "--root", str(root))
            self.assertEqual(index.read_text(), "foreign\n")
            self.assertTrue((cache / ".chousi.file2intent.md").is_file())


class ExtractTests(unittest.TestCase):
    def test_text_snippets_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "note.md"; file.write_text(("before " * 100) + "needle" + (" after" * 100))
            result = run(EXTRACT, str(file), "--pattern", "needle", "--context", "300")
            self.assertEqual(len(result["matches"]), 1); self.assertLessEqual(len(result["matches"][0]["text"]), 306)

    def test_docx_like_xml_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.docx"
            with zipfile.ZipFile(file, "w") as archive:
                archive.writestr("word/document.xml", '<w:document xmlns:w="urn:test"><w:p><w:r><w:t>HN版 IMLP 咨询页</w:t></w:r></w:p></w:document>')
            result = run(EXTRACT, str(file), "--pattern", "IMLP")
            self.assertEqual(result["method"], "office"); self.assertEqual(len(result["matches"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
