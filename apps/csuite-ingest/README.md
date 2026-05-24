# csuite-ingest (M10 V2 ingests)

Read-only connectors that pull the V2 visibility gaps into the self-hosted
Supabase so the C-Suite agents can see them through the Data Brain MCP. A batch
worker, not a service: a host cron runs it; one source failing never blocks the
rest.

## Sources

| Connector | Table | Source | Credential |
|---|---|---|---|
| `email_engagement` | `email_engagement` | sending platform | `EMAIL_ENGAGEMENT_*` |
| `support_tickets` | `support_tickets` | helpdesk | `SUPPORT_TICKETS_*` |
| `churn_reasons` | `churn_reasons` | billing / survey | `CHURN_*` |
| `content_calendar` | `content_calendar` | calendar tool | `CONTENT_CALENDAR_*` |
| `webinar_metrics` | `webinar_metrics` | webinar tool | `WEBINAR_*` |
| `nps_feedback` | `nps_feedback` | survey tool | `NPS_*` |
| `audit_feed` | `audit_feed` | internal (dispatch + audit_log) | none |

The normalized columns are fixed in `db/migrations/0003_v2_ingest.sql`. Only each
connector's `fetch()` is source-specific; `normalize()` and the FAKE fixture are
already done, so the schema is locked and tested before a tool is wired.

## Design

```
source SaaS ──fetch()──▶ raw ──normalize()──▶ rows ──upsert(pk)──▶ Supabase
                                                          (service role)
```

- `base.Connector` is the contract: `table`, `columns`, `pk`, `source`,
  `normalize()`, `fake_raw()`, and `fetch()` (or `read_source()` for internal).
- `runner.run()` fans out over `connectors.REGISTRY`, validates each row against
  the declared columns, and upserts. Failures are isolated per connector.
- `store.SupabaseStore` upserts via PostgREST with `resolution=merge-duplicates`;
  `FakeStore` is the in-memory CI double.

## Run

```bash
# All sources, against the live Supabase:
docker compose -p csuite --env-file <csuite.env> \
  -f infra/docker-compose.ingest.yml run --rm csuite-ingest

# A subset:
... run --rm csuite-ingest audit_feed nps_feedback
```

## Test

```bash
uv sync --extra dev && uv run pytest   # FAKE mode, no network, no creds; >=90% cov
```

## Adding / wiring a source

1. Confirm the tool and add `<SRC>_PROVIDER` / `<SRC>_API_KEY` to `csuite.env`.
2. Implement that connector's `fetch(env)` against the tool's API.
3. The normalized schema and tests already exist; extend `fake_raw()` if needed.
