#!/usr/bin/env python3
"""Manage WIP=1 feature state and verification evidence for an adopted Harness."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

VALID_STATES = {"not_started", "active", "blocked", "passing"}


def find_repo() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[2]]:
        if (candidate / ".harness" / "config.json").exists():
            return candidate
    raise SystemExit("ERROR: .harness/config.json not found. Run from the repository or install Harness first.")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: Unable to read {path}: {exc}") from exc


def save_json(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def paths(repo: Path) -> tuple[Path, Path]:
    config_path = repo / ".harness" / "config.json"
    config = load_json(config_path)
    features = repo / config.get("documents", {}).get("features", "docs/FEATURES.json")
    evidence = repo / config.get("rules", {}).get("evidence_directory", ".harness/evidence")
    return features, evidence


def get_feature(payload: dict[str, Any], feature_id: str) -> dict[str, Any]:
    for feature in payload.get("features", []):
        if feature.get("id") == feature_id:
            return feature
    raise SystemExit(f"ERROR: Unknown feature id {feature_id!r}.")


def active_features(payload: dict[str, Any]) -> list[str]:
    return [str(feature.get("id")) for feature in payload.get("features", []) if feature.get("state") == "active"]


def git_metadata(repo: Path) -> dict[str, Any]:
    def command(*args: str) -> str | None:
        result = subprocess.run(args, cwd=repo, capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    head = command("git", "rev-parse", "--short", "HEAD")
    status = command("git", "status", "--porcelain")
    return {"git_head": head, "working_tree_dirty": bool(status) if status is not None else None}


def cmd_list(payload: dict[str, Any]) -> int:
    if not payload.get("features"):
        print("No feature items defined.")
        return 0
    for feature in payload["features"]:
        print(f"{feature['id']:12} {feature['state']:12} {feature['behavior']}")
    return 0


def cmd_add(args: argparse.Namespace, payload: dict[str, Any], features_path: Path) -> int:
    if any(feature.get("id") == args.id for feature in payload.get("features", [])):
        print(f"ERROR: Feature {args.id} already exists.")
        return 1
    if not args.verify:
        print("ERROR: At least one --verify command is required; a feature cannot complete without evidence.")
        return 1
    payload.setdefault("features", []).append({
        "id": args.id,
        "behavior": args.behavior,
        "state": "not_started",
        "verification": args.verify,
        "evidence": None,
        "blocked_reason": None,
    })
    save_json(features_path, payload)
    print(f"Added {args.id}: {args.behavior}")
    return 0


def cmd_start(args: argparse.Namespace, payload: dict[str, Any], features_path: Path) -> int:
    feature = get_feature(payload, args.id)
    active = [item for item in active_features(payload) if item != args.id]
    if active:
        print(f"ERROR: WIP=1 enforced. Finish or block active task(s) first: {', '.join(active)}")
        return 1
    if feature.get("state") == "passing":
        print(f"ERROR: {args.id} is already passing; create a new feature for additional behavior.")
        return 1
    feature["state"] = "active"
    feature["blocked_reason"] = None
    save_json(features_path, payload)
    print(f"Activated {args.id}.")
    return 0


def cmd_block(args: argparse.Namespace, payload: dict[str, Any], features_path: Path) -> int:
    feature = get_feature(payload, args.id)
    if feature.get("state") != "active":
        print(f"ERROR: Only an active feature can be blocked; {args.id} is {feature.get('state')}.")
        return 1
    feature["state"] = "blocked"
    feature["blocked_reason"] = args.reason
    save_json(features_path, payload)
    print(f"Blocked {args.id}: {args.reason}")
    return 0


def cmd_verify(args: argparse.Namespace, repo: Path, payload: dict[str, Any], features_path: Path, evidence_root: Path) -> int:
    feature = get_feature(payload, args.id)
    if feature.get("state") != "active":
        print(f"ERROR: Only an active feature can be verified; {args.id} is {feature.get('state')}.")
        return 1
    commands = feature.get("verification", [])
    if not commands:
        print("ERROR: No verification commands configured for this feature.")
        return 1
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = evidence_root / args.id / timestamp
    evidence_dir.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    passed = True
    for index, command in enumerate(commands, start=1):
        print(f"$ {command}", flush=True)
        completed = subprocess.run(str(command), shell=True, cwd=repo, text=True, capture_output=True, check=False)
        log_path = evidence_dir / f"command-{index:02d}.log"
        log_path.write_text(
            f"$ {command}\n\nSTDOUT\n{completed.stdout}\n\nSTDERR\n{completed.stderr}\n",
            encoding="utf-8",
        )
        results.append({"command": command, "returncode": completed.returncode, "log": str(log_path.relative_to(repo))})
        if completed.returncode != 0:
            passed = False
            break
    result = {
        "feature_id": args.id,
        "verified_at": timestamp,
        "passed": passed,
        "commands": results,
        **git_metadata(repo),
    }
    result_path = evidence_dir / "result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    feature["evidence"] = str(result_path.relative_to(repo))
    if passed:
        feature["state"] = "passing"
        feature["blocked_reason"] = None
        print(f"Verification passed; {args.id} is now passing. Evidence: {result_path.relative_to(repo)}")
    else:
        print(f"Verification failed; {args.id} remains active. Evidence: {result_path.relative_to(repo)}")
    save_json(features_path, payload)
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Harness feature tasks and evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    add = sub.add_parser("add")
    add.add_argument("--id", required=True)
    add.add_argument("--behavior", required=True)
    add.add_argument("--verify", action="append", default=[], help="Repeat for each verification command.")
    start = sub.add_parser("start")
    start.add_argument("id")
    block = sub.add_parser("block")
    block.add_argument("id")
    block.add_argument("--reason", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("id")
    args = parser.parse_args()

    repo = find_repo()
    features_path, evidence_root = paths(repo)
    payload = load_json(features_path)
    invalid = [f.get("state") for f in payload.get("features", []) if f.get("state") not in VALID_STATES]
    if invalid:
        print(f"ERROR: Invalid feature states found: {invalid}")
        return 1
    if args.command == "list":
        return cmd_list(payload)
    if args.command == "add":
        return cmd_add(args, payload, features_path)
    if args.command == "start":
        return cmd_start(args, payload, features_path)
    if args.command == "block":
        return cmd_block(args, payload, features_path)
    if args.command == "verify":
        return cmd_verify(args, repo, payload, features_path, evidence_root)
    return 1


if __name__ == "__main__":
    sys.exit(main())
