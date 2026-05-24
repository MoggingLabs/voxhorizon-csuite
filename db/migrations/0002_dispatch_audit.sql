-- 0002_dispatch_audit.sql
-- C-Suite-owned tables: dispatch (one row per agent dispatch) and audit_log
-- (every action). RLS deny-all; only the service role (BYPASSRLS, used by the
-- dispatcher and Mission Control behind the auth gate) reads/writes. Controls
-- C7, C10. Forward-only and idempotent.

create table if not exists dispatch (
  id uuid primary key,
  agent text not null,
  prompt text,
  requested_by text,
  status text not null default 'running',
  result_ref text,
  created_at timestamptz not null default now(),
  finished_at timestamptz
);

create table if not exists audit_log (
  id bigserial primary key,
  actor text not null,
  action text not null,
  target text,
  detail text,
  created_at timestamptz not null default now()
);

-- Deny-all: enable RLS and define no policies, so anon/authenticated have no
-- access. The service role bypasses RLS.
alter table dispatch enable row level security;
alter table audit_log enable row level security;

revoke all on dispatch from anon, authenticated;
revoke all on audit_log from anon, authenticated;
