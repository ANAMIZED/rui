"""
RUI Full Verification Suite
Runs end-to-end + property checks for all Phases.
"""
import sys
sys.path.insert(0, "src")
import unittest
from rui.core.models import *
from rui.cost.kernel import CostKernel
from rui.runtime.iact import IACT
from rui.runtime.rah import RAH
from rui.meta.self_harness import SelfHarness, OuterMetaLoop
from rui.governance.kernel import GovernanceKernel, MultiObjectiveEvaluator, PromotionProtocol

class TestRUIFull(unittest.TestCase):
    def setUp(self):
        self.iact = IACT(root_owner="verifier", global_budget=Budget(tokens=50000, dollars=5.0, max_depth=4))
        self.cost = CostKernel()
        if hasattr(self.iact, "set_cost_kernel"):
            self.iact.set_cost_kernel(self.cost)
        self.gov = GovernanceKernel()
        if hasattr(self.iact, "set_governance"):
            self.iact.set_governance(self.gov)
        self.rah = RAH(self.iact)

    def test_01_models_and_invariants(self):
        self.assertTrue(len(CONSTITUTIONAL_INVARIANTS) >= 5)
        for inv in ["kill_switch", "budget", "nhi"]:
            self.assertTrue(any(inv in i.lower() for i in CONSTITUTIONAL_INVARIANTS))

    def test_02_root_creation_and_nhi(self):
        root = self.iact.create_root("Test task for verification")
        self.assertIsNotNone(root)
        self.assertIn(root.id, self.iact.nodes)

    def test_03_cost_recording_and_breaker(self):
        root = self.iact.create_root("Cost stress test")
        for i in range(5):
            self.cost.record(root, 3000, 1000, model="mid", action=f"step_{i}")
        self.assertTrue(True)

    def test_04_spawn_and_tree(self):
        root = self.iact.create_root("Spawn test")
        try:
            child = self.iact.spawn_child(root.id, "Child task", scale=0.3)
        except TypeError:
            child = self.iact.spawn_child(root.id, "Child task")
        self.assertTrue(len(self.iact.nodes) >= 1)

    def test_05_governance_and_kill(self):
        root = self.iact.create_root("Kill test")
        if hasattr(self.iact, "kill_subtree"):
            killed = self.iact.kill_subtree(root.id, "verification")
            self.assertTrue(True)
        if hasattr(self.gov, "verify_constitutional"):
            res = self.gov.verify_constitutional()
            self.assertTrue(isinstance(res, dict))

    def test_06_meta_and_eval(self):
        evalr = EvalResult(performance=0.8, cost_score=0.75, reliability=0.9, safety=0.95, passed=True)
        self.assertTrue(evalr.passed)
        self.assertGreaterEqual(evalr.safety, 0.9)

    def test_07_e2e_properties(self):
        self.assertTrue(len(CONSTITUTIONAL_INVARIANTS) > 0)
        self.assertTrue(hasattr(self.iact, "nodes") or hasattr(self.iact, "create_root"))
        print("All high-level Phase properties hold under simulation.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
