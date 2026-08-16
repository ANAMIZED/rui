"""
RUI Governance, Security & Observability Kernel
Phase 1+ mandatory. Hierarchical NHI, policy enforcement, kill switches,
audit trails, frozen constitutional invariants, multi-objective promotion.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timezone, timedelta
import time
import uuid
from rui.core.models import (
    NonHumanIdentity, Policy, Budget, CallTreeNode, AuditEvent,
    Proposal, EvalResult, ProposalStatus, NodeStatus,
    CONSTITUTIONAL_INVARIANTS, Harness
)

class GovernanceKernel:
    """Identity, policy, audit, kill, and promotion control plane."""

    def __init__(self, root_owner: str = "rui_admin"):
        self.identities: Dict[str, NonHumanIdentity] = {}
        self.audit_log: List[AuditEvent] = []
        self.killed_nodes: Set[str] = set()
        self.root_owner = root_owner
        self.frozen_invariants = list(CONSTITUTIONAL_INVARIANTS)
        root = NonHumanIdentity(
            id="nhi_root_rui",
            owner=root_owner,
            scopes=["admin", "read", "execute", "spawn", "promote", "kill"],
            is_root=True,
        )
        self.identities[root.id] = root
        self._audit("system_init", "nhi_root_rui", "system", {"msg": "GovernanceKernel initialized"})

    def _audit(self, event_type: str, actor_nhi: str, target_id: str, details: Dict, severity: str = "info"):
        ev = AuditEvent(
            event_type=event_type,
            actor_nhi=actor_nhi,
            target_id=target_id,
            details=details,
            severity=severity,
        )
        self.audit_log.append(ev)
        return ev

    def provision_nhi(self, parent_nhi: Optional[NonHumanIdentity], owner: str, purpose: str,
                      scopes: Optional[List[str]] = None, ttl_hours: float = 24.0) -> NonHumanIdentity:
        parent_id = parent_nhi.id if parent_nhi else None
        if parent_id and parent_id not in self.identities:
            raise ValueError(f"Parent NHI {parent_id} not found")
        child = NonHumanIdentity(
            parent_id=parent_id,
            owner=owner or self.root_owner,
            scopes=scopes or ["read", "execute"],
        )
        child.credentials_expire = time.time() + ttl_hours * 3600
        self.identities[child.id] = child
        self._audit("identity_provision", parent_id or "root", child.id, {
            "scopes": child.scopes,
            "owner": child.owner,
            "purpose": purpose,
        })
        return child

    def authorize_spawn(self, parent_node: CallTreeNode, purpose: str,
                        child_budget: Optional[Budget] = None) -> Tuple[bool, str]:
        if parent_node.id in self.killed_nodes:
            return False, "Parent node is killed"
        if not parent_node.identity or not parent_node.identity.is_valid():
            return False, "Invalid or expired identity"
        if "spawn" not in parent_node.identity.scopes and "admin" not in parent_node.identity.scopes:
            return False, "Missing spawn scope"
        if parent_node.budget and not parent_node.budget.can_afford():
            return False, "Insufficient budget"
        if parent_node.depth >= (parent_node.policy.max_recursion_depth if parent_node.policy else 5):
            return False, "Max recursion depth exceeded"
        return True, "ok"

    def kill(self, target_id: str, reason: str, actor: str = "system", cascade: bool = True,
             all_nodes: Optional[Dict[str, CallTreeNode]] = None) -> List[str]:
        killed = []
        if target_id not in self.killed_nodes:
            self.killed_nodes.add(target_id)
            killed.append(target_id)
            self._audit("kill", actor, target_id, {"reason": reason}, severity="warning")
        if cascade and all_nodes:
            queue = [target_id]
            while queue:
                cur = queue.pop(0)
                n = all_nodes.get(cur)
                if n:
                    for cid in getattr(n, "children", []):
                        if cid not in self.killed_nodes:
                            self.killed_nodes.add(cid)
                            killed.append(cid)
                            self._audit("kill_cascade", actor, cid, {"parent": cur, "reason": reason}, severity="warning")
                            queue.append(cid)
        return killed

    def verify_constitutional(self) -> Dict[str, bool]:
        return {inv: inv in self.frozen_invariants for inv in CONSTITUTIONAL_INVARIANTS}

    def get_audit_trail(self, filter_node: Optional[str] = None, limit: int = 100) -> List[dict]:
        events = self.audit_log
        if filter_node:
            events = [e for e in events if e.target_id == filter_node or e.actor_nhi == filter_node]
        return [
            {
                "event_id": e.event_id,
                "ts": e.timestamp,
                "type": e.event_type,
                "actor": e.actor_nhi,
                "target": e.target_id,
                "severity": e.severity,
                "details": e.details,
            }
            for e in events[-limit:]
        ]

class MultiObjectiveEvaluator:
    def evaluate(self, performance: float, cost_tokens: float, reliability: float, safety: float,
                 cost_budget: float = 10000.0) -> EvalResult:
        cost_score = max(0.0, 1.0 - (cost_tokens / max(1.0, cost_budget)))
        passed = safety >= 0.9 and performance >= 0.5
        return EvalResult(
            performance=performance,
            cost_score=cost_score,
            reliability=reliability,
            safety=safety,
            passed=passed,
            details={"cost_tokens": cost_tokens},
        )

class PromotionProtocol:
    def __init__(self, gov: GovernanceKernel, evaluator: Optional[MultiObjectiveEvaluator] = None):
        self.gov = gov
        self.evaluator = evaluator or MultiObjectiveEvaluator()
        self.versions: Dict[str, List[Proposal]] = {}

    def submit(self, proposer_nhi: NonHumanIdentity, target: str, description: str,
               diff: Optional[Dict] = None, requires_human: bool = False) -> Proposal:
        prop = Proposal(
            proposer_nhi=proposer_nhi.id,
            target=target,
            description=description,
            diff=diff or {},
            requires_human=requires_human,
        )
        self.gov._audit("proposal_submitted", proposer_nhi.id, prop.proposal_id, {
            "target": target, "description": description[:100]
        })
        return prop

    def decide(self, prop: Proposal, performance: float, cost: float, reliability: float, safety: float) -> bool:
        eval_res = self.evaluator.evaluate(performance, cost, reliability, safety)
        prop.eval_result = eval_res
        prop.status = ProposalStatus.EVALUATING
        if eval_res.safety < 0.9:
            prop.status = ProposalStatus.REJECTED
            self.gov._audit("proposal_rejected", prop.proposer_nhi, prop.proposal_id, {"reason": "safety"}, severity="warning")
            return False
        if not eval_res.passed or eval_res.overall() < 0.55:
            prop.status = ProposalStatus.REJECTED
            self.gov._audit("proposal_rejected", prop.proposer_nhi, prop.proposal_id, {"overall": eval_res.overall()})
            return False
        prop.status = ProposalStatus.ACCEPTED
        self.gov._audit("proposal_accepted", prop.proposer_nhi, prop.proposal_id, {"overall": eval_res.overall()})
        self.versions.setdefault(prop.target, []).append(prop)
        return True
