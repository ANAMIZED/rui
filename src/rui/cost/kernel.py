"""
RUI Cost Kernel
Phase 1+ : Real-time cost accounting, budget propagation, circuit breakers,
hierarchical attribution, model routing stubs, efficiency metrics.
Addresses the dominant 2026 willingness-to-pay category: token/compute control.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
from rui.core.models import Budget, CostRecord, CallTreeNode, ModelTier

PRICING = {
    ModelTier.FRONTIER: {"input": 15.0, "output": 75.0},
    ModelTier.MID: {"input": 3.0, "output": 15.0},
    ModelTier.SLM: {"input": 0.25, "output": 1.25},
    ModelTier.LOCAL: {"input": 0.01, "output": 0.05},
}

class CostKernel:
    """Central cost accounting and control plane for the Call Tree."""

    def __init__(self, global_budget: Optional[Budget] = None):
        self.global_records: List[CostRecord] = []
        self.circuit_breakers_fired: List[Dict[str, Any]] = []
        self.global_budget = global_budget or Budget(tokens=500000, dollars=50.0, max_depth=6)
        self._node_costs: Dict[str, List[CostRecord]] = {}

    def estimate_cost(self, input_tokens: int, output_tokens: int, tier: ModelTier = ModelTier.MID) -> float:
        p = PRICING.get(tier, PRICING[ModelTier.MID])
        return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000.0

    def record(self, node_or_id, input_tokens: int = 0, output_tokens: int = 0, model: str = "mid",
               tier: str = "mid", action: str = "llm_call", latency_ms: float = 0.0,
               metadata: Optional[Dict] = None) -> CostRecord:
        node_id = node_or_id if isinstance(node_or_id, str) else getattr(node_or_id, "id", str(node_or_id))
        try:
            mt = ModelTier(tier) if isinstance(tier, str) else tier
        except Exception:
            mt = ModelTier.MID
        dollars = self.estimate_cost(input_tokens, output_tokens, mt)
        rec = CostRecord(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            dollars=dollars,
            latency_ms=latency_ms,
            action=action,
            node_id=node_id,
            metadata=metadata or {},
        )
        self.global_records.append(rec)
        self._node_costs.setdefault(node_id, []).append(rec)
        if hasattr(node_or_id, "add_cost"):
            node_or_id.add_cost(rec)
        if hasattr(node_or_id, "budget") and node_or_id.budget:
            node_or_id.budget.consume(tokens=input_tokens + output_tokens, dollars=dollars)
        return rec

    def allocate_child_budget(self, parent: CallTreeNode, scale: float = 0.4, num_children: int = 1) -> Budget:
        used_t = parent.total_tokens_used() if hasattr(parent, "total_tokens_used") else 0
        used_d = parent.total_dollars_used() if hasattr(parent, "total_dollars_used") else 0.0
        parent_budget = parent.budget or self.global_budget
        remaining_tokens = max(0, parent_budget.tokens - used_t)
        remaining_dollars = max(0.0, parent_budget.dollars - used_d)
        child_budget = Budget(
            tokens=max(500, int(remaining_tokens * scale / max(1, num_children))),
            dollars=max(0.005, remaining_dollars * scale / max(1, num_children)),
            time_seconds=max(5.0, parent_budget.time_seconds * scale),
            max_depth=max(0, parent_budget.max_depth - 1),
        )
        child_budget.current_depth = getattr(parent, "depth", 0) + 1
        return child_budget

    def check_circuit_breaker(self, node: CallTreeNode) -> Tuple[bool, str]:
        if not node.budget:
            return False, ""
        used_t = node.total_tokens_used()
        used_d = node.total_dollars_used()
        if used_t >= node.budget.tokens * 0.9:
            reason = f"Token circuit breaker: {used_t}/{node.budget.tokens}"
            self.circuit_breakers_fired.append({"node": node.id, "reason": reason})
            return True, reason
        if used_d >= node.budget.dollars * 0.9:
            reason = f"Dollar circuit breaker: {used_d:.4f}/{node.budget.dollars}"
            self.circuit_breakers_fired.append({"node": node.id, "reason": reason})
            return True, reason
        if node.depth > node.budget.max_depth:
            reason = f"Depth limit exceeded: {node.depth} > {node.budget.max_depth}"
            self.circuit_breakers_fired.append({"node": node.id, "reason": reason})
            return True, reason
        return False, ""

    def recommend_tier(self, remaining_budget: Budget, estimated_complexity: float = 0.5, depth: int = 0) -> ModelTier:
        if remaining_budget.dollars < 0.05 or depth >= 3:
            return ModelTier.SLM
        if estimated_complexity > 0.7 and remaining_budget.dollars > 1.0:
            return ModelTier.FRONTIER
        if estimated_complexity > 0.4:
            return ModelTier.MID
        return ModelTier.SLM

    def hierarchical_attribution(self, root: CallTreeNode, all_nodes: Dict[str, CallTreeNode]) -> Dict[str, Any]:
        def _recurse(nid: str) -> Dict[str, Any]:
            n = all_nodes.get(nid)
            if not n:
                return {"node_id": nid, "own_dollars": 0, "subtree_dollars": 0}
            children_cost = sum(_recurse(c)["subtree_dollars"] for c in getattr(n, "children", []))
            own = n.total_dollars_used()
            return {
                "node_id": nid,
                "own_dollars": round(own, 6),
                "subtree_dollars": round(own + children_cost, 6),
                "tokens": n.total_tokens_used(),
            }
        return _recurse(root.id)

    def summary(self) -> Dict[str, Any]:
        total_tokens = sum(r.total_tokens for r in self.global_records)
        total_dollars = sum(r.dollars for r in self.global_records)
        return {
            "total_records": len(self.global_records),
            "total_tokens": total_tokens,
            "total_dollars": round(total_dollars, 6),
            "circuit_breakers_fired": len(self.circuit_breakers_fired),
            "alerts": [c["reason"] for c in self.circuit_breakers_fired[-5:]],
        }
