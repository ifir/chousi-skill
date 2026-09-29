"""Shared path, fingerprint, JSON, and time helpers."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

CHUNK = 64 * 1024


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


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


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


def by_source(data: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    return {
        str(item["source"]): (str(key), item)
        for key, item in data.get("items", {}).items()
        if isinstance(item, dict) and item.get("source")
    }
