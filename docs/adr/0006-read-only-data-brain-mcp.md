# ADR 0006: Agents read business data only through a read-only MCP

- Status: Accepted
- Date: 2026-05-23

## Context

Agents must see the whole business but must not be able to mutate it, especially
given that they ingest untrusted content (transcripts, lead notes, ad copy) that
could carry prompt injection. The Data Brain holds all business data in Supabase.

## Decision

Agents read business truth only through a read-only Data Brain MCP server with a
five-layer guard: a tool vocabulary of read-only tools; a read-only transaction
per query; a single SELECT/WITH only with a DML denylist; a row cap and statement
timeout; and a SELECT-only Postgres role (`csuite_readonly`) as the outermost
guard. Agents never call source SaaS APIs directly for writes.

## Consequences

A prompt-injected agent cannot write or delete by construction. The SQL guard is
gated by golden allow/deny evals (C3) and the prompt-injection fixture (C8). V1
agents have no write tools at all; any future write is a separate, gated decision.
