# ADR-004: Jev / TypeSafe AI for Structured Financial Judgment

## Context
Financial risk scoring, profile classification, and evidence sufficiency assessments require calibrated, structured judgment rather than unconstrained narrative text.

## Problem
Free-form LLM outputs hallucinate, suffer from formatting drift, fail to provide calibrated confidence intervals, and resist reliable programmatic routing.

## Options Considered
1. **Regex / Prompt Parsing of LLM Text**: Brittle, prone to sudden parsing errors when prompts change or models update.
2. **Jev / TypeSafe AI System One**: Typed schemas, explicit choice/score distributions, calibrated confidence scores, and discrete routing thresholds.

## Decision
Adopt **Jev / TypeSafe AI** as the structured judgment layer for financial profiling and research evaluation.

## Why
Jev returns strongly typed evaluations with confidence metrics. Workflows can deterministically route based on configurable confidence thresholds (high confidence -> proceed; medium -> gather more evidence; low -> surface uncertainty).

## Trade-offs
Questions must be formally authored in a question registry with explicit input/output schemas rather than improvised on-the-fly.

## Consequences
No financial classification or quality gate relies on parsing unstructured conversational LLM output.

## Revisit Conditions
If a domain requires purely open-ended creative narrative where calibrated categorical/numerical judgment is not applicable.
