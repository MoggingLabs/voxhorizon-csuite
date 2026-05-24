# Migrations

Forward-only, sequential SQL migrations for the C-Suite-owned tables (the
`dispatch` and `audit_log` tables, with RLS deny-all and service-role writes).
Added in M5-3. Naming: `NNNN_short_name.sql`. Never rewrite history; add a new
migration to fix.

The Data Brain read surface (`t01..t91`) is NOT migrated here; it comes from the
`business-data-brain-template` warehouse. See [../SCHEMA.md](../SCHEMA.md).
