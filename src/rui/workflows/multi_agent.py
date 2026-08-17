"""Sequential multi-agent workflow under shared RUI budget & governance."""

from __future__ import annotations

from typing import Any, List

from rui import RUI


def run_multi_agent_workflow(
    rui: RUI,
    goal: str,
    roles: List[str] | None = None,
    budget_tokens: int = 30000,
) -> dict[str, Any]:
    """
    Run a sequential multi-agent workflow.

    Creates a root for the overall goal, then spawns one child per role
    (planner → worker → critic by default). Each child inherits budget
    and policy; kill switches and circuit breakers remain active.
    """
    roles = roles or ["planner", "worker", "critic"]
    root = rui.start_task(f"[workflow] {goal}")
    if not root:
        return {"error": "failed to create workflow root", "goal": goal}

    # Mild root execution so the tree is live
    rui.iact.execute_node(root.id, simulate_tokens=min(800, budget_tokens // 10))

    results: list[dict[str, Any]] = []
    for role in roles:
        child = rui.iact.spawn_child(
            root.id,
            f"[{role}] Contribute to goal: {goal}",
            scale=0.25,
        )
        if not child:
            results.append({"role": role, "status": "denied", "error": "spawn denied"})
            continue
        out = rui.iact.execute_node(
            child.id,
            simulate_tokens=min(1500, budget_tokens // max(len(roles), 1)),
        )
        results.append({
            "role": role,
            "node_id": child.id,
            "depth": child.depth,
            "status": child.status.value if hasattr(child.status, "value") else str(child.status),
            "result": out,
        })

    return {
        "goal": goal,
        "root_id": root.id,
        "roles": roles,
        "results": results,
        "tree": rui.tree_summary(),
        "constitution_ok": all(rui.verify_constitution().values()),
    }
