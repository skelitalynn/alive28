#!/usr/bin/env python3
"""Validate the repository documentation route without third-party packages."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / ".harness" / "config.json"
ROOT_README = REPO / "README.md"
DOCS_INDEX = REPO / "docs" / "README.md"
LEGACY_DOCS = (
    REPO / "docs" / "startup.md",
    REPO / "docs" / "issue_report.md",
)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def local_links(path: Path) -> list[Path]:
    targets: list[Path] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        targets.append((path.parent / target).resolve())
    return targets


def main() -> int:
    failures: list[str] = []
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {CONFIG_PATH.relative_to(REPO)}: {exc}")
        return 1

    documents = config.get("documents", {})
    for role, relative in documents.items():
        path = REPO / str(relative)
        if not path.is_file():
            failures.append(f"missing configured document ({role}): {relative}")

    required_index_targets = {
        (REPO / "docs" / name).resolve()
        for name in (
            "PRODUCT.md",
            "ARCHITECTURE.md",
            "DEVELOPMENT.md",
            "testing.md",
            "PROGRESS.md",
            "DECISIONS.md",
            "FEATURES.json",
        )
    }
    index_targets = set(local_links(DOCS_INDEX)) if DOCS_INDEX.is_file() else set()
    for target in sorted(required_index_targets - index_targets):
        failures.append(f"docs/README.md does not route to {target.relative_to(REPO)}")

    if DOCS_INDEX.resolve() not in set(local_links(ROOT_README)):
        failures.append("README.md does not route to docs/README.md")

    for markdown in (ROOT_README, DOCS_INDEX):
        if not markdown.is_file():
            failures.append(f"missing document: {markdown.relative_to(REPO)}")
            continue
        for target in local_links(markdown):
            if not target.exists():
                failures.append(
                    f"broken local link in {markdown.relative_to(REPO)}: "
                    f"{target.relative_to(REPO)}"
                )

    for legacy in LEGACY_DOCS:
        if legacy.exists():
            failures.append(f"legacy duplicate document still exists: {legacy.relative_to(REPO)}")

    if failures:
        print("Documentation check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Documentation route is complete and contains no legacy duplicates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
