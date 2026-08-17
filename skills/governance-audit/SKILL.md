# Skill: Governance & Audit (RUI)

## Purpose
Hierarchical Non-Human Identity (NHI), policy inheritance, cascading kill switches, immutable audit trail, and frozen constitutional invariants.

## Surfaces
- CLI: `rui gov constitution` / `rui gov audit`
- API: `GET /v1/constitution` / `GET /v1/audit`
- MCP: `verify_constitution` / `get_audit_log`

## Invariants (must never be silently disabled)
- kill_switch_must_exist
- nhi_required_for_all_nodes
- budget_enforcement_mandatory
- outer_meta_requires_human_or_high_assurance
- no_privilege_escalation
- audit_log_immutable
- safety_score_hard_gate_0.9
