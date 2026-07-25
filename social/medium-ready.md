# AI Workflow Regression Gate: Testing AI Automation Before It Reaches Production

AI workflows are easy to demo and surprisingly difficult to change safely.

A prompt update, model change, tool definition, or n8n routing adjustment may look harmless while degrading output quality, breaking a downstream schema, increasing latency, or raising cost. Traditional software tests alone do not capture those behavioral regressions.

![AI Workflow Regression Gate architecture](https://raw.githubusercontent.com/ohjeffkuston/ai-workflow-regression-gate/main/docs/architecture.png)

## The problem: AI behavior changes even when the code still runs

An AI workflow can return HTTP 200 and still be operationally broken. The answer may omit a required action. A structured field may disappear. A forbidden term may leak into the response. The new version may be slower or more expensive than the baseline.

When those checks are informal, teams rely on manual spot checks and production feedback. That is difficult to audit and impossible to repeat consistently.

## A deterministic gate around probabilistic systems

I built **AI Workflow Regression Gate** to evaluate recorded baseline and candidate runs before release. It does not call a model. Instead, it consumes explicit fixtures and applies version-controlled policy.

For each case, the gate evaluates:

- coverage of expected terms;
- forbidden content;
- required response-schema keys;
- quality drop from the baseline;
- latency increase;
- cost increase.

The output is an explainable `PASS`, `REVIEW`, or `BLOCK` decision with case-level findings.

## Why offline fixtures matter

Running evaluation against recorded fixtures makes the result deterministic, fast, inexpensive, and safe for CI. It also avoids placing production data or API keys inside the test process.

The safety boundary is deliberate:

- no LLM call;
- no workflow deployment;
- no infrastructure mutation;
- human approval for every non-passing decision.

## Integrating the gate with n8n and CI/CD

The repository includes an inactive n8n workflow that accepts a regression suite through a webhook, runs the local evaluator, and routes the result. Passing changes can proceed to the next release step. `REVIEW` and `BLOCK` results stop for human judgment.

GitHub Actions runs the same unit tests and validates the example and n8n JSON artifacts. The engine fails closed when input is malformed or case identifiers are duplicated.

## What this project demonstrates

This is a small implementation of a larger platform-engineering principle: probabilistic components still need deterministic operational controls.

The project demonstrates AI orchestration, test automation, model-independent evaluation, CI/CD integration, n8n workflow design, cost and latency governance, and human-in-the-loop release control.

The question is not whether AI workflows will change. They will. The question is whether the organization can prove that each change is safe enough to release.

The source code, test suite, architecture diagram, Docker image definition, and n8n workflow are available on GitHub:

https://github.com/ohjeffkuston/ai-workflow-regression-gate

