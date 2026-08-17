# AGENTS.md — Coding Agent Contract for RUI

When working on this repository as a coding agent:

1. **Never disable or bypass** constitutional invariants, budget enforcement, or kill switches.
2. Prefer changes that improve cost efficiency, reliability, or governance visibility.
3. Keep the verification suite (`tests/`, `tests/e2e/`) green.
4. Follow the package layout under `src/rui/`.
5. Document any new Phase-4 self-improvement capability with an explicit gate and audit trail.
6. Match the professional scaffolding style of the related [server-os](https://github.com/ANAMIZED/server-os) repository.

## Surfaces you must keep working

| Surface | Entry |
|---------|-------|
| CLI | `rui` (`src/rui/cli.py`) |
| REST API | `rui-api` / `rui serve` (`src/rui/api/`) |
| MCP Server | `rui-mcp` (`src/rui/mcp/server.py`) |
| Python SDK | `from rui.sdk import RUIClient` |
| Multi-agent workflows | `rui.workflows` + `skills/multi-agent-workflow/` |
| Live console | `rui-1.html` |

Any change that breaks import of these surfaces or the CI "Import surfaces" / "CLI smoke" steps is a regression.

Fail closed. Prefer reversible, versioned changes.
