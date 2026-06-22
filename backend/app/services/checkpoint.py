from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select
from spoon_ai.graph.types import StateSnapshot

from ..models import GraphCheckpoint


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
            if key != "db"
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class SQLiteGraphCheckpointer:
    """Persistent adapter for SpoonOS StateGraph's checkpoint interface."""

    def __init__(self, bind: Any, max_checkpoints_per_thread: int = 50):
        self.bind = bind
        self.max_checkpoints_per_thread = max_checkpoints_per_thread

    def save_checkpoint(self, thread_id: str, snapshot: StateSnapshot) -> None:
        if not thread_id:
            raise ValueError("thread_id is required")

        metadata = _json_safe(snapshot.metadata or {})
        checkpoint_id = metadata.get("checkpoint_id") or str(uuid.uuid4())
        metadata["checkpoint_id"] = checkpoint_id
        row = GraphCheckpoint(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state_values=_json_safe(snapshot.values),
            next_nodes=list(snapshot.next),
            config_data=_json_safe(snapshot.config or {}),
            checkpoint_metadata=metadata,
            created_at=snapshot.created_at,
        )
        with Session(self.bind) as session:
            session.add(row)
            session.commit()
            rows = session.exec(
                select(GraphCheckpoint)
                .where(GraphCheckpoint.thread_id == thread_id)
                .order_by(GraphCheckpoint.id.desc())
            ).all()
            for stale in rows[self.max_checkpoints_per_thread :]:
                session.delete(stale)
            if len(rows) > self.max_checkpoints_per_thread:
                session.commit()

    def get_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str | None = None,
    ) -> StateSnapshot | None:
        with Session(self.bind) as session:
            statement = select(GraphCheckpoint).where(
                GraphCheckpoint.thread_id == thread_id
            )
            if checkpoint_id:
                statement = statement.where(
                    GraphCheckpoint.checkpoint_id == checkpoint_id
                )
            else:
                statement = statement.order_by(GraphCheckpoint.id.desc())
            row = session.exec(statement).first()
            return self._to_snapshot(row) if row else None

    def list_checkpoints(self, thread_id: str) -> list[StateSnapshot]:
        with Session(self.bind) as session:
            rows = session.exec(
                select(GraphCheckpoint)
                .where(GraphCheckpoint.thread_id == thread_id)
                .order_by(GraphCheckpoint.id)
            ).all()
            return [self._to_snapshot(row) for row in rows]

    def clear_thread(self, thread_id: str) -> None:
        with Session(self.bind) as session:
            rows = session.exec(
                select(GraphCheckpoint).where(
                    GraphCheckpoint.thread_id == thread_id
                )
            ).all()
            for row in rows:
                session.delete(row)
            session.commit()

    @staticmethod
    def _to_snapshot(row: GraphCheckpoint) -> StateSnapshot:
        return StateSnapshot(
            values=json.loads(json.dumps(row.state_values)),
            next=tuple(row.next_nodes),
            config=json.loads(json.dumps(row.config_data)),
            metadata=json.loads(json.dumps(row.checkpoint_metadata)),
            created_at=row.created_at,
        )
