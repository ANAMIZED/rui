# Skill: Multi-Agent Workflow (RUI)

## Purpose
Run sequential specialist agents (planner → worker → critic, or custom roles) under a shared recursive call tree, budget, and governance kernel.

## When to use
- Decompose a complex goal into role-specialized sub-agents
- Keep all work inside the IACT (Interactive Agents Call Tree)
- Enforce hierarchical budgets, kill switches, and constitutional invariants

## Interfaces

### CLI
```bash
rui workflow run --goal "Analyze funding-rate opportunities" --agents planner,researcher,critic
```

### Python SDK
```python
from rui.sdk import RUIClient
with RUIClient() as c:
    result = c.workflow(goal="...", agents=["planner", "worker", "critic"])
```

### MCP
Tool: `run_multi_agent(goal, agents?, budget_tokens?)`

### REST
`POST /v1/workflows` with body `{ "goal": "...", "agents": [...], "budget_tokens": 30000 }`

## Guarantees
- Fail-closed: spawn denied if budget, policy, or kill switch blocks it
- Every agent is a first-class CallTreeNode with NHI + audit entry
- Constitution remains verified after the workflow
