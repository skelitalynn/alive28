#!/usr/bin/env python3
"""Run exit checks and write a session handoff artifact."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


def find_repo() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[2]]:
        if (candidate / ".harness" / "config.json").exists():
            return candidate
    raise SystemExit("ERROR: .harness/config.json not found.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository state and generate a Harness session report.")
    parser.add_argument("--allow-active", action="store_true", help="Write a handoff for an unfinished active feature without failing solely for WIP.")
    parser.add_argument("--skip-check", action="store_true", help="Write report without executing configured verification; records this omission.")
    args = parser.parse_args()
    repo = find_repo()
    config = json.loads((repo / ".harness" / "config.json").read_text(encoding="utf-8"))
    features_path = repo / config["documents"]["features"]
    features = json.loads(features_path.read_text(encoding="utf-8"))
    active = [feature["id"] for feature in features.get("features", []) if feature.get("state") == "active"]

    verification_rc = 0
    if not args.skip_check:
        verification_rc = subprocess.run([sys.executable, str(repo / "scripts" / "harness" / "doctor.py"), "--run"], cwd=repo, check=False).returncode

    git = subprocess.run(["git", "status", "--short"], cwd=repo, text=True, capture_output=True, check=False)
    git_status = git.stdout.strip() if git.returncode == 0 else "git status unavailable"
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_dir = repo / config.get("rules", {}).get("session_directory", ".harness/session")
    session_dir.mkdir(parents=True, exist_ok=True)
    report = session_dir / f"{timestamp}.md"
    report.write_text(
        "# Harness Session Handoff\n\n"
        f"- Timestamp (UTC): `{timestamp}`\n"
        f"- Verification: `{'skipped' if args.skip_check else ('passed' if verification_rc == 0 else 'failed')}`\n"
        f"- Active features: `{', '.join(active) if active else 'none'}`\n\n"
        "## Git status\n\n"
        f"```text\n{git_status or 'clean'}\n```\n",
        encoding="utf-8",
    )
    print(f"Session handoff written to {report.relative_to(repo)}")
    if verification_rc != 0:
        print("ERROR: Exit verification failed; session is not in a verified clean state.")
        return 1
    if active and not args.allow_active:
        print(f"ERROR: Active feature(s) remain: {', '.join(active)}. Finish, block, or use --allow-active for an explicit handoff.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
