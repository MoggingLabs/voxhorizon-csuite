# Database schema

Two surfaces: the read surface (the Data Brain warehouse the agents read) and the
C-Suite-owned tables (dispatch + audit) this repo creates with forward-only
migrations in `db/migrations/`.

## Read surface (Data Brain, read-only to agents)

Agents read these only through the SELECT-only `csuite_readonly` role via the
Data Brain MCP. This repo does not own or migrate these tables; they come from the
`business-data-brain-template` warehouse.

| Table | Holds | Source |
|---|---|---|
| t01_leads | canonical lead (name, source, stage) | GoHighLevel + Typeform + Slack |
| t02_ads | ad performance (spend, CPL, ROAS) | Meta Ads |
| t03_bookings | bookings, show status | Calendly |
| t04_no_shows_cancels | no-shows, cancellations | Calendly |
| t05_deals_closed | closed deals (cash, closer) | Slack new-clients + Calendly |
| t06_income_processors | payments | Whop, Fanbasis, Stripe |
| t07_expenses | bank, expenses by category | Mercury |
| t08_eod_reports | closer EOD reports | Slack |
| t09_clients | active client roster, CSM | Monday |
| t10_lead_scores | lead quality (0-10) | Claude scoring |
| t11_manychat_leads | IG DM opt-ins | ManyChat |
| t12_content_youtube .. t15_content_x | content performance | YouTube, IG, LinkedIn, X |
| t16_overrides | operator inline edits | UI |
| t17_call_recordings | transcripts + AI analysis | Grain + Fathom |
| t18_csm_actions | CSM action log | manual |
| t19_payment_notis | payment alerts | Slack |
| t20_slack_new_clients | raw new-client posts | Slack |
| t21_monthly_projections | targets vs actuals | manual + computed |
| t91_weekly_qualitative_cache | weekly themes | Claude |

V2 gaps (M10, not yet ingested anywhere): email engagement, support tickets,
churn reasons, content calendar, webinar metrics, NPS, an audit-log feed.

## C-Suite-owned tables (this repo migrates)

| Table | Purpose | Access |
|---|---|---|
| dispatch | one row per agent dispatch (agent, prompt, requested_by, started_at, finished_at, status, result_ref) | RLS deny-all; service-role writes; MC reads via gate |
| audit_log | every action (actor, action, target, detail, ts) | RLS deny-all; service-role writes |

## Roles and RLS

- `csuite_readonly`: SELECT on the read surface only. INSERT/UPDATE/DELETE/DDL all
  denied (proven by `sec_readonly_role_write_denied`). The MCP connects as this
  role.
- RLS deny-all on the C-Suite-owned tables; only the service role (behind the
  Mission Control gate and the dispatcher) writes (`sec_rls_deny_all`).
- Migrations are forward-only and sequential (`NNNN_*.sql`); do not rewrite
  history, add a new migration to fix.
