"""
Recursive Agent Harness (RAH)
Implements harness recursion: parent spawns full sub-harnesses via script simulation.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable
import time
from rui.core.models import Harness, CallTreeNode, NodeStatus, ModelTier
from rui.runtime.iact import IACT

class RAH:
    """Recursive Agent Harness manager."""

    def __init__(self, iact: IACT):
        self.iact = iact

    def create_default_harness(self, name: str = "default") -> Harness:
        return Harness(
            name=name,
            system_prompt="You are a recursive coding/research agent. Decompose complex tasks and spawn sub-agents when beneficial.",
            tools=["code_exec", "fs_read", "search"],
            recursion_policy={
                "enabled": True,
                "min_complexity": 0.4,
                "prefer_parallel": True,
                "max_subagents": 8,
            },
        )

    def recursive_decompose(self, parent_id: str, subtasks: List[str],
                            work_fn: Optional[Callable] = None) -> List[Any]:
        results = []
        parent = self.iact.nodes.get(parent_id)
        if not parent:
            return results

        for st in subtasks:
            child = self.iact.spawn_child(parent_id, st, scale=0.3)
            if child:
                res = self.iact.execute_node(child.id, work_fn=work_fn,
                                             simulate_tokens=800, simulate_output=250, model="mid")
                results.append(res)
                if self.iact.should_recurse(child, complexity=0.55):
                    gchild = self.iact.spawn_child(child.id, f"Refine: {st[:40]}", scale=0.4)
                    if gchild:
                        self.iact.execute_node(gchild.id, work_fn=work_fn,
                                               simulate_tokens=400, simulate_output=150, model="slm")
        return results

    def should_recurse(self, node: CallTreeNode, complexity: float = 0.5) -> bool:
        return self.iact.should_recurse(node, complexity)
