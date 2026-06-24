#!/usr/bin/env python3
"""Fail when deleted frontend mock/Agent adapters reappear."""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
FORBIDDEN_FILES = [
    "frontend/src/lib/api/mockClient.ts",
    "frontend/src/lib/api/spoonClient.ts",
    "frontend/src/lib/api/spoonAgent.ts",
    "frontend/src/lib/store/localStore.ts",
    "frontend/src/lib/store/schema.ts",
    "frontend/lib/api.ts",
    "frontend/lib/abi.ts",
]
FORBIDDEN_PATTERNS = [
    "mockClient",
    "spoonClient",
    "spoonAgent",
    "SpoonOSReactAgent",
    "SpoonOSGraphAgent",
    "localStore",
    "STORE_EVENT",
    "resetStore",
    "loadStore",
    "saveStore",
    "../store/schema",
    "lib/store/schema",
]
SCAN_ROOTS = [
    REPO / "frontend",
]


def iter_source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {"node_modules", ".next"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        yield path


def main() -> int:
    problems: list[str] = []
    for relative in FORBIDDEN_FILES:
        path = REPO / relative
        if path.exists():
            problems.append(f"forbidden legacy file still exists: {relative}")

    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in iter_source_files(root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in text:
                    problems.append(
                        f"forbidden legacy reference {pattern!r} in "
                        f"{path.relative_to(REPO)}"
                    )

    if problems:
        print("\n".join(problems))
        return 1
    print("No legacy frontend mock/Agent adapters found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
