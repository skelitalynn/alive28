import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks.json"


def load_tasks() -> list:
    # Use utf-8-sig to tolerate BOM from Windows editors
    with open(DATA_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def get_task_by_day_index(day_index: int) -> dict:
    tasks = load_tasks()
    if day_index < 1 or day_index > len(tasks):
        raise ValueError("dayIndex must be between 1 and 28")
    return tasks[day_index - 1]
