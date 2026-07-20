# Findings

## 1. Direct external fusion worked

The completed direct-xAI replay exercised three independent panel calls, structured comparison, fresh synthesis, two exact-artifact reviews, usage/cost accounting, persistence, and response receipts. All seven requested and actual model IDs were exact `grok-4.5`; both reviewers passed the same synthesis hash.

The execution handoff remained fail-closed: it was ready for the host workflow but did not claim mutation authorization while host plan and pre-execution gates were still pending.

## 2. Native and direct model provenance differ usefully

Direct xAI returned exact `grok-4.5`. Native Grok Build was requested as `grok-4.5` at `high`, while telemetry named the served implementation `grok-4.5-build`. Recording both prevents a host build alias from being mistaken for a different user selection.

## 3. The failed native attempt found an invocation problem

The first native attempt allowed a tool path while limiting the agent to one turn. It consumed one call and stopped cancelled before a verdict turn. The second used a bounded tool-less prompt and ended normally with the required structured `pass`. The failure remains part of the cost record instead of being hidden as a warm-up.

## 4. Preflight failure is not provider quality

One direct attempt lacked the configured key and dispatched zero calls. Another encountered transport/DNS failure with no completed model call or recorded usage. Neither carries information about answer quality; both carry useful information about fail-closed diagnostics and attempt visibility.

## 5. Cross-model fusion remains unproven here

Different Grok 4.5 roles can disagree productively, but a one-family panel does not test the value of model-family diversity. OpenRouter was not funded and no optional GPT/Claude seat participated in this Grok-host campaign.
