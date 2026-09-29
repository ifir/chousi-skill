"""Check file freshness and direction coverage without changing cache."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cache_common import by_source, fingerprint, normalized, safe_file


def direction_coverage(item: dict[str, Any], direction: str, keywords: list[str]) -> str:
    requested_direction = normalized(direction)
    requested_keywords = {normalized(value) for value in keywords if normalized(value)}
    cached_keywords: set[str] = set()
    for entry in item.get("directions", []):
        if not isinstance(entry, dict):
            continue
        if requested_direction and normalized(str(entry.get("direction", ""))) == requested_direction:
            return "exact-direction"
        cached_keywords.update(normalized(str(value)) for value in entry.get("keywords", []) if normalized(str(value)))
    return "all-keywords" if requested_keywords and requested_keywords.issubset(cached_keywords) else "uncovered"


def inspect(root: Path, paths: list[str], data: dict[str, Any], direction: str, keywords: list[str]) -> list[dict[str, Any]]:
    known = by_source(data); requested = paths or sorted(known); results = []
    for value in requested:
        path = root / value; old = known.get(value)
        if path.is_symlink() or not path.is_file():
            results.append({"path": value, "status": "missing", "cached": bool(old)}); continue
        path = safe_file(root, value); current = fingerprint(path); cached = data.get("items", {}).get(current); coverage = None
        if isinstance(cached, dict):
            coverage = direction_coverage(cached, direction, keywords) if direction or keywords else "not-requested"
            status = "fresh" if coverage == "not-requested" else ("fresh-covered" if coverage != "uncovered" else "fresh-uncovered")
        else:
            status = "stale" if old else "uncached"
        results.append({"path": value, "status": status, "coverage": coverage, "fingerprint": current, "cached_fingerprint": old[0] if old else None})
    return results
