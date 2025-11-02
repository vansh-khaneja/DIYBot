"""
Deployments API - deploy saved workflows as invokable endpoints
"""

from __future__ import annotations

import json
import time
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import USING_POSTGRES, get_connection, list_columns
from api.v1.nodes import execute_flow as run_execute_endpoint


router = APIRouter(prefix="/deployments", tags=["deployments"])


def init_db() -> None:
    with get_connection() as conn:
        if USING_POSTGRES:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    workflow_id TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    workflow_hash TEXT,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployment_logs (
                    id TEXT PRIMARY KEY,
                    deployment_id TEXT NOT NULL,
                    status TEXT,
                    latency_ms DOUBLE PRECISION,
                    request_json TEXT,
                    response_json TEXT,
                    error TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deployment_id) REFERENCES deployments(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_deployment_id
                ON deployment_logs (deployment_id, created_at DESC)
                """
            )
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    workflow_id TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployment_logs (
                    id TEXT PRIMARY KEY,
                    deployment_id TEXT NOT NULL,
                    status TEXT,
                    latency_ms REAL,
                    request_json TEXT,
                    response_json TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (deployment_id) REFERENCES deployments(id)
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_deployment_id
                ON deployment_logs (deployment_id, created_at DESC)
                """
            )

            columns = list_columns(conn, "deployments")
            if "workflow_hash" not in columns:
                conn.execute("ALTER TABLE deployments ADD COLUMN workflow_hash TEXT")
            if "updated_at" not in columns:
                conn.execute(
                    "ALTER TABLE deployments ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))"
                )
            conn.commit()


init_db()


