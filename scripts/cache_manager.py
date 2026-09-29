#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from cache_common import valid_root
from cache_index import write_index
from cache_inspect import inspect
from cache_record import record
from cache_store import initialize


def main() -> int:
    parser = argparse.ArgumentParser(description="维护抽丝的只读检索缓存")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "index"):
        command = sub.add_parser(name)
        command.add_argument("--root", required=True)
    check = sub.add_parser("inspect")
    check.add_argument("--root", required=True)
    check.add_argument("--path", action="append", default=[])
    check.add_argument("--direction", default="")
    check.add_argument("--keyword", action="append", default=[])
    save = sub.add_parser("record")
    save.add_argument("--root", required=True)
    save.add_argument("--path", required=True)
    save.add_argument("--direction", required=True)
    save.add_argument("--intent", required=True)
    save.add_argument("--keyword", action="append", default=[])
    save.add_argument("--evidence", action="append", default=[])
    save.add_argument("--method", choices=("text", "metadata", "pdf", "office", "ocr", "transcription", "keyframes", "combined", "unavailable"), required=True)
    save.add_argument("--confidence", choices=("high", "medium", "low"), required=True)
    args = parser.parse_args()
    try:
        root = valid_root(args.root)
        machine, index, data = initialize(root)
        if args.command == "inspect":
            result = inspect(root, args.path, data, args.direction, args.keyword)
        elif args.command == "record":
            result = record(root, machine, index, data, args)
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
