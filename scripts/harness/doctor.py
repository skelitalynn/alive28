#!/usr/bin/env python3
"""Inspect or execute the validation chain configured by harness-adopter."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_repo() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[2]]:
        if (candidate / ".harness" / "config.json").exists():
            return candidate
    raise SystemExit("ERROR: .harness/config.json not found. Run from the repository or install Harness first.")


def load_config(repo: Path) -> dict[str, Any]:
    try:
        return json.loads((repo / ".harness" / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: Unable to read .harness/config.json: {exc}") from exc


def run_command(command: str, repo: Path) -> int:
    print(f"\n$ {command}", flush=True)
    completed = subprocess.run(command, shell=True, cwd=repo, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Harness routing and optionally run configured verification commands.")
    parser.add_argument("--run", action="store_true", help="Execute commands.check after structural checks.")
    parser.add_argument("--setup", action="store_true", help="Run commands.setup before commands.check.")
    args = parser.parse_args()

    repo = find_repo()
    config = load_config(repo)
    documents = config.get("documents", {})
    commands = config.get("commands", {})
    failures: list[str] = []

    print(f"Repository: {repo}")
    print("Documentation routes:")
    for role, relative in documents.items():
        path = repo / str(relative)
        status = "OK" if path.exists() else "MISSING"
        print(f"  {role:12} {relative} [{status}]")
        if not path.exists():
            failures.append(f"Missing document: {relative}")

    features_path = repo / str(documents.get("features", "docs/FEATURES.json"))
    if features_path.exists():
        try:
            payload = json.loads(features_path.read_text(encoding="utf-8"))
            active = [f.get("id") for f in payload.get("features", []) if f.get("state") == "active"]
            if len(active) > int(config.get("rules", {}).get("wip_limit", 1)):
                failures.append(f"WIP limit violated: active tasks are {active}")
            print(f"Active tasks: {active or 'none'}")
        except json.JSONDecodeError as exc:
            failures.append(f"Invalid features JSON: {exc}")

    print("Configured commands:")
    for name in ("setup", "dev"):
        if commands.get(name):
            print(f"  {name:12} {commands[name]}")
    check_commands = commands.get("check", [])
    for index, command in enumerate(check_commands, start=1):
        print(f"  check[{index}]     {command}")
    if not check_commands:
        failures.append("No commands.check configured; fill in .harness/config.json from actual project tooling.")

    if failures:
        print("\nStructural findings:")
        for failure in failures:
            print(f"- {failure}")
        if not args.run:
            return 1

    if args.setup:
        setup = commands.get("setup")
        if not setup:
            print("ERROR: --setup requested but commands.setup is not configured.")
            return 1
        if run_command(str(setup), repo) != 0:
            print("ERROR: Setup command failed. Fix the environment or update commands.setup before validating.")
            return 1

    if args.run:
        if not check_commands:
            print("ERROR: No verification commands configured.")
            return 1
        for command in check_commands:
            if run_command(str(command), repo) != 0:
                print(f"ERROR: Verification failed while running: {command}")
                return 1
        print("\nVerification chain passed.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
