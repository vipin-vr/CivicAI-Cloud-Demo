from __future__ import annotations

import unittest

from priority import calculate_priority, priority_label


class PriorityTests(unittest.TestCase):
    def test_weighted_score_and_label(self) -> None:
        score, label, explanation = calculate_priority("High", 80, 60)
        self.assertEqual(score, 72.0)
        self.assertEqual(label, "High")
        self.assertIn("72.0/100", explanation)

    def test_inputs_are_clamped_and_unknown_severity_is_safe(self) -> None:
        score, label, _ = calculate_priority("unexpected", -10, 200)
        self.assertEqual(score, 50.0)
        self.assertEqual(label, "High")

    def test_label_boundaries(self) -> None:
        self.assertEqual(priority_label(29.9), "Low")
        self.assertEqual(priority_label(30), "Medium")
        self.assertEqual(priority_label(50), "High")
        self.assertEqual(priority_label(75), "Critical")
