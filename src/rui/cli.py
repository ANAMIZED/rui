"""RUI CLI — operator surface for humans and scripts."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table
from rich.panel import Panel

from rui import __version__, RUI

app = typer.Typer(
    name="rui",
    help="RUI — Recursive UltraIntelligence Autonomous Agentic OS CLI",
    no_args_is_help=True,
)
tree_app = typer.Typer(help="Call-tree / IACT operations")
app.add_typer(tree_app, name="tree")
gov_app = typer.Typer(help="Governance & constitution")
app.add_typer(gov_app, name="gov")
workflow_app = typer.Typer(help="Multi-agent workflows")
app.add_typer(workflow_app, name="workflow")

# Shared in-process instance for local CLI use
_rui: Optional[RUI] = None


def _get() -> RUI:
    global _rui
    if _rui is None:
        _rui = RUI()
    return _rui


@app.command()
def version():
    """Print RUI version."""
    rprint(f"[bold]RUI[/bold] {__version__}")


@app.command()
def status():
    """Show runtime status and constitution check."""
    r = _get()
    inv = r.verify_constitution()
    ok = all(inv.values())
    summary = r.tree_summary()
    rprint(Panel.fit(
        f"[green]OK[/green]  constitution={'verified' if ok else 'BROKEN'}\n"
        f"nodes={summary.get('total_nodes', 0)}  root={summary.get('root_id') or '—'}\n"
        f"owner={r.owner}",
        title="RUI Status",
    ))
    table = Table(title="Constitutional Invariants")
    table.add_column("Invariant")
    table.add_column("Status")
    for k, v in inv.items():
        table.add_row(k, "[green]✓[/green]" if v else "[red]✗[/red]")
    rprint(table)


@tree_app.command("start")
def tree_start(
    task: str = typer.Argument(..., help="Root task description"),
    tokens: int = typer.Option(60000, "--tokens", "-t"),
):
    """Spawn a root node and run a simple execute cycle."""
    r = _get()
    root = r.start_task(task)
    if not root:
        rprint("[red]Failed to create root[/red]")
        raise typer.Exit(1)
    # Execute with simulated work
    result = r.iact.execute_node(root.id, simulate_tokens=min(2000, tokens // 4))
    rprint(f"[green]Root[/green] {root.id}")
    rprint(f"Status: {root.status.value if hasattr(root.status, 'value') else root.status}")
    rprint(f"Result: {result}")


@tree_app.command("spawn")
def tree_spawn(
    parent_id: str = typer.Argument(...),
    task: str = typer.Argument(...),
):
    """Spawn a child under an existing node."""
    r = _get()
    child = r.iact.spawn_child(parent_id, task)
    if not child:
        rprint("[red]Spawn denied (budget / policy / kill)[/red]")
        raise typer.Exit(1)
    r.iact.execute_node(child.id)
    rprint(f"[green]Child[/green] {child.id}  depth={child.depth}")


@tree_app.command("show")
def tree_show():
    """Print current call-tree summary."""
    r = _get()
    summary = r.tree_summary()
    rprint(json.dumps(summary, indent=2, default=str))


@tree_app.command("kill")
def tree_kill(
    node_id: str = typer.Argument(...),
    reason: str = typer.Option("operator", "--reason", "-r"),
):
    """Trip hierarchical kill switch on a node (and cascade)."""
    r = _get()
    killed = r.iact.kill_subtree(node_id, reason=reason)
    rprint(f"[yellow]Killed[/yellow] {len(killed)} node(s): {killed}")


@gov_app.command("audit")
def gov_audit(limit: int = typer.Option(20, "--limit", "-n")):
    """Show recent governance audit trail."""
    r = _get()
    events = r.governance.get_audit_trail(limit=limit)
    rprint(json.dumps(events, indent=2, default=str))


@gov_app.command("constitution")
def gov_constitution():
    """Verify frozen constitutional invariants."""
    r = _get()
    inv = r.verify_constitution()
    for k, v in inv.items():
        mark = "[green]PASS[/green]" if v else "[red]FAIL[/red]"
        rprint(f"{mark}  {k}")


@workflow_app.command("run")
def workflow_run(
    goal: str = typer.Option(..., "--goal", "-g"),
    agents: str = typer.Option("planner,worker,critic", "--agents", "-a"),
    budget_tokens: int = typer.Option(30000, "--tokens", "-t"),
):
    """Run a sequential multi-agent workflow under a shared budget."""
    from rui.workflows.multi_agent import run_multi_agent_workflow

    roles = [x.strip() for x in agents.split(",") if x.strip()]
    r = _get()
    result = run_multi_agent_workflow(r, goal=goal, roles=roles, budget_tokens=budget_tokens)
    rprint(json.dumps(result, indent=2, default=str))


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8080, "--port", "-p"),
):
    """Start the RUI REST API (uvicorn)."""
    import uvicorn
    rprint(f"Starting RUI API on http://{host}:{port}")
    uvicorn.run("rui.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
