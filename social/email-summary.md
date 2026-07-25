Hello Jeffrey,

Day 8 of your Cloud + AI portfolio is AI Workflow Regression Gate.

PROJECT PURPOSE

AI workflows can regress after a prompt, model, tool, or n8n routing change even when the code still runs. This project compares recorded baseline and candidate results and produces a deterministic PASS, REVIEW, or BLOCK decision before release.

ARCHITECTURE

1. Workflow change: recorded baseline and candidate fixtures enter the gate.
2. Regression engine: deterministic checks cover quality, forbidden terms, schema, latency, and cost.
3. Decision report: case-level findings explain every PASS, REVIEW, or BLOCK result.
4. Human approval: non-passing changes stop. The project never deploys a workflow.

HOW THE CODE WORKS

- `engine.py` validates the input, calculates term-coverage quality, compares baseline and candidate performance, detects forbidden content and missing schema keys, and returns stable JSON.
- `cli.py` loads a suite and exits 0 only for PASS. REVIEW and BLOCK exit 1 so CI can stop a risky release.
- `tests/test_engine.py` covers safe changes, forbidden content, quality, schema, latency, cost, deterministic output, input immutability, and duplicate-ID failure.
- `examples/regression-suite.json` is an intentionally risky example that demonstrates REVIEW.
- `n8n/regression-gate-workflow.json` shows how an inactive webhook workflow can route PASS to approval and everything else to human review.
- `.github/workflows/ci.yml` runs unit tests and validates JSON artifacts.

HOW TO RUN IT

From the project directory:

`PYTHONPATH=src python -m unittest discover -s tests -v`

Then run the example:

`PYTHONPATH=src python -m ai_workflow_regression_gate examples/regression-suite.json`

The example exits 1 because it contains deliberate regressions. Inspect the JSON findings rather than treating that exit code as an application crash.

DEPLOYMENT PRACTICE

- Use synthetic or redacted fixtures only.
- Never store API keys, production prompts, or customer data in the repository.
- Protect the release branch and require the regression test as a status check.
- Version thresholds like code.
- Keep human approval for REVIEW and BLOCK.
- Import the n8n workflow only into a controlled self-hosted environment and inspect the command node before activation.

WHAT TO LEARN

Be able to explain why an AI workflow can be technically available but behaviorally regressed. Understand the difference between model evaluation and operational release gating. Practice tracing a case from input validation through quality, schema, latency, and cost findings to the final decision.

INTERVIEW POSITIONING

Use this project when asked how you would operationalize AI safely:

“I built a model-independent regression gate for AI and n8n workflows. It compares recorded baseline and candidate runs across quality, schema, latency, cost, and forbidden content. The engine produces deterministic evidence for CI/CD and requires human approval for non-passing changes. It calls no model and performs no deployment.”

Likely follow-up questions:

- Why use recorded fixtures? They make CI deterministic, fast, inexpensive, and safe.
- Why not auto-deploy PASS? PASS can feed the next controlled stage, but branch protection and human governance should match organizational risk.
- How would you extend it? Add semantic evaluators behind an interface, signed evidence, trend storage, per-workflow policies, and a protected CI status check.
- What is the failure mode? Invalid or duplicate input fails closed; REVIEW and BLOCK return a non-zero exit code.

Portfolio links:

GitHub: https://github.com/ohjeffkuston/ai-workflow-regression-gate
Architecture: https://raw.githubusercontent.com/ohjeffkuston/ai-workflow-regression-gate/main/docs/architecture.png

Regards,
Your Cloud + AI Portfolio Automation

