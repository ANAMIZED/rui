"""
RUI - Recursive UltraIntelligence Autonomous Agentic OS
Top-level integration of all kernels.
"""

from rui.runtime.iact import IACT
from rui.runtime.rah import RAH
from rui.meta.self_harness import SelfHarness, OuterMetaLoop
from rui.core.models import *
from rui.cost.kernel import CostKernel

class RUI:
    def __init__(self, owner: str = "rui_admin"):
        self.iact = IACT(root_owner=owner)
        self.cost = CostKernel()
        if hasattr(self.iact, "set_cost_kernel"):
            self.iact.set_cost_kernel(self.cost)
        self.rah = RAH(self.iact)
        self.self_harness = SelfHarness(self.iact)
        self.outer_meta = OuterMetaLoop(self.self_harness)
        self.owner = owner

    def start_task(self, task: str):
        h = self.rah.create_default_harness("root") if hasattr(self.rah, "create_default_harness") else None
        root = self.iact.create_root(task, harness=h, owner=self.owner) if hasattr(self.iact, "create_root") else None
        return root

def main():
    print("RUI Autonomous Agentic OS ready")

if __name__ == "__main__":
    main()
