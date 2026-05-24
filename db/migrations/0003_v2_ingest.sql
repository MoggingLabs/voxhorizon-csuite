-- 0003_v2_ingest.sql
-- M10 V2 visibility gaps: business-data tables the C-Suite ingests pull into the
-- self-hosted Supabase so agents can read them through the Data Brain MCP.
--
-- Security shape (per table):
--   * service role (BYPASSRLS) writes, used only by the ingest worker server-side.
--   * csuite_readonly (the MCP role from 0001) may SELECT: explicit grant + an
--     RLS policy scoped to that role. This is business data the agents read.
--   * anon / authenticated (the public PostgREST surface) get nothing: RLS is on,
--     their grants are revoked, and no policy names them (control C7).
-- Forward-only and idempotent: safe to re-apply.

create table if not exists email_engagement (
  id text primary key,
  source text not null,
  contact_email text,
  campaign text,
  event_type text,            -- sent | delivered | open | click | bounce | unsub | reply
  subject text,
  occurred_at timestamptz,
  meta jsonb,
  ingested_at timestamptz not null default now()
);

create table if not exists support_tickets (
  id text primary key,
  source text not null,
  requester_email text,
  subject text,
  status text,                -- open | pending | solved | closed
  priority text,
  channel text,
  assignee text,
  created_at timestamptz,
  updated_at timestamptz,
  first_response_at timestamptz,
  resolved_at timestamptz,
  satisfaction text,
  tags jsonb,
  ingested_at timestamptz not null default now()
);

create table if not exists churn_reasons (
  id text primary key,
  source text not null,
  account text,
  customer_email text,
  plan text,
  mrr_lost numeric,
  reason_category text,
  reason_text text,
  canceled_at timestamptz,
  tenure_days integer,
  ingested_at timestamptz not null default now()
);

create table if not exists content_calendar (
  id text primary key,
  source text not null,
  title text,
  channel text,               -- blog | youtube | ig | tiktok | email | x | linkedin
  status text,                -- idea | draft | scheduled | published
  owner text,
  scheduled_for timestamptz,
  published_at timestamptz,
  url text,
  tags jsonb,
  ingested_at timestamptz not null default now()
);

create table if not exists webinar_metrics (
  id text primary key,
  source text not null,
  webinar_title text,
  scheduled_for timestamptz,
  registrants integer,
  attendees integer,
  attendance_rate numeric,
  avg_watch_minutes numeric,
  replay_views integer,
  conversions integer,
  revenue numeric,
  ingested_at timestamptz not null default now()
);

create table if not exists nps_feedback (
  id text primary key,
  source text not null,
  respondent_email text,
  score integer,              -- 0..10
  category text,              -- promoter | passive | detractor
  comment text,
  survey text,
  submitted_at timestamptz,
  ingested_at timestamptz not null default now()
);

-- Internal compliance feed: consolidates the C-Suite's own dispatch + audit_log
-- (and future events) into one queryable timeline. Needs no external credential.
create table if not exists audit_feed (
  id text primary key,
  occurred_at timestamptz,
  actor text,
  action text,
  target text,
  source_table text,          -- dispatch | audit_log
  detail text,
  ingested_at timestamptz not null default now()
);

-- Lock down every ingest table the same way.
do $$
declare t text;
begin
  foreach t in array array[
    'email_engagement','support_tickets','churn_reasons','content_calendar',
    'webinar_metrics','nps_feedback','audit_feed'
  ]
  loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from anon, authenticated', t);
    execute format('grant select on %I to csuite_readonly', t);
    execute format('drop policy if exists %I on %I', t || '_csuite_read', t);
    execute format(
      'create policy %I on %I for select to csuite_readonly using (true)',
      t || '_csuite_read', t
    );
  end loop;
end
$$;
