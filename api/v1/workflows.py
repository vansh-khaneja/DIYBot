"""
Workflows API - Minimal SQLite persistence (no Alembic)
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/workflows", tags=["workflows"])


# Database setup
DB_DIR = Path(__file__).resolve().parents[3] / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "workflows.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


init_db()


class WorkflowIn(BaseModel):
    name: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(..., description="Workflow graph JSON")


@router.get("/", response_model=Dict[str, Any])
async def list_workflows():
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at FROM workflows ORDER BY id DESC"
            ).fetchall()
        items = [dict(r) for r in rows]
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {e}")


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(workflow_id: int):
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, name, data_json, created_at FROM workflows WHERE id = ?",
                (workflow_id,),
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
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO workflows (name, data_json) VALUES (?, ?)",
                (payload.name, json.dumps(payload.data)),
            )
            conn.commit()
            new_id = cur.lastrowid
        return {"success": True, "data": {"id": new_id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save workflow: {e}")


