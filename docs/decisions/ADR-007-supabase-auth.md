# ADR-007: Supabase Auth with Local JWKS Verification

## Context
FinSight requires multi-tenant user authentication (email/password, Google OAuth, session management).

## Problem
Balancing fast time-to-market against vendor lock-in and request latency.

## Options Considered
1. **Custom Auth from Scratch**: High development and maintenance cost, security risk regarding password hashing, session revocation, and OAuth flows.
2. **Supabase Auth with per-request remote validation**: Easy to configure, but creates a runtime network dependency and latency bottleneck on every API call.
3. **Supabase Auth with local JWKS token verification**: Leverages Supabase for user signup/login while FastAPI validates JWTs locally against cached JWKS public keys without network hops.

## Decision
Use **Supabase Auth** with local JWKS (JSON Web Key Set) signature verification in FastAPI.

## Why
Offloads identity management, password resets, and OAuth to an established provider while keeping API request latency low and avoiding an external availability dependency on every authenticated call.

## Trade-offs
Vendor tie to Supabase's user store, though mitigated by Supabase's open standard JWT format and user export capabilities.

## Consequences
The `users` table maintains an `auth_provider` column to support potential migrations in the future.

## Revisit Conditions
If multi-tenant enterprise SAML or on-premise authentication becomes a primary requirement.
