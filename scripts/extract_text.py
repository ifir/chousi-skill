#!/usr/bin/env python3
"""Extract bounded searchable text from supported local document formats."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT = {".md", ".txt", ".log", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".html", ".htm", ".js", ".ts", ".py", ".java", ".go", ".rs", ".sql"}
OOXML = {".docx", ".pptx", ".xlsx", ".epub"}


def _xml_text(data: bytes) -> str:
    root = ET.fromstring(data)
    return " ".join((node.text or "").strip() for node in root.iter() if node.tag.endswith(("}t", "}v")) and (node.text or "").strip())


def _ooxml(path: Path) -> list[dict[str, str]]:
    sections = []
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith((".xml", ".xhtml", ".html", ".htm"))]
        for name in names:
            try:
                text = _xml_text(archive.read(name))
            except (ET.ParseError, KeyError):
                continue
            if text:
                sections.append({"locator": name, "text": text})
    return sections


def _display_locator(path: Path, locator: str) -> str:
    if path.suffix.lower() == ".pptx":
        match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", locator)
        if match:
            return f"第{match.group(1)}页"
    return locator


def _pdf(path: Path) -> list[dict[str, str]]:
    command = shutil.which("pdftotext")
    if command:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "document.txt"
            process = subprocess.run([command, str(path), str(output)], capture_output=True, text=True, check=False)
            if process.returncode == 0 and output.is_file():
                return [{"locator": "text-layer", "text": output.read_text(encoding="utf-8", errors="replace")} ]
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF 文本层读取需要本机 pdftotext 或 pypdf") from exc
    reader = PdfReader(str(path))
    return [{"locator": f"第{index}页", "text": page.extract_text() or ""} for index, page in enumerate(reader.pages, 1)]


def extract(path: Path) -> tuple[str, list[dict[str, str]]]:
    suffix = path.suffix.lower()
    if suffix in TEXT:
        return "text", [{"locator": "全文", "text": path.read_text(encoding="utf-8", errors="replace")}]
    if suffix in OOXML:
        return "office", _ooxml(path)
    if suffix == ".pdf":
        return "pdf", _pdf(path)
    raise ValueError(f"不支持的文本提取格式: {suffix or '<无扩展名>'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="按文件结构提取可检索文本；默认只返回匹配片段")
    parser.add_argument("path", type=Path); parser.add_argument("--pattern")
    parser.add_argument("--context", type=int, default=300); parser.add_argument("--max-hits", type=int, default=5)
    args = parser.parse_args(); path = args.path.expanduser().resolve()
    if not path.is_file() or path.is_symlink(): parser.error(f"不是可读取的普通文件: {path}")
    try:
        method, sections = extract(path)
        hits = []
        if args.pattern:
            regex = re.compile(args.pattern, re.I)
            for section in sections:
                for match in regex.finditer(section["text"]):
                    radius = max(100, min(args.context, 500)) // 2
                    candidate = {"locator": _display_locator(path, section["locator"]), "text": section["text"][max(0, match.start()-radius):match.end()+radius]}
                    if not hits or candidate["locator"] != hits[-1]["locator"]:
                        hits.append(candidate)
                    if len(hits) >= max(1, min(args.max_hits, 5)): break
                if len(hits) >= max(1, min(args.max_hits, 5)): break
        result = {"source": str(path), "method": method, "sections": len(sections), "matches": hits}
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
