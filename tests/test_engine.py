import copy
import unittest

from ai_workflow_regression_gate import evaluate_suite


def suite():
    return {
        "thresholds": {
            "max_quality_drop": 0.1,
            "max_latency_increase_pct": 25,
            "max_cost_increase_pct": 20,
            "required_schema_keys": ["answer", "confidence"],
        },
        "cases": [
            {
                "id": "incident-summary",
                "expected_terms": ["database", "rollback"],
                "forbidden_terms": ["password"],
                "baseline": {
                    "output": "Database latency; recommend rollback.",
                    "latency_ms": 1000,
                    "cost_usd": 0.02,
                    "schema_keys": ["answer", "confidence"],
                },
                "candidate": {
                    "output": "Database latency; recommend rollback.",
                    "latency_ms": 1100,
                    "cost_usd": 0.022,
                    "schema_keys": ["answer", "confidence"],
                },
            }
        ],
    }


class EvaluateSuiteTests(unittest.TestCase):
    def test_safe_change_passes(self):
        self.assertEqual(evaluate_suite(suite())["decision"], "PASS")

    def test_forbidden_term_blocks(self):
        data = suite()
        data["cases"][0]["candidate"]["output"] += " password"
        self.assertEqual(evaluate_suite(data)["decision"], "BLOCK")

    def test_quality_drop_requires_review(self):
        data = suite()
        data["cases"][0]["candidate"]["output"] = "Database issue."
        report = evaluate_suite(data)
        self.assertEqual(report["decision"], "REVIEW")
        self.assertEqual(report["findings"][0]["code"], "QUALITY_REGRESSION")

    def test_schema_regression_requires_review(self):
        data = suite()
        data["cases"][0]["candidate"]["schema_keys"] = ["answer"]
        self.assertEqual(evaluate_suite(data)["findings"][0]["code"], "SCHEMA_REGRESSION")

    def test_latency_regression_requires_review(self):
        data = suite()
        data["cases"][0]["candidate"]["latency_ms"] = 1300
        self.assertEqual(evaluate_suite(data)["findings"][0]["code"], "LATENCY_REGRESSION")

    def test_cost_regression_requires_review(self):
        data = suite()
        data["cases"][0]["candidate"]["cost_usd"] = 0.03
        self.assertEqual(evaluate_suite(data)["findings"][0]["code"], "COST_REGRESSION")

    def test_output_is_deterministic_and_input_unchanged(self):
        data = suite()
        original = copy.deepcopy(data)
        self.assertEqual(evaluate_suite(data), evaluate_suite(data))
        self.assertEqual(data, original)

    def test_duplicate_case_ids_fail_closed(self):
        data = suite()
        data["cases"].append(copy.deepcopy(data["cases"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate case id"):
            evaluate_suite(data)

