# ADR-003: LangGraph for Agent Workflow Orchestration

## Context
Complex research queries require multi-step planning, domain-specific retrieval, evidence validation, structured judgment, deterministic calculation, and synthesis.

## Problem
Selecting an agent orchestration framework that guarantees state persistence, inspectable nodes, bounded iterative loops, and predictable error handling.

## Options Considered
1. **Unstructured AutoGen / CrewAI / ReAct loops**: Hard to bound, non-deterministic transitions, high token drift, risk of runaway executions.
2. **LangGraph StateGraph**: Explicit state schema (`ResearchState`), clear edge conditions, cyclable with configurable iteration limits (`MAX_RESEARCH_ITERATIONS`), and native LangSmith tracing.

## Decision
Adopt **LangGraph** with an explicit state graph for research workflow execution.

## Why
LangGraph treats workflows as state machines. Every node execution is deterministic in its transitions, bounded by explicit budgets (`MAX_TOOL_CALLS`, `MAX_RESEARCH_ITERATIONS`, and wall-clock deadlines), and can broadcast progress events over Redis Pub/Sub.

## Trade-offs
Requires declaring typed state dictionaries and explicit edge functions rather than allowing an LLM to freely decide arbitrary actions.

## Consequences
Agents cannot execute arbitrary tools or spin in unbounded loops. All state mutations are audited and emitted as progress events.

## Revisit Conditions
If sub-tasks require dynamic autonomous sub-agent swarms that cannot be modeled as a directed cyclical graph.
