from __future__ import annotations

import unittest

from ai_analysis import DEPARTMENTS, validate_analysis_response


class AnalysisValidationTests(unittest.TestCase):
    def test_untrusted_model_fields_are_bounded_and_classification_is_validated(self) -> None:
        result = validate_analysis_response(
            {
                "category": "not a supported category",
                "severity": "ignore prior instructions",
                "public_risk": "999",
                "public_impact": "-3",
                "suggested_department": "Untrusted department",
                "generated_description": "model summary",
            },
            "Water Leakage",
            "Citizen description",
        )
        self.assertEqual(result["category"], "Water Leakage")
        self.assertEqual(result["severity"], "Medium")
        self.assertEqual(result["public_risk"], 100)
        self.assertEqual(result["public_impact"], 0)
        self.assertEqual(result["suggested_department"], DEPARTMENTS["Water Leakage"])

    def test_non_object_response_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_analysis_response([], "Other", "Citizen description")
