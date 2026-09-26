# ADR-002: PostgreSQL with pgvector for Relational and Vector Data

## Context
FinSight requires storage for structured financial entities (accounts, holdings, transactions) and semantic vector search for filings, research sources, and learning modules.

## Problem
Deciding whether to introduce a standalone vector database (e.g. Qdrant, Pinecone) alongside PostgreSQL or use PostgreSQL with `pgvector`.

## Options Considered
1. **Dedicated Vector Database (Qdrant/Pinecone/Milvus)**: Separate infrastructure, dual write consistency issues, independent backup management.
2. **PostgreSQL + pgvector**: Unified relational and vector storage, atomic transactions, unified backups, HNSW vector indexing.

## Decision
Adopt **PostgreSQL with the pgvector extension** as the single authoritative database for relational entities and document chunk embeddings.

## Why
Simplifies infrastructure dramatically, prevents dual-write inconsistencies, allows cross-joining embeddings directly with relational metadata (`source_id`, `learning_module_id`), and easily handles V1 document scale.

## Trade-offs
Dedicated vector engines may offer specialized hybrid indexing at tens of millions of vectors, but FinSight's V1 volume is well within pgvector's sweet spot.

## Consequences
Migrations must ensure `CREATE EXTENSION IF NOT EXISTS vector;` runs before vector columns are declared. `document_chunks` table includes `embedding_model` and `embedding_version` to track dimensionality and model lineage.

## Revisit Conditions
Vector index build times or vector query latency becoming a system-wide bottleneck under extreme corpus expansion (>5M chunks).
