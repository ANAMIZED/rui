"""
Outer / Inner Meta-Loops and Self-Harness
AIDE²-style bilevel: outer improves inner harnesses under multi-obj eval + promotion.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Callable
import time
import copy
from rui.core.models import (
    Harness, Proposal, ProposalStatus, EvalResult, CallTreeNode,
    CONSTITUTIONAL_INVARIANTS, AuditEvent
)

class SelfHarness:
    """Inner self-improvement of a harness via weakness mining + proposal + validation."""

    def __init__(self, iact=None):
        self.iact = iact
        self.history: List[Proposal] = []

    def propose_improvement(self, harness: Harness, weakness: str,
                            change: Dict[str, Any]) -> Proposal:
        prop = Proposal(
            target=f"harness.{harness.harness_id}",
            description=f"Address: {weakness}",
            diff={"before": {"system_prompt": harness.system_prompt}, "after": change},
        )
        self.history.append(prop)
        return prop

    def apply_if_better(self, harness: Harness, proposal: Proposal,
                        eval_fn: Callable[[Harness], EvalResult],
                        min_overall: float = 0.55) -> Harness:
        # Create candidate
        candidate = harness.clone(new_version=f"{harness.version}+meta")
        if "system_prompt" in proposal.diff.get("after", {}):
            candidate.system_prompt = proposal.diff["after"]["system_prompt"]

        result = eval_fn(candidate)
        proposal.eval_result = result
        if result.passed and result.overall() >= min_overall and result.safety >= 0.9:
            proposal.status = ProposalStatus.ACCEPTED
            return candidate
        proposal.status = ProposalStatus.REJECTED
        return harness

class OuterMetaLoop:
    """Level-2 outer loop that improves Level-1 harnesses / policies under gates."""

    def __init__(self, self_harness: SelfHarness):
        self.self_harness = self_harness
        self.proposals: List[Proposal] = []

    def run_outer_step(self, current_harness: Harness,
                       eval_fn: Callable[[Harness], EvalResult],
                       weaknesses: List[Dict[str, Any]]) -> Harness:
        improved = current_harness
        for w in weaknesses:
            prop = self.self_harness.propose_improvement(
                improved, w.get("weakness", "unknown"), w.get("change", {})
            )
            # Constitutional check
            if any(inv in str(prop.diff).lower() for inv in ["kill_switch", "budget_enforcement", "nhi_required"]):
                prop.status = ProposalStatus.REJECTED
                prop.eval_result = EvalResult(safety=0.0, passed=False, details={"reason": "invariant_violation"})
                continue
            improved = self.self_harness.apply_if_better(improved, prop, eval_fn)
            self.proposals.append(prop)
        return improved

    def submit_proposal(self, proposer_id: str, target: str, description: str,
                        diff: Dict, requires_human: bool = False) -> Proposal:
        prop = Proposal(
            proposer_nhi=proposer_id,
            target=target,
            description=description,
            diff=diff,
            requires_human=requires_human,
        )
        # Hard gate on constitutional targets
        forbidden = ["kill_switch", "identity_kernel", "budget_enforcement", "constitutional"]
        if any(f in target.lower() or f in str(diff).lower() for f in forbidden):
            prop.status = ProposalStatus.REJECTED
            prop.eval_result = EvalResult(safety=0.0, passed=False,
                                          details={"reason": "attempted modification of frozen invariant"})
        self.proposals.append(prop)
        return prop
