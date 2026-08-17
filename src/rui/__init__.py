"""
RUI - Recursive UltraIntelligence Autonomous Agentic OS
Top-level integration of all kernels + surfaces.
"""

from __future__ import annotations

__version__ = "0.2.0"

from rui.runtime.iact import IACT
from rui.runtime.rah import RAH
from rui.meta.self_harness import SelfHarness, OuterMetaLoop
from rui.core.models import *  # noqa: F401,F403
from rui.cost.kernel import CostKernel
from rui.governance.kernel import GovernanceKernel, PromotionProtocol, MultiObjectiveEvaluator


class RUI:
    """Top-level Recursive UltraIntelligence instance."""

    def __init__(self, owner: str = "rui_admin"):
        self.owner = owner
        self.iact = IACT(root_owner=owner)
        self.cost = CostKernel()
        self.governance = GovernanceKernel(root_owner=owner)
        if hasattr(self.iact, "set_cost_kernel"):
            self.iact.set_cost_kernel(self.cost)
        if hasattr(self.iact, "set_governance"):
            self.iact.set_governance(self.governance)
        self.rah = RAH(self.iact)
        self.self_harness = SelfHarness(self.iact)
        self.outer_meta = OuterMetaLoop(self.self_harness)
        self.promotion = PromotionProtocol(self.governance)

    def start_task(self, task: str):
        h = self.rah.create_default_harness("root") if hasattr(self.rah, "create_default_harness") else None
        root = self.iact.create_root(task, harness=h, owner=self.owner) if hasattr(self.iact, "create_root") else None
        return root

    def tree_summary(self) -> dict:
        return self.iact.get_tree_summary()

    def verify_constitution(self) -> dict:
        return self.governance.verify_constitutional()


def main():
    print(f"RUI Autonomous Agentic OS v{__version__} ready")


if __name__ == "__main__":
    main()
