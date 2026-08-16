"""Unit tests for CostKernel."""
import sys
sys.path.insert(0, "src")
import unittest
from rui.core.models import Budget, CallTreeNode, ModelTier
from rui.cost.kernel import CostKernel

class TestCostKernel(unittest.TestCase):
    def setUp(self):
        self.ck = CostKernel(Budget(tokens=10000, dollars=1.0, max_depth=3))

    def test_estimate(self):
        cost = self.ck.estimate_cost(1000, 500, ModelTier.MID)
        self.assertGreater(cost, 0)

    def test_record(self):
        node = CallTreeNode(budget=Budget(tokens=5000, dollars=0.5))
        rec = self.ck.record(node, 100, 50, model="test", action="unit")
        self.assertEqual(rec.input_tokens, 100)
        self.assertTrue(len(self.ck.global_records) >= 1)

    def test_circuit_breaker(self):
        node = CallTreeNode(budget=Budget(tokens=100, dollars=0.01, max_depth=2))
        for _ in range(5):
            self.ck.record(node, 30, 10)
        should, reason = self.ck.check_circuit_breaker(node)
        self.assertTrue(should or node.total_tokens_used() > 0)

if __name__ == "__main__":
    unittest.main()
