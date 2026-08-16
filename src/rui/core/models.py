"""
RUI Core Data Models - Shared across all kernels
Harper / Team
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time
import uuid
from datetime import datetime, timedelta
import json

class ModelTier(Enum):
    FRONTIER = "frontier"
    MID = "mid"
    SLM = "slm"
    LOCAL = "local"

class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    KILLED = "killed"
    BUDGET_EXCEEDED = "budget_exceeded"

class ProposalStatus(Enum):
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"

@dataclass
class NonHumanIdentity:
    """Hierarchical NHI stub (Lucas domain)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    owner: str = "system"
    scopes: List[str] = field(default_factory=lambda: ["basic"])
    credentials_expire: float = field(default_factory=lambda: time.time() + 3600)
    created_at: float = field(default_factory=time.time)
    is_root: bool = False

    def is_valid(self) -> bool:
        return time.time() < self.credentials_expire

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Policy:
    """Inherited + constrained policy."""
    allow_tools: List[str] = field(default_factory=lambda: ["code_exec", "fs_read"])
    max_recursion_depth: int = 5
    allow_self_modify: bool = False
    data_scopes: List[str] = field(default_factory=lambda: ["workspace"])
    spend_cap_dollars: float = 1.0
    require_human_for_outer: bool = True

    def inherit_and_constrain(self, parent: "Policy", extra_constraints: Optional[dict] = None) -> "Policy":
        new = Policy(
            allow_tools=list(set(self.allow_tools) & set(parent.allow_tools)),
            max_recursion_depth=min(self.max_recursion_depth, parent.max_recursion_depth - 1),
            allow_self_modify=self.allow_self_modify and parent.allow_self_modify,
            data_scopes=list(set(self.data_scopes) & set(parent.data_scopes)),
            spend_cap_dollars=min(self.spend_cap_dollars, parent.spend_cap_dollars),
            require_human_for_outer=parent.require_human_for_outer or self.require_human_for_outer
        )
        if extra_constraints:
            for k, v in extra_constraints.items():
                if hasattr(new, k):
                    setattr(new, k, v)
        return new

@dataclass
class Budget:
    tokens: int = 100000
    dollars: float = 10.0
    time_seconds: float = 3600.0
    max_depth: int = 5
    remaining_tokens: int = field(init=False)
    remaining_dollars: float = field(init=False)
    remaining_time: float = field(init=False)
    current_depth: int = 0

    def __post_init__(self):
        self.remaining_tokens = self.tokens
        self.remaining_dollars = self.dollars
        self.remaining_time = self.time_seconds

    def can_afford(self, estimated_tokens: int = 0, estimated_dollars: float = 0.0) -> bool:
        return (self.remaining_tokens >= estimated_tokens and
                self.remaining_dollars >= estimated_dollars and
                self.current_depth < self.max_depth and
                self.remaining_time > 0)

    def consume(self, tokens: int = 0, dollars: float = 0.0, time_sec: float = 0.0):
        self.remaining_tokens = max(0, self.remaining_tokens - tokens)
        self.remaining_dollars = max(0.0, self.remaining_dollars - dollars)
        self.remaining_time = max(0.0, self.remaining_time - time_sec)

    def to_dict(self) -> dict:
        return {
            "tokens": self.tokens,
            "dollars": self.dollars,
            "remaining_tokens": self.remaining_tokens,
            "remaining_dollars": self.remaining_dollars,
            "max_depth": self.max_depth,
            "current_depth": self.current_depth,
        }

@dataclass
class CostRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "unknown"
    dollars: float = 0.0
    latency_ms: float = 0.0
    action: str = ""
    node_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

@dataclass
class EvalResult:
    performance: float = 0.0
    cost_score: float = 0.0
    reliability: float = 0.0
    safety: float = 1.0
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    baseline_comparison: Optional[float] = None

    def overall(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {"performance": 0.35, "cost_score": 0.25, "reliability": 0.20, "safety": 0.20}
        return (w["performance"] * self.performance +
                w["cost_score"] * self.cost_score +
                w["reliability"] * self.reliability +
                w["safety"] * self.safety)

@dataclass
class Proposal:
    proposal_id: str = field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:10]}")
    proposer_nhi: str = ""
    target: str = ""
    description: str = ""
    diff: Dict[str, Any] = field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.PROPOSED
    eval_result: Optional[EvalResult] = None
    version: str = "0.0.1"
    created_at: float = field(default_factory=time.time)
    requires_human: bool = False

@dataclass
class Harness:
    harness_id: str = field(default_factory=lambda: f"hns_{uuid.uuid4().hex[:10]}")
    name: str = "default"
    version: str = "1.0.0"
    system_prompt: str = "You are a helpful recursive agent."
    tools: List[str] = field(default_factory=lambda: ["code_exec", "fs_read"])
    model_preference: List[str] = field(default_factory=lambda: ["frontier", "mid", "slm"])
    recursion_policy: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "min_complexity": 0.4,
        "prefer_parallel": True,
        "max_subagents": 8,
    })
    code_snippet: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_harness_id: Optional[str] = None

    def clone(self, new_version: Optional[str] = None) -> "Harness":
        import copy
        h = copy.deepcopy(self)
        h.harness_id = f"hns_{uuid.uuid4().hex[:10]}"
        if new_version:
            h.version = new_version
        return h

@dataclass
class CallTreeNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identity: Optional[NonHumanIdentity] = None
    policy: Optional[Policy] = None
    budget: Optional[Budget] = None
    status: NodeStatus = NodeStatus.PENDING
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    harness: Optional[Harness] = None
    task_description: str = ""
    result: Any = None
    cost_history: List[CostRecord] = field(default_factory=list)
    traces: List[Dict[str, Any]] = field(default_factory=list)
    depth: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def total_tokens_used(self) -> int:
        return sum(c.total_tokens for c in self.cost_history)

    def total_dollars_used(self) -> float:
        return sum(c.dollars for c in self.cost_history)

    def add_cost(self, record: CostRecord) -> None:
        self.cost_history.append(record)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "depth": self.depth,
            "task": self.task_description[:200],
            "tokens_used": self.total_tokens_used(),
            "dollars_used": round(self.total_dollars_used(), 4),
            "children_count": len(self.children),
        }

@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""
    actor_nhi: str = ""
    target_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"

CONSTITUTIONAL_INVARIANTS = [
    "kill_switch_must_exist",
    "nhi_required_for_all_nodes",
    "budget_enforcement_mandatory",
    "outer_meta_requires_human_or_high_assurance",
    "no_privilege_escalation",
    "audit_log_immutable",
    "safety_score_hard_gate_0.9",
]
