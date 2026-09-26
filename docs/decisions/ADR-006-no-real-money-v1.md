# ADR-006: Explicit Product Boundary — No Real-Money Execution in V1

## Context
FinSight provides investment research, financial education, portfolio analytics, and forward simulations.

## Problem
Determining whether V1 should include broker integrations, trade execution, or fund custody.

## Options Considered
1. **Direct Broker Execution / Trading**: Incurs intense regulatory requirements, SEC/FINRA/SEBI compliance burdens, complex security auditing, and severe financial liability.
2. **Research, Education, and Simulation Boundary (V1)**: Focus strictly on intelligence, manual/virtual portfolios, deterministic analytics, scenario modeling, and learning.

## Decision
FinSight V1 **strictly prohibits** broker execution, trade placement, autonomous buying/selling, or custody of client funds.

## Why
Ensures development velocity is focused on solving research provenance, structured AI judgments, and financial analytics without prematurely navigating broker broker-dealer regulations.

## Trade-offs
Users must record trades manually or use virtual portfolios for simulation.

## Consequences
All marketing, API contracts, UI copy, and system behaviors reflect educational and research guidance, never automated financial advice or direct execution.

## Revisit Conditions
Post-V1 phase when dedicated legal and compliance frameworks are established for broker-dealer API integration.