def normalize_timestamp(value: Optional[str | datetime]) -> Optional[str]:
    if not value:
        return value

    # Handle datetime objects (from Postgres) - convert to ISO format with Z
    if isinstance(value, datetime):
        # If already has timezone info, convert to UTC
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        # If naive datetime, assume it's UTC
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    # Handle string values (from SQLite)
    trimmed = value.strip()
    if not trimmed:
        return value

    if trimmed.endswith("Z") or ("+" in trimmed[10:]):
        return trimmed

    candidate = trimmed.replace(" ", "T")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return value

    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def log_deployment_invocation(
    *,
    deployment_id: str,
    status: str,
    request_data: Dict[str, Any],
    response_data: Optional[Any],
    error: Optional[str],
    latency_ms: float,
) -> None:
    log_id = str(uuid.uuid4())

    try:
        request_json = json.dumps(request_data, ensure_ascii=False)
    except (TypeError, ValueError):
        request_json = json.dumps({"raw": str(request_data)}, ensure_ascii=False)

    if response_data is None:
        response_json: Optional[str] = None
    else:
        try:
            response_json = json.dumps(response_data, ensure_ascii=False)
        except (TypeError, ValueError):
            response_json = json.dumps({"raw": str(response_data)}, ensure_ascii=False)

    insert_query = (
        """
        INSERT INTO deployment_logs (
            id, deployment_id, status, latency_ms, request_json, response_json, error
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
    )
    
    # Optimized pruning: only prune occasionally (every 10th call) and use a more efficient query
    # This reduces the overhead of pruning on every single invocation
    import random
    should_prune = random.random() < 0.1  # 10% chance to prune
    
    if USING_POSTGRES:
        # More efficient Postgres pruning using a subquery with OFFSET
        prune_query = (
            """
            DELETE FROM deployment_logs
            WHERE deployment_id = %s
              AND created_at < (
                SELECT created_at FROM deployment_logs
                WHERE deployment_id = %s
                ORDER BY created_at DESC
                OFFSET 50 LIMIT 1
              )
            """
        )
    else:
        # SQLite version
        insert_query = insert_query.replace("%s", "?")
        prune_query = (
            """
            DELETE FROM deployment_logs
            WHERE deployment_id = ?
              AND id NOT IN (
                SELECT id FROM deployment_logs
                WHERE deployment_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 50
              )
            """
        )

    with get_connection() as conn:
        conn.execute(
            insert_query,
            (
                log_id,
                deployment_id,
                status,
                float(latency_ms),
                request_json,
                response_json,
                error,
            ),
        )
        
        # Only prune occasionally to reduce overhead
        if should_prune:
            conn.execute(prune_query, (deployment_id, deployment_id))
        
        if not USING_POSTGRES:
            conn.commit()


class CreateDeploymentIn(BaseModel):
    workflow_id: str
    name: Optional[str] = None


# Map backend node_id to executor class name
NODE_ID_TO_CLASS: Dict[str, str] = {
    "query_node": "QueryNode",
    "language_model_node": "LanguageModelNode",
    "web_search_node": "WebSearchNode",
    "knowledge_base_retrieval_node": "KnowledgeBaseRetrievalNode",
    "intent_classification_node": "IntentClassificationNode",
    "conditional_node": "ConditionalNode",
    "response_node": "ResponseNode",
}


def compile_workflow(saved: Dict[str, Any]) -> Dict[str, Any]:
    """Compile saved React Flow graph into executor format."""
    nodes_cfg: Dict[str, Any] = {}
    for n in saved.get("nodes", []):
        data = n.get("data") or {}
        node_schema = data.get("nodeSchema") or {}
        backend_id = (node_schema.get("node_id") or "").lower()
        node_class = NODE_ID_TO_CLASS.get(backend_id) or backend_id.title().replace("_", "")
        nodes_cfg[n["id"]] = {
            "type": node_class,
            "parameters": data.get("parameters", {}),
        }

    def _norm_handle(val: Optional[str]) -> Optional[str]:
        if not val:
            return val
        v = str(val)
        # strip common prefixes used in frontend handle ids
        for prefix in ("output-", "input-"):
            if v.startswith(prefix):
                return v[len(prefix):]
        return v

    edges_out = []
    for e in saved.get("edges", []):
        edges_out.append(
            {
                "from": {"node": e["source"], "output": _norm_handle(e.get("sourceHandle") or "") or None},
                "to": {"node": e["target"], "input": _norm_handle(e.get("targetHandle") or "") or None},
            }
        )

    return {"nodes": nodes_cfg, "edges": edges_out}


def compute_workflow_hash(data: Dict[str, Any]) -> str:
    """Compute hash of workflow data for change detection"""
    workflow_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(workflow_str.encode()).hexdigest()


@router.post("/", response_model=Dict[str, Any])
async def create_deployment(payload: CreateDeploymentIn):
    with get_connection() as conn:
        wf = conn.execute(
            "SELECT id, name, data_json FROM workflows WHERE id = %s"
            if USING_POSTGRES
            else "SELECT id, name, data_json FROM workflows WHERE id = ?",
            (payload.workflow_id,),
        ).fetchone()
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")

        try:
            data = json.loads(wf["data_json"])  # saved react-flow graph
        except Exception:
            raise HTTPException(status_code=400, detail="Saved workflow data is invalid JSON")

        compiled = compile_workflow(data)
        workflow_hash = compute_workflow_hash(data)

        # Check which columns exist
        available_columns = list_columns(conn, "deployments")
        has_hash = "workflow_hash" in available_columns
        has_updated_at = "updated_at" in available_columns

        # Check if this workflow already has a deployment
        existing = conn.execute(
            "SELECT id FROM deployments WHERE workflow_id = %s LIMIT 1"
            if USING_POSTGRES
            else "SELECT id FROM deployments WHERE workflow_id = ? LIMIT 1",
            (payload.workflow_id,),
        ).fetchone()

        if existing:
            # Update existing deployment
            dep_id = existing["id"]
            
            # Build UPDATE query based on available columns
            placeholder = "%s" if USING_POSTGRES else "?"
            update_parts = [f"name = {placeholder}", f"data_json = {placeholder}"]
            update_values = [payload.name or wf["name"], json.dumps(compiled)]
            
            if has_hash:
                update_parts.append(f"workflow_hash = {placeholder}")
                update_values.append(workflow_hash)
            
            if has_updated_at:
                update_parts.append(
                    "updated_at = CURRENT_TIMESTAMP" if USING_POSTGRES else "updated_at = datetime('now')"
                )
            
            update_values.append(dep_id)  # for WHERE clause
            
            conn.execute(
                (
                    f"UPDATE deployments SET {', '.join(update_parts)} WHERE id = %s"
                    if USING_POSTGRES
                    else f"UPDATE deployments SET {', '.join(update_parts)} WHERE id = ?"
                ),
                tuple(update_values),
            )
            if not USING_POSTGRES:
                conn.commit()
            return {"success": True, "data": {"id": dep_id, "invoke_url": f"/api/v1/deployments/{dep_id}/invoke", "updated": True}}
        else:
            # Create new deployment
            dep_id = str(uuid.uuid4())
            
            # Build INSERT query based on available columns
            insert_cols = ["id", "name", "workflow_id", "data_json"]
            insert_values = [dep_id, payload.name or wf["name"], payload.workflow_id, json.dumps(compiled)]
            
            if has_hash:
                insert_cols.append("workflow_hash")
                insert_values.append(workflow_hash)
            
            placeholders = ", ".join(["%s"] * len(insert_values))
            if not USING_POSTGRES:
                placeholders = placeholders.replace("%s", "?")
            
            conn.execute(
                f"INSERT INTO deployments ({', '.join(insert_cols)}) VALUES ({placeholders})",
                tuple(insert_values),
            )
        if not USING_POSTGRES:
            conn.commit()
        return {"success": True, "data": {"id": dep_id, "invoke_url": f"/api/v1/deployments/{dep_id}/invoke", "updated": False}}


@router.get("/", response_model=Dict[str, Any])
async def list_deployments():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, workflow_id, is_active, created_at FROM deployments ORDER BY created_at DESC"
        ).fetchall()
    data: list[Dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        item["created_at"] = normalize_timestamp(item.get("created_at"))
        data.append(item)
    return {"success": True, "data": data}


@router.get("/{deployment_id}/logs", response_model=Dict[str, Any])
async def get_deployment_logs(deployment_id: str, limit: int = 50, offset: int = 0):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    with get_connection() as conn:
        rows = conn.execute(
            (
                """
                SELECT id, deployment_id, created_at, status, latency_ms, request_json, response_json, error
                FROM deployment_logs
                WHERE deployment_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """
                if USING_POSTGRES
                else """
                SELECT id, deployment_id, created_at, status, latency_ms, request_json, response_json, error
                FROM deployment_logs
                WHERE deployment_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """
            ),
            (deployment_id, limit, offset),
        ).fetchall()

        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM deployment_logs WHERE deployment_id = %s"
            if USING_POSTGRES
            else "SELECT COUNT(*) as cnt FROM deployment_logs WHERE deployment_id = ?",
            (deployment_id,),
        ).fetchone()

    logs: List[Dict[str, Any]] = []
    for row in rows:
        row_dict = dict(row)
        request_obj: Any = None
        response_obj: Any = None

        if row_dict.get("request_json"):
            try:
                request_obj = json.loads(row_dict["request_json"])
            except Exception:
                request_obj = row_dict["request_json"]

        if row_dict.get("response_json"):
            try:
                response_obj = json.loads(row_dict["response_json"])
            except Exception:
                response_obj = row_dict["response_json"]

        logs.append(
            {
                "id": row_dict["id"],
                "deployment_id": row_dict["deployment_id"],
                "created_at": normalize_timestamp(row_dict.get("created_at")),
                "status": row_dict.get("status"),
                "latency_ms": row_dict.get("latency_ms"),
                "request": request_obj,
                "response": response_obj,
                "error": row_dict.get("error"),
            }
        )

    total = total_row["cnt"] if total_row else 0
    return {"success": True, "data": {"logs": logs, "total": total}}


@router.get("/workflow/{workflow_id}", response_model=Dict[str, Any])
async def get_deployment_by_workflow(workflow_id: str):
    """Get deployment status for a specific workflow"""
    with get_connection() as conn:
        available_columns = list_columns(conn, "deployments")
        
        # Build SELECT query based on available columns
        select_cols = ["id", "name", "workflow_id", "is_active", "created_at"]
        if "updated_at" in available_columns:
            select_cols.append("updated_at")
        if "workflow_hash" in available_columns:
            select_cols.append("workflow_hash")
        
        # Get deployment info
        deployment = conn.execute(
            (
                f"SELECT {', '.join(select_cols)} FROM deployments WHERE workflow_id = %s LIMIT 1"
                if USING_POSTGRES
                else f"SELECT {', '.join(select_cols)} FROM deployments WHERE workflow_id = ? LIMIT 1"
            ),
            (workflow_id,),
        ).fetchone()
        
        if not deployment:
            return {"success": True, "data": None}
        
        # Get current workflow data to check if changes exist
        workflow = conn.execute(
            "SELECT data_json FROM workflows WHERE id = %s"
            if USING_POSTGRES
            else "SELECT data_json FROM workflows WHERE id = ?",
            (workflow_id,),
        ).fetchone()
        
        has_changes = False
        # Only check for changes if workflow_hash column exists
        if workflow and "workflow_hash" in available_columns:
            try:
                current_data = json.loads(workflow["data_json"])
                current_hash = compute_workflow_hash(current_data)
                stored_hash = deployment["workflow_hash"] if "workflow_hash" in deployment.keys() else None
                has_changes = stored_hash is None or current_hash != stored_hash
            except:
                # If there's any error, assume there are changes to be safe
                has_changes = True
        elif workflow:
            # If workflow_hash doesn't exist, always assume changes (to trigger update)
            has_changes = True

    result = dict(deployment)
    result["created_at"] = normalize_timestamp(result.get("created_at"))
    if "updated_at" in result:
        result["updated_at"] = normalize_timestamp(result.get("updated_at"))
    result["has_changes"] = has_changes
    return {"success": True, "data": result}


class InvokeIn(BaseModel):
    query: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None


@router.post("/{deployment_id}/invoke", response_model=Dict[str, Any])
async def invoke_deployment(deployment_id: str, payload: InvokeIn):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT data_json, is_active FROM deployments WHERE id = %s"
            if USING_POSTGRES
            else "SELECT data_json, is_active FROM deployments WHERE id = ?",
            (deployment_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if int(row["is_active"]) != 1:
        raise HTTPException(status_code=400, detail="Deployment is inactive")

    try:
        compiled = json.loads(row["data_json"])  # executor-ready structure
    except Exception:
        raise HTTPException(status_code=500, detail="Deployment data is corrupted")

    # Allow top-level 'query' to override QueryNode.parameters.query
    if payload.query is not None and payload.query != "":
        for nid, spec in (compiled.get("nodes") or {}).items():
            if (spec.get("type") or "").lower() == "querynode":
                params = spec.get("parameters") or {}
                params["query"] = payload.query
                spec["parameters"] = params

    # External inputs bag (optional advanced use)
    inputs = payload.inputs or {}

    run_payload = {"nodes": compiled["nodes"], "edges": compiled["edges"], "inputs": inputs}
    request_summary = {"query": payload.query, "inputs": inputs}
    start_time = time.perf_counter()
    status = "success"
    response_data: Optional[Any] = None
    error_text: Optional[str] = None

    try:
        # Delegate to existing executor logic
        result = await run_execute_endpoint(run_payload)
        response_data = result
        return result
    except Exception as exc:
        status = "error"
        error_text = str(exc)
        raise
    finally:
        try:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            log_deployment_invocation(
                deployment_id=deployment_id,
                status=status,
                request_data=request_summary,
                response_data=response_data,
                error=error_text,
                latency_ms=latency_ms,
            )
        except Exception as log_exc:
            print(f"Failed to log deployment invocation: {log_exc}")


@router.patch("/{deployment_id}/toggle", response_model=Dict[str, Any])
async def toggle_deployment(deployment_id: str):
    """Toggle deployment active/inactive status"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT is_active FROM deployments WHERE id = %s"
            if USING_POSTGRES
            else "SELECT is_active FROM deployments WHERE id = ?",
            (deployment_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Toggle is_active: 1 -> 0 or 0 -> 1
        new_status = 1 if int(row["is_active"]) == 0 else 0
        conn.execute(
            "UPDATE deployments SET is_active = %s WHERE id = %s"
            if USING_POSTGRES
            else "UPDATE deployments SET is_active = ? WHERE id = ?",
            (new_status, deployment_id),
        )
        if not USING_POSTGRES:
            conn.commit()
    return {"success": True, "data": {"is_active": new_status}}


@router.patch("/{deployment_id}/status", response_model=Dict[str, Any])
async def update_deployment_status(deployment_id: str, is_active: bool):
    """Set deployment active/inactive status"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM deployments WHERE id = %s"
            if USING_POSTGRES
            else "SELECT id FROM deployments WHERE id = ?",
            (deployment_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        conn.execute(
            "UPDATE deployments SET is_active = %s WHERE id = %s"
            if USING_POSTGRES
            else "UPDATE deployments SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, deployment_id),
        )
        if not USING_POSTGRES:
            conn.commit()
    return {"success": True, "data": {"is_active": 1 if is_active else 0}}


@router.delete("/{deployment_id}", response_model=Dict[str, Any])
async def delete_deployment(deployment_id: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM deployments WHERE id = %s"
            if USING_POSTGRES
            else "DELETE FROM deployments WHERE id = ?",
            (deployment_id,),
        )
        if not USING_POSTGRES:
            conn.commit()
    return {"success": True}


