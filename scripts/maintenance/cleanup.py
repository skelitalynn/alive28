#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlmodel import Session

from backend.app.database import engine, init_db
from backend.app.services.cleanup import cleanup_ephemeral_records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove expired Alive28 authentication and recovery records."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report candidates without deleting records.",
    )
    args = parser.parse_args()

    init_db()
    with Session(engine) as session:
        result = cleanup_ephemeral_records(session, dry_run=args.dry_run)
    print(json.dumps(result.model_dump(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
