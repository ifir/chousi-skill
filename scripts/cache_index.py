"""Generate the user-readable chousi cache index."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cache_common import write_text

MARKER = "<!-- managed-by: chousi -->"


def write_index(path: Path, data: dict[str, Any]) -> None:
    rows = []
    for key, item in sorted(data.get("items", {}).items()):
        if not isinstance(item, dict):
            continue
        values = [key[:16], str(item.get("source", "")), str(item.get("modified_at", "")),
                  str(item.get("intent", "")), "、".join(map(str, item.get("keywords", []))),
                  str(item.get("method", "")), str(item.get("confidence", "")),
                  str(item.get("analyzed_at", "")), "missing" if item.get("missing") else "fresh"]
        rows.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    header = (f"{MARKER}\n# 抽丝文件内容意图索引缓存\n\n"
              "> 本索引用于避免对未变化文件重复读取；只保存短摘要与证据定位。\n\n"
              "| 缓存指纹 | 当前路径 | 最新修改时间 | 内容意图摘要 | 关键词 | 识别方式 | 置信度 | 识别时间 | 缓存状态 |\n"
              "|---|---|---|---|---|---|---|---|---|\n")
    write_text(path, header + ("\n".join(rows) or "| - | - | - | 暂无缓存 | - | - | - | - | - |") + "\n")
