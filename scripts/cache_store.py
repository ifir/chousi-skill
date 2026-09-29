"""Select, initialize, and validate chousi cache files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cache_common import load_json, now_iso, write_json
from cache_index import MARKER, write_index


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


def initialize(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    machine, index = cache_paths(root)
    data = load_json(machine, {"version": 1, "items": {}})
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        raise ValueError(f"缓存格式无效，不会覆盖: {machine}")
    data.setdefault("version", 1)
    if not machine.exists():
        data["updated_at"] = now_iso(); write_json(machine, data)
    if not index.exists():
        write_index(index, data)
    return machine, index, data
