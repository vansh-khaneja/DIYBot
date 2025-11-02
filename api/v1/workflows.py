"""Workflows API supporting both SQLite and Postgres backends."""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import USING_POSTGRES, get_connection, list_columns


router = APIRouter(prefix="/workflows", tags=["workflows"])


def init_db() -> None:
    with get_connection() as conn:
        if USING_POSTGRES:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

            columns = list_columns(conn, "workflows")
            if columns and "id" in columns:
                cursor = conn.execute("PRAGMA table_info(workflows)")
                rows = cursor.fetchall()
                id_type = None
                for row in rows:
                    col_name = row["name"] if isinstance(row, dict) else row[1]
                    if col_name == "id":
                        id_type = row["type"] if isinstance(row, dict) else row[2]
                        break
                if id_type == "INTEGER":
                    conn.execute("BEGIN TRANSACTION")
                    try:
                        conn.execute(
                            """
                            CREATE TABLE IF NOT EXISTS workflows_new (
                                id TEXT PRIMARY KEY,
                                name TEXT NOT NULL,
                                data_json TEXT NOT NULL,
                                created_at TEXT DEFAULT (datetime('now'))
                            )
                            """
                        )
                        old_rows = conn.execute(
                            "SELECT id, name, data_json, created_at FROM workflows"
                        ).fetchall()
                        for row in old_rows:
                            conn.execute(
                                "INSERT INTO workflows_new (id, name, data_json, created_at) VALUES (?, ?, ?, ?)",
                                (str(uuid.uuid4()), row[1], row[2], row[3]),
                            )
                        conn.execute("DROP TABLE workflows")
                        conn.execute("ALTER TABLE workflows_new RENAME TO workflows")
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        raise


init_db()


class WorkflowIn(BaseModel):
    name: str = Field(default="", description="Workflow name (auto-generated if empty)")
    data: Dict[str, Any] = Field(..., description="Workflow graph JSON")


def generate_workflow_name(conn) -> str:
    """Generate auto-increment workflow name like 'Untitled 1', 'Untitled 2', etc."""

    rows = conn.execute(
        "SELECT name FROM workflows WHERE name LIKE 'Untitled %' ORDER BY name"
    ).fetchall()

    existing_numbers: List[int] = []
    for row in rows:
        name = row["name"] if isinstance(row, dict) else row[0]
        if name.startswith("Untitled "):
            try:
                existing_numbers.append(int(name.replace("Untitled ", "")))
            except ValueError:
                continue

    next_num = 1
    while next_num in existing_numbers:
        next_num += 1
    return f"Untitled {next_num}"


@router.get("/", response_model=Dict[str, Any])
async def list_workflows():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at FROM workflows ORDER BY created_at DESC"
            ).fetchall()
        items = [dict(r) for r in rows]
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {e}")


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(workflow_id: str):
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, data_json, created_at FROM workflows WHERE id = %s",
                (workflow_id,) if USING_POSTGRES else (workflow_id,),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")
        item = dict(row)
        item["data"] = json.loads(item.pop("data_json"))
        return {"success": True, "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {e}")


@router.post("/", response_model=Dict[str, Any])
async def save_workflow(payload: WorkflowIn):
    try:
        workflow_id = str(uuid.uuid4())
        with get_connection() as conn:
            workflow_name = payload.name.strip() if payload.name else ""
            if not workflow_name:
                workflow_name = generate_workflow_name(conn)

            conn.execute(
                "INSERT INTO workflows (id, name, data_json) VALUES (%s, %s, %s)"
                if USING_POSTGRES
                else "INSERT INTO workflows (id, name, data_json) VALUES (?, ?, ?)",
                (workflow_id, workflow_name, json.dumps(payload.data)),
            )
        return {"success": True, "data": {"id": workflow_id, "name": workflow_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save workflow: {e}")


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.put("/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(workflow_id: str, payload: WorkflowUpdate):
    try:
        with get_connection() as conn:
            update_parts = []
            update_values: List[Any] = []

            if payload.name is not None:
                update_parts.append("name = %s" if USING_POSTGRES else "name = ?")
                update_values.append(payload.name)

            if payload.data is not None:
                update_parts.append("data_json = %s" if USING_POSTGRES else "data_json = ?")
                update_values.append(json.dumps(payload.data))

            if not update_parts:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_values.append(workflow_id)

            query = f"UPDATE workflows SET {', '.join(update_parts)} WHERE id = %s"
            if not USING_POSTGRES:
                query = query.replace("%s", "?")

            cur = conn.execute(query, tuple(update_values))
            if hasattr(cur, "rowcount") and cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Workflow not found")
        return {"success": True, "data": {"id": workflow_id}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {e}")


@router.delete("/{workflow_id}", response_model=Dict[str, Any])
async def delete_workflow(workflow_id: str):
    try:
        with get_connection() as conn:
            query = "DELETE FROM workflows WHERE id = %s"
            if not USING_POSTGRES:
                query = query.replace("%s", "?")
            cur = conn.execute(query, (workflow_id,))
            if hasattr(cur, "rowcount") and cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Workflow not found")
        return {"success": True, "data": {"id": workflow_id}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {e}")

