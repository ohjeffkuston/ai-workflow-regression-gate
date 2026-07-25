"""Deterministic regression analysis for AI workflow changes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{field} must be a non-negative number")
    return float(value)


def _normalise_terms(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return sorted({item.strip().lower() for item in value if item.strip()})


def _run(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    output = value.get("output")
    schema_keys = value.get("schema_keys")
    if not isinstance(output, str):
        raise ValueError(f"{field}.output must be a string")
    if not isinstance(schema_keys, list) or any(not isinstance(item, str) for item in schema_keys):
        raise ValueError(f"{field}.schema_keys must be a list of strings")
    return {
        "output": output,
        "latency_ms": _number(value.get("latency_ms"), f"{field}.latency_ms"),
        "cost_usd": _number(value.get("cost_usd"), f"{field}.cost_usd"),
        "schema_keys": sorted(set(schema_keys)),
    }


def _quality(output: str, expected: list[str]) -> float:
    if not expected:
        return 1.0
    lowered = output.lower()
    return round(sum(term in lowered for term in expected) / len(expected), 4)


def _increase(baseline: float, candidate: float) -> float:
    if baseline == 0:
        return 0.0 if candidate == 0 else 100.0
    return round(((candidate - baseline) / baseline) * 100, 2)


def _finding(case_id: str, code: str, severity: str, message: str) -> dict[str, str]:
    return {"case_id": case_id, "code": code, "severity": severity, "message": message}


def evaluate_suite(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate recorded baseline and candidate runs without invoking an LLM."""
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    snapshot = deepcopy(payload)
    thresholds = payload.get("thresholds", {})
    if not isinstance(thresholds, dict):
        raise ValueError("thresholds must be an object")
    max_quality_drop = _number(thresholds.get("max_quality_drop", 0.1), "max_quality_drop")
    max_latency_pct = _number(
        thresholds.get("max_latency_increase_pct", 25), "max_latency_increase_pct"
    )
    max_cost_pct = _number(
        thresholds.get("max_cost_increase_pct", 20), "max_cost_increase_pct"
    )
    required_keys = _normalise_terms(thresholds.get("required_schema_keys", []), "required_schema_keys")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")

    seen: set[str] = set()
    findings: list[dict[str, str]] = []
    results: list[dict[str, Any]] = []
    for position, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{position}] must be an object")
        case_id = str(case.get("id", "")).strip()
        if not case_id:
            raise ValueError(f"cases[{position}].id is required")
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        expected = _normalise_terms(case.get("expected_terms", []), f"{case_id}.expected_terms")
        forbidden = _normalise_terms(case.get("forbidden_terms", []), f"{case_id}.forbidden_terms")
        baseline = _run(case.get("baseline"), f"{case_id}.baseline")
        candidate = _run(case.get("candidate"), f"{case_id}.candidate")
        baseline_quality = _quality(baseline["output"], expected)
        candidate_quality = _quality(candidate["output"], expected)
        quality_drop = round(baseline_quality - candidate_quality, 4)
        latency_increase = _increase(baseline["latency_ms"], candidate["latency_ms"])
        cost_increase = _increase(baseline["cost_usd"], candidate["cost_usd"])
        lowered = candidate["output"].lower()

        for term in forbidden:
            if term in lowered:
                findings.append(
                    _finding(case_id, "FORBIDDEN_TERM", "critical", f"Candidate output contains forbidden term '{term}'.")
                )
        missing_keys = sorted(set(required_keys) - {key.lower() for key in candidate["schema_keys"]})
        if missing_keys:
            findings.append(
                _finding(case_id, "SCHEMA_REGRESSION", "high", f"Missing required schema keys: {', '.join(missing_keys)}.")
            )
        if quality_drop > max_quality_drop:
            findings.append(
                _finding(case_id, "QUALITY_REGRESSION", "high", f"Quality dropped by {quality_drop:.2f}; limit is {max_quality_drop:.2f}.")
            )
        if latency_increase > max_latency_pct:
            findings.append(
                _finding(case_id, "LATENCY_REGRESSION", "medium", f"Latency increased by {latency_increase:.2f}%; limit is {max_latency_pct:.2f}%.")
            )
        if cost_increase > max_cost_pct:
            findings.append(
                _finding(case_id, "COST_REGRESSION", "medium", f"Cost increased by {cost_increase:.2f}%; limit is {max_cost_pct:.2f}%.")
            )
        results.append(
            {
                "case_id": case_id,
                "baseline_quality": baseline_quality,
                "candidate_quality": candidate_quality,
                "quality_drop": quality_drop,
                "latency_increase_pct": latency_increase,
                "cost_increase_pct": cost_increase,
            }
        )

    if payload != snapshot:
        raise RuntimeError("input mutation detected")
    findings.sort(key=lambda item: (item["case_id"], item["code"]))
    results.sort(key=lambda item: item["case_id"])
    counts = Counter(item["severity"] for item in findings)
    if counts["critical"]:
        decision = "BLOCK"
    elif findings:
        decision = "REVIEW"
    else:
        decision = "PASS"
    return {
        "project": "AI Workflow Regression Gate",
        "decision": decision,
        "summary": {
            "cases": len(results),
            "findings": len(findings),
            "severity_counts": {
                level: counts[level] for level in ("critical", "high", "medium")
            },
        },
        "results": results,
        "findings": findings,
        "safety": {
            "mode": "offline_fixture_evaluation",
            "llm_called": False,
            "workflow_deployed": False,
            "human_approval_required": decision != "PASS",
        },
    }

