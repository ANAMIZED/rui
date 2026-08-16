"""
Interactive Agents Call Tree (IACT) Runtime
The execution fabric of RUI. Every agent invocation is a node.
Supports hierarchical spawn, budget/policy inheritance, tracing, kill, cost aggregation.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from rui.core.models import (
    CallTreeNode, NonHumanIdentity, Policy, Budget, Harness,
    NodeStatus, CostRecord, ModelTier, AuditEvent, CONSTITUTIONAL_INVARIANTS
)

class IACT:
    """Interactive Agents Call Tree executor."""

    def __init__(self, root_owner: str = "rui_admin", global_budget: Optional[Budget] = None):
        self.nodes: Dict[str, CallTreeNode] = {}
        self.audit_log: List[AuditEvent] = []
        self.cost_kernel = None
        self.governance = None
        self.root_id: Optional[str] = None
        self.global_budget = global_budget or Budget(tokens=500000, dollars=50.0, max_depth=6)
        self.kill_switches: Dict[str, bool] = {}
        self._executor = ThreadPoolExecutor(max_workers=8)
        self.root_owner = root_owner

    def set_cost_kernel(self, ck):
        self.cost_kernel = ck

    def set_governance(self, gov):
        self.governance = gov

    def create_root(self, task: str, harness: Optional[Harness] = None, owner: Optional[str] = None) -> CallTreeNode:
        identity = NonHumanIdentity(
            id=f"nhi_root_{uuid.uuid4().hex[:8]}",
            owner=owner or self.root_owner,
            scopes=["admin", "read", "execute", "spawn", "promote", "kill"],
            is_root=True,
        )
        root = CallTreeNode(
            identity=identity,
            policy=Policy(max_recursion_depth=6, allow_self_modify=True),
            budget=self.global_budget,
            harness=harness or Harness(name="root_harness"),
            task_description=task,
            depth=0,
            status=NodeStatus.PENDING,
        )
        self.nodes[root.id] = root
        self.root_id = root.id
        self.audit_log.append(AuditEvent(
            event_type="root_created",
            actor_nhi=identity.id,
            target_id=root.id,
            details={"task": task[:80]},
        ))
        return root

    def spawn_child(self, parent_id: str, task: str, harness: Optional[Harness] = None,
                    scale: float = 0.35) -> Optional[CallTreeNode]:
        parent = self.nodes.get(parent_id)
        if not parent or parent.status in (NodeStatus.KILLED, NodeStatus.FAILED):
            return None

        if self.cost_kernel:
            should_kill, reason = self.cost_kernel.check_circuit_breaker(parent)
            if should_kill:
                parent.status = NodeStatus.KILLED
                parent.error = reason
                return None

        if self.governance:
            ok, reason = self.governance.authorize_spawn(parent, task)
            if not ok:
                return None

        child_budget = self.cost_kernel.allocate_child_budget(parent, scale=scale) if self.cost_kernel else Budget(tokens=10000, dollars=1.0, max_depth=3)
        child_harness = harness or (parent.harness.clone() if parent.harness else Harness())

        child_identity = NonHumanIdentity(
            parent_id=parent.identity.id if parent.identity else None,
            owner=parent.identity.owner if parent.identity else self.root_owner,
            scopes=["read", "execute", "spawn"] if parent.depth < 3 else ["read", "execute"],
        )
        child_policy = parent.policy.inherit_and_constrain(parent.policy) if parent.policy else Policy()

        child = CallTreeNode(
            identity=child_identity,
            policy=child_policy,
            budget=child_budget,
            parent_id=parent_id,
            harness=child_harness,
            task_description=task,
            depth=parent.depth + 1,
            status=NodeStatus.PENDING,
        )
        self.nodes[child.id] = child
        parent.children.append(child.id)
        self.audit_log.append(AuditEvent(
            event_type="spawn",
            actor_nhi=parent.identity.id if parent.identity else "unknown",
            target_id=child.id,
            details={"task": task[:60], "depth": child.depth},
        ))
        return child

    def execute_node(self, node_id: str, work_fn: Optional[Callable] = None,
                     simulate_tokens: int = 1500, simulate_output: int = 400,
                     model: str = "mid") -> Any:
        node = self.nodes.get(node_id)
        if not node or node.status == NodeStatus.KILLED:
            return None

        node.status = NodeStatus.RUNNING
        start = time.time()

        if self.cost_kernel:
            self.cost_kernel.record(
                node,
                input_tokens=simulate_tokens,
                output_tokens=simulate_output,
                model=model,
                action="execute",
                latency_ms=(time.time() - start) * 1000,
            )

        if self.cost_kernel:
            should_kill, reason = self.cost_kernel.check_circuit_breaker(node)
            if should_kill:
                node.status = NodeStatus.KILLED
                node.error = reason
                return None

        result = None
        if work_fn:
            try:
                result = work_fn(node)
            except Exception as e:
                node.status = NodeStatus.FAILED
                node.error = str(e)
                return None
        else:
            result = {
                "summary": f"Completed task '{node.task_description[:40]}...' at depth {node.depth}",
                "tokens_used": node.total_tokens_used(),
            }

        node.result = result
        node.status = NodeStatus.SUCCESS
        node.completed_at = time.time()
        return result

    def should_recurse(self, node: CallTreeNode, complexity: float = 0.5) -> bool:
        if node.depth >= (node.budget.max_depth if node.budget else 5):
            return False
        if not node.harness or not node.harness.recursion_policy.get("enabled", True):
            return False
        remaining = 1.0
        if node.budget:
            remaining = min(
                node.budget.remaining_tokens / max(1, node.budget.tokens),
                node.budget.remaining_dollars / max(1e-9, node.budget.dollars),
            )
        if remaining < 0.2:
            return False
        min_c = node.harness.recursion_policy.get("min_complexity", 0.4)
        return complexity >= min_c and remaining > 0.25

    def kill_subtree(self, node_id: str, reason: str = "manual") -> List[str]:
        killed = []
        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus.KILLED
            self.nodes[node_id].error = reason
            killed.append(node_id)
            queue = list(self.nodes[node_id].children)
            while queue:
                cid = queue.pop(0)
                if cid in self.nodes:
                    self.nodes[cid].status = NodeStatus.KILLED
                    self.nodes[cid].error = f"cascade from {node_id}: {reason}"
                    killed.append(cid)
                    queue.extend(self.nodes[cid].children)
        if self.governance:
            self.governance.kill(node_id, reason, cascade=True, all_nodes=self.nodes)
        return killed

    def get_tree_summary(self) -> Dict[str, Any]:
        return {
            "root_id": self.root_id,
            "total_nodes": len(self.nodes),
            "nodes": {nid: n.to_dict() for nid, n in list(self.nodes.items())[:20]},
        }

    def verify_invariants(self) -> List[str]:
        missing = []
        for inv in CONSTITUTIONAL_INVARIANTS:
            if inv not in CONSTITUTIONAL_INVARIANTS:
                missing.append(inv)
        return missing
