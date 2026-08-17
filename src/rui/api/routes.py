"""RUI REST routes — thin HTTP surface over the kernels."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rui import RUI
from rui.workflows.multi_agent import run_multi_agent_workflow

router = APIRouter(prefix="/v1")

# Process-global instance (single-process demo / production can inject)
_rui = RUI()


class TaskCreate(BaseModel):
    task: str
    tokens: int = 60000


class SpawnRequest(BaseModel):
    parent_id: str
    task: str


class KillRequest(BaseModel):
    reason: str = "api"


class WorkflowCreate(BaseModel):
    goal: str
    agents: list[str] = Field(default_factory=lambda: ["planner", "worker", "critic"])
    budget_tokens: int = 30000


@router.get("/status")
def status() -> dict[str, Any]:
    inv = _rui.verify_constitution()
    return {
        "constitution_ok": all(inv.values()),
        "invariants": inv,
        "tree": _rui.tree_summary(),
        "owner": _rui.owner,
    }


@router.post("/tree/start")
def tree_start(body: TaskCreate) -> dict[str, Any]:
    root = _rui.start_task(body.task)
    if not root:
        raise HTTPException(500, "failed to create root")
    result = _rui.iact.execute_node(root.id, simulate_tokens=min(2000, body.tokens // 4))
    return {
        "node_id": root.id,
        "status": root.status.value if hasattr(root.status, "value") else str(root.status),
        "result": result,
    }


@router.post("/tree/spawn")
def tree_spawn(body: SpawnRequest) -> dict[str, Any]:
    child = _rui.iact.spawn_child(body.parent_id, body.task)
    if not child:
        raise HTTPException(403, "spawn denied (budget / policy / kill)")
    result = _rui.iact.execute_node(child.id)
    return {
        "node_id": child.id,
        "depth": child.depth,
        "status": child.status.value if hasattr(child.status, "value") else str(child.status),
        "result": result,
    }


@router.get("/tree")
def tree_show() -> dict[str, Any]:
    return _rui.tree_summary()


@router.post("/tree/{node_id}/kill")
def tree_kill(node_id: str, body: KillRequest) -> dict[str, Any]:
    killed = _rui.iact.kill_subtree(node_id, reason=body.reason)
    return {"killed": killed}


@router.get("/audit")
def audit(limit: int = 50) -> list[dict[str, Any]]:
    return _rui.governance.get_audit_trail(limit=limit)


@router.get("/constitution")
def constitution() -> dict[str, bool]:
    return _rui.verify_constitution()


@router.post("/workflows")
def create_workflow(body: WorkflowCreate) -> dict[str, Any]:
    return run_multi_agent_workflow(
        _rui,
        goal=body.goal,
        roles=body.agents,
        budget_tokens=body.budget_tokens,
    )
