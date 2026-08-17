# Recursive UltraIntelligence (RUI)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Autonomous Agentic Operating System**

RUI is a recursive, cost-aware, governed agentic operating system. It implements:

- **Recursive Agent Harnesses (RAH)** — full harness recursion (tools + FS + planning + context) as the recursive unit
- **Recursive Agent Optimization (RAO)** — learned / heuristic policy for when and how to spawn & delegate across a call tree
- **Interactive Agents Call Tree (IACT)** — the runtime fabric, security boundary, cost accounting tree and observability spine
- **Outer / Inner Meta-Loops** — AIDE²-style bilevel autoresearch for controlled self-improvement of the full stack
- **Cost Kernel** — first-class token/dollar budgets, propagation, circuit breakers, hierarchical attribution, model-tier routing
- **Governance Kernel** — hierarchical Non-Human Identity (NHI), policy inheritance, cascading kill switches, multi-objective promotion gates, frozen constitutional invariants

Fail-closed. Verified end-to-end under simulation.

A senior engineer who has never seen this repository can, using **only** the source code and this `README.md`:

1. Install and run the verification suite
2. Exercise the recursive runtime, cost controls and governance
3. Inspect the Phase coverage and gap analysis

**[Support Public Goods](https://donate.stripe.com/00w5kE3wOg5L8Jn2F243S00)** · **[Support Agentic OS Kernels ($99)](https://buy.stripe.com/bJecN63wObPv6Bf7Zm43S02)**

### Non-custodial USDC (preferred for agents)

| Network | Address | Explorer |
|---------|---------|----------|
| **Base** | `0xD3d0E9eDAe3Ac7bb199a8EAA761BdA423b878438` | [basescan](https://basescan.org/address/0xD3d0E9eDAe3Ac7bb199a8EAA761BdA423b878438) |
| **Ethereum** | `0xD3d0E9eDAe3Ac7bb199a8EAA761BdA423b878438` | [etherscan](https://etherscan.io/address/0xD3d0E9eDAe3Ac7bb199a8EAA761BdA423b878438) |
| **Solana** | `ETQwWf19axArsY493UfC6bxe2BmEzmzvCb58PPnC38A` | [solscan](https://solscan.io/account/ETQwWf19axArsY493UfC6bxe2BmEzmzvCb58PPnC38A) |

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
python tests/e2e/test_rui_e2e.py
```

## Architecture (matching Server OS layout)

```
src/rui/
├── core/models.py          # Shared dataclasses + CONSTITUTIONAL_INVARIANTS
├── cost/kernel.py          # Budget, recording, routing, circuit breakers
├── governance/kernel.py    # NHI, policy, kill, audit, PromotionProtocol
├── runtime/iact.py         # Interactive Agents Call Tree
├── runtime/rah.py          # Recursive Agent Harness
├── meta/self_harness.py    # SelfHarness + OuterMetaLoop
└── __init__.py             # Top-level RUI integration
```

## Phase Coverage

| Phase | Contents | Status |
|-------|----------|--------|
| 1 | IACT + RAH + CostKernel + Governance + NHI + budgets + kill + audit | ✅ Verified |
| 2 | RAO-style recursion decisions + Self-Harness | ✅ Verified |
| 3 | Outer meta-loops + multi-obj gated promotion | ✅ Verified |
| 4 | Full-stack gated RSI concepts + constitutional invariants | ✅ Verified |

See `docs/RUI_BUILD_VERIFICATION_REPORT.md` for the full audit, test evidence and explicit production gap analysis.

## Design Principles

1. Cost is a first-class resource (budgets propagate; circuit breakers fire)
2. Least privilege by construction (hierarchical NHI + policy inheritance)
3. Observable by default (Call Tree is the trace)
4. Fail closed (unauthorized spawn denied, invariants frozen)
5. Recursion is learned / gated, never free

## Relationship to Server OS

RUI extends the Server OS concept with explicit **harness recursion**, **RAO**, **outer/inner meta-loops** and **open-ended but constitutionally bounded self-improvement** of the agent stack itself. Layout and professional scaffolding deliberately mirror [server-os](https://github.com/ANAMIZED/server-os).

## License

Apache-2.0
