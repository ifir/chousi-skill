#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

CHUNK = 64 * 1024
MARKER = "<!-- managed-by: chousi -->"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def modified_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def fingerprint(path: Path) -> str:
    stat = path.stat()
    digest = hashlib.sha256()
    digest.update(f"v2:{stat.st_size}:{stat.st_mtime_ns}:".encode())
    with path.open("rb") as handle:
        digest.update(handle.read(CHUNK))
        if stat.st_size > CHUNK:
            handle.seek(max(0, stat.st_size - CHUNK))
            digest.update(handle.read(CHUNK))
    return digest.hexdigest()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def cache_paths(root: Path) -> tuple[Path, Path]:
    cache = root / ".cache"
    primary = cache / "file2intent.md"
    if primary.exists():
        try:
            owned = MARKER in primary.read_text(encoding="utf-8", errors="replace")[:512]
        except OSError:
            owned = False
        index = primary if owned else cache / ".chousi.file2intent.md"
    else:
        index = primary
    return cache / ".chousi.intent.json", index


def valid_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"检索根目录不存在: {root}")
    return root


def safe_file(root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or ".cache" in relative.parts:
        raise ValueError(f"路径必须是根目录内且不能位于 .cache: {value}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"路径越出检索根目录: {value}") from exc
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"不是可读取的普通文件: {value}")
    return path


def initialize(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    machine, index = cache_paths(root)
    data = load_json(machine, {"version": 1, "items": {}})
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        raise ValueError(f"缓存格式无效，不会覆盖: {machine}")
    data.setdefault("version", 1)
    if not machine.exists():
        data["updated_at"] = now_iso()
        write_json(machine, data)
    if not index.exists():
        write_index(index, data)
    return machine, index, data


def rows(data: dict[str, Any]) -> list[str]:
    output = []
    for key, item in sorted(data.get("items", {}).items()):
        if not isinstance(item, dict):
            continue
        values = [
            key[:16], str(item.get("source", "")), str(item.get("modified_at", "")),
            str(item.get("intent", "")), "、".join(map(str, item.get("keywords", []))),
            str(item.get("method", "")), str(item.get("confidence", "")),
            str(item.get("analyzed_at", "")), "missing" if item.get("missing") else "fresh",
        ]
        output.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    return output


def write_index(path: Path, data: dict[str, Any]) -> None:
    header = (
        f"{MARKER}\n# 抽丝文件内容意图索引缓存\n\n"
        "> 本索引用于避免对未变化文件重复读取；只保存短摘要与证据定位。\n\n"
        "| 缓存指纹 | 当前路径 | 最新修改时间 | 内容意图摘要 | 关键词 | 识别方式 | 置信度 | 识别时间 | 缓存状态 |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    body = "\n".join(rows(data)) or "| - | - | - | 暂无缓存 | - | - | - | - | - |"
    write_text(path, header + body + "\n")


def by_source(data: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    found: dict[str, tuple[str, dict[str, Any]]] = {}
    for key, item in data.get("items", {}).items():
        if isinstance(item, dict) and item.get("source"):
            found[str(item["source"])] = (str(key), item)
    return found


def inspect(root: Path, paths: list[str], data: dict[str, Any]) -> list[dict[str, Any]]:
    known = by_source(data)
    requested = paths or sorted(known)
    results = []
    for value in requested:
        path = root / value
        old = known.get(value)
        if path.is_symlink() or not path.is_file():
            results.append({"path": value, "status": "missing", "cached": bool(old)})
            continue
        path = safe_file(root, value)
        current = fingerprint(path)
        if current in data.get("items", {}):
            status = "fresh"
        elif old:
            status = "stale"
        else:
            status = "uncached"
        results.append({"path": value, "status": status, "fingerprint": current, "cached_fingerprint": old[0] if old else None})
    return results


def parse_evidence(values: list[str]) -> list[dict[str, str]]:
    result = []
    for value in values:
        if "::" not in value:
            raise ValueError("evidence 必须使用 定位::摘要 格式")
        locator, summary = value.split("::", 1)
        result.append({"locator": locator.strip(), "summary": summary.strip()})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="维护抽丝的只读检索缓存")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "index"):
        command = sub.add_parser(name)
        command.add_argument("--root", required=True)
    check = sub.add_parser("inspect")
    check.add_argument("--root", required=True)
    check.add_argument("--path", action="append", default=[])
    record = sub.add_parser("record")
    record.add_argument("--root", required=True)
    record.add_argument("--path", required=True)
    record.add_argument("--intent", required=True)
    record.add_argument("--keyword", action="append", default=[])
    record.add_argument("--evidence", action="append", default=[])
    record.add_argument("--method", choices=("text", "metadata", "pdf", "office", "ocr", "transcription", "keyframes", "combined", "unavailable"), required=True)
    record.add_argument("--confidence", choices=("high", "medium", "low"), required=True)
    args = parser.parse_args()
    try:
        root = valid_root(args.root)
        machine, index, data = initialize(root)
        if args.command == "inspect":
            result: Any = inspect(root, args.path, data)
        elif args.command == "record":
            path = safe_file(root, args.path)
            key = fingerprint(path)
            previous = by_source(data).get(args.path)
            stat = path.stat()
            item = {
                "source": args.path, "modified_at": modified_at(path), "size": stat.st_size,
                "intent": args.intent, "keywords": list(dict.fromkeys(args.keyword)),
                "evidence": parse_evidence(args.evidence), "method": args.method,
                "confidence": args.confidence, "analyzed_at": now_iso(), "missing": False,
            }
            if previous and previous[0] != key:
                item["supersedes"] = previous[0]
            data["items"][key] = item
            data["updated_at"] = now_iso()
            write_json(machine, data)
            write_index(index, data)
            result = {"recorded": args.path, "fingerprint": key, "index": str(index)}
        elif args.command == "index":
            write_index(index, data)
            result = {"index": str(index), "items": len(data["items"])}
        else:
            result = {"machine_cache": str(machine), "index": str(index), "items": len(data["items"])}
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
