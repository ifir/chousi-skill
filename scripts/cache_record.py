"""Validate and persist one direction-aware cache record."""
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from cache_common import by_source, fingerprint, modified_at, normalized, now_iso, safe_file, write_json
from cache_index import write_index


def parse_evidence(values: list[str]) -> list[dict[str, str]]:
    result = []
    for value in values:
        if "::" not in value:
            raise ValueError("evidence 必须使用 定位::摘要 格式")
        locator, summary = (part.strip() for part in value.split("::", 1))
        if not locator or not summary:
            raise ValueError("evidence 的定位和摘要不能为空")
        result.append({"locator": locator, "summary": summary})
    return result


def record(root: Path, machine: Path, index: Path, data: dict[str, Any], args: Namespace) -> dict[str, Any]:
    path = safe_file(root, args.path); key = fingerprint(path); previous = by_source(data).get(args.path); stat = path.stat()
    previous_item = data["items"].get(key, {}); directions = list(previous_item.get("directions", [])) if isinstance(previous_item, dict) else []
    direction_key = normalized(args.direction)
    directions = [entry for entry in directions if not isinstance(entry, dict) or normalized(str(entry.get("direction", ""))) != direction_key]
    analyzed_at = now_iso(); evidence = parse_evidence(args.evidence); keywords = list(dict.fromkeys(args.keyword))
    directions.append({"direction": args.direction, "keywords": keywords, "intent": args.intent, "evidence": evidence,
                       "method": args.method, "confidence": args.confidence, "analyzed_at": analyzed_at})
    item = {"source": args.path, "modified_at": modified_at(path), "size": stat.st_size, "intent": args.intent,
            "keywords": keywords, "evidence": evidence, "method": args.method, "confidence": args.confidence,
            "analyzed_at": analyzed_at, "missing": False, "directions": directions}
    if previous and previous[0] != key:
        item["supersedes"] = previous[0]
    data["items"][key] = item; data["updated_at"] = now_iso(); write_json(machine, data); write_index(index, data)
    return {"recorded": args.path, "fingerprint": key, "index": str(index)}
