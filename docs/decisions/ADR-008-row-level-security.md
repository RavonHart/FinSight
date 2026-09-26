# ADR-008: Defense-in-Depth Row-Level Security (RLS)

## Context
Financial records, portfolio holdings, personal profiles, and research projects must never leak across user boundaries.

## Problem
Application-level ownership checks (`WHERE user_id = :current_user_id`) are standard, but a single accidental omission in a complex query creates a catastrophic multi-tenant data leak.

## Options Considered
1. **Application-Only Checks**: Fast to implement initially, but zero defense if a developer forgets a filter or a library behaves unexpectedly.
2. **Database Row-Level Security (RLS)**: Enforced directly inside PostgreSQL policies; active transaction session variables (`app.current_user_id`) restrict query visibility automatically.

## Decision
Enforce **Row-Level Security (RLS)** as a defense-in-depth boundary on all user-owned tables in PostgreSQL alongside application-level verification.

## Why
Financial data requires zero-tolerance isolation. With RLS, even if an application endpoint omits a filter, PostgreSQL refuses to return or mutate rows belonging to another user.

## Trade-offs
Database connections must set the session user ID (`SET LOCAL app.current_user_id = :user_id`) at transaction start.

## Consequences
Migrations include `ENABLE ROW LEVEL SECURITY` and policy definitions for all user-owned tables. Service role / migrations can bypass via superuser/admin credentials.

## Revisit Conditions
None; mandatory for financial multi-tenancy.
