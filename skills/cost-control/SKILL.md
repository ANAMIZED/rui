# Skill: Cost Control (RUI)

## Purpose
Treat tokens and dollars as first-class resources with hierarchical budgets, circuit breakers, and metering.

## Key objects
- `Budget` on every CallTreeNode
- `CostKernel.record` / `check_circuit_breaker` / `allocate_child_budget`
- x402-style receipts (simulation in the live console)

## Operator tips
- Prefer smaller child allocations (`scale=0.25–0.35`)
- Trip kill switches early on cost spikes
- Use the frozen holdout + multi-objective gate before promoting cost-related prompt/routing changes
