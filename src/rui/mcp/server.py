"""RUI as an MCP Server.

Exposes Recursive UltraIntelligence primitives as MCP tools so any
MCP-compatible client can spawn recursive call trees, enforce budgets,
trip kill switches, inspect audit/constitution, and run multi-agent workflows.
"""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from rui import RUI, __version__
from rui.workflows.multi_agent import run_multi_agent_workflow

_rui = RUI()

mcp = MCPServer(
    "RUI",
    instructions=(
        "You are connected to RUI (Recursive UltraIntelligence), an Autonomous Agentic Operating System. "
        "Use the tools to start recursive call trees, spawn children under budget & policy, "
        "inspect the constitution and audit trail, trip hierarchical kill switches, "
        "and orchestrate multi-agent workflows. Always prefer explicit budgets and fail-closed governance."
    ),
)


@mcp.tool()
def rui_status() -> dict[str, Any]:
    """Return RUI version, constitution status, and call-tree summary."""
    inv = _rui.verify_constitution()
    return {
        "version": __version__,
        "constitution_ok": all(inv.values()),
        "invariants": inv,
        "tree": _rui.tree_summary(),
        "owner": _rui.owner,
    }


@mcp.tool()
def start_root_task(task: str, tokens: int = 60000) -> dict[str, Any]:
    """Create a root call-tree node and execute it (simulated work under budget)."""
    root = _rui.start_task(task)
    if not root:
        return {"error": "failed to create root"}
    result = _rui.iact.execute_node(root.id, simulate_tokens=min(2000, tokens // 4))
    return {
        "node_id": root.id,
        "status": root.status.value if hasattr(root.status, "value") else str(root.status),
        "result": result,
    }


@mcp.tool()
def spawn_child(parent_id: str, task: str) -> dict[str, Any]:
    """Spawn a child node under a parent (budget + policy + kill enforced)."""
    child = _rui.iact.spawn_child(parent_id, task)
    if not child:
        return {"error": "spawn denied (budget / policy / kill)"}
    result = _rui.iact.execute_node(child.id)
    return {
        "node_id": child.id,
        "depth": child.depth,
        "status": child.status.value if hasattr(child.status, "value") else str(child.status),
        "result": result,
    }


@mcp.tool()
def get_call_tree() -> dict[str, Any]:
    """Return the current Interactive Agents Call Tree summary."""
    return _rui.tree_summary()


@mcp.tool()
def kill_node(node_id: str, reason: str = "mcp") -> dict[str, Any]:
    """Trip hierarchical kill switch on a node and cascade to descendants."""
    killed = _rui.iact.kill_subtree(node_id, reason=reason)
    return {"killed": killed}


@mcp.tool()
def get_audit_log(limit: int = 40) -> list[dict[str, Any]]:
    """Return governance audit records."""
    return _rui.governance.get_audit_trail(limit=limit)


@mcp.tool()
def verify_constitution() -> dict[str, bool]:
    """Verify frozen constitutional invariants."""
    return _rui.verify_constitution()


@mcp.tool()
def run_multi_agent(
    goal: str,
    agents: list[str] | None = None,
    budget_tokens: int = 30000,
) -> dict[str, Any]:
    """Run a sequential multi-agent workflow (planner / worker / critic by default) under shared budget."""
    roles = agents or ["planner", "worker", "critic"]
    return run_multi_agent_workflow(_rui, goal=goal, roles=roles, budget_tokens=budget_tokens)


def main() -> None:
    """Entry point for rui-mcp / stdio MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
