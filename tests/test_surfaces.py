"""Smoke tests for SDK, API, CLI, MCP, and multi-agent workflow surfaces."""

from __future__ import annotations


def test_version():
    from rui import __version__
    assert __version__
    assert __version__.startswith("0.")


def test_rui_instance():
    from rui import RUI
    r = RUI(owner="test")
    inv = r.verify_constitution()
    assert all(inv.values())
    root = r.start_task("surface smoke")
    assert root is not None
    summary = r.tree_summary()
    assert summary["total_nodes"] >= 1


def test_cli_app_import():
    from rui.cli import app
    assert app is not None


def test_sdk_import():
    from rui.sdk import RUIClient
    assert RUIClient is not None


def test_api_app_import():
    from rui.api.main import app
    assert app is not None
    assert app.title.startswith("RUI")


def test_mcp_import():
    from rui.mcp.server import mcp
    assert mcp is not None


def test_multi_agent_workflow():
    from rui import RUI
    from rui.workflows import run_multi_agent_workflow

    r = RUI(owner="wf_test")
    out = run_multi_agent_workflow(
        r,
        goal="Smoke multi-agent workflow",
        roles=["planner", "worker"],
        budget_tokens=8000,
    )
    assert "root_id" in out
    assert out.get("constitution_ok") is True
    assert len(out.get("results", [])) == 2
