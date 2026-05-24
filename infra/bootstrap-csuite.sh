#!/usr/bin/env bash
#
# bootstrap-csuite.sh - stand up the ISOLATED Vox Horizon C-Suite stack.
#
# Run AS ROOT on the existing VPS. Idempotent. This script ONLY ever writes
# under /opt/voxhorizon-csuite and /home/csuite, uses its own docker compose
# projects (csuite, csuite-supabase) and its own network (csuite_net). It never
# touches /opt/voxhorizon, the production containers, or production networks.
#
# Modes:
#   (default)     full bootstrap: user, dirs, supabase clone, secrets, up
#   --dry-run     do everything except docker pull/build/up and migrations
#   migrate       apply the Data Brain SQL migrations to the self-hosted DB
#   --help
#
set -euo pipefail

# --- fixed, isolated paths (refuse to run against production root) ---
CSUITE_USER="csuite"
ROOT="${CSUITE_ROOT:-/opt/voxhorizon-csuite}"
REPO_DIR="${ROOT}/repo"                     # this License-and-Scale checkout
SUPA_SRC="${ROOT}/supabase-src"             # official supabase/supabase clone
SUPA_DIR="${SUPA_SRC}/docker"               # its docker compose dir
BUILD_DB="${ROOT}/build/data-brain"         # assembled Data Brain build context
AGENTS_ROOT="${ROOT}/agents"                # one data dir per Hermes agent
SECRETS_DIR="/home/${CSUITE_USER}/.config/voxhorizon-csuite"
ENV_FILE="${SECRETS_DIR}/csuite.env"
CSUITE_AGENTS="rex dash closer vault bob pulse"
SUPA_PROJECT="csuite-supabase"
OUR_PROJECT="csuite"
KONG_PORT="8100"
STUDIO_PORT="8101"

if [[ "${ROOT}" == "/opt/voxhorizon" ]]; then
  echo "refusing: ROOT must be the isolated /opt/voxhorizon-csuite" >&2; exit 1
fi

DRY_RUN=0
MODE="bootstrap"
case "${1:-}" in
  --help|-h) sed -n '1,30p' "$0"; exit 0 ;;
  --dry-run) DRY_RUN=1 ;;
  migrate)   MODE="migrate" ;;
  "")        ;;
  *) echo "unknown arg: $1 (see --help)" >&2; exit 2 ;;
esac

say() { echo; echo "=== $* ==="; }
need_root() { [[ "${EUID}" -eq 0 ]] || { echo "run as root" >&2; exit 1; }; }

# Where this script lives (so we can copy our scaffold files).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- JWT generation for self-hosted Supabase anon/service keys ---
# Builds an HS256 JWT signed with JWT_SECRET, no external deps (pure python3).
gen_jwt() {
  local role="$1" secret="$2"
  python3 - "$role" "$secret" <<'PY'
import sys, json, time, hmac, hashlib, base64
role, secret = sys.argv[1], sys.argv[2]
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
header = b64(json.dumps({"alg":"HS256","typ":"JWT"},separators=(',',':')).encode())
now = int(time.time())
payload = b64(json.dumps({"role":role,"iss":"supabase","iat":now,"exp":now+10*365*24*3600},separators=(',',':')).encode())
signing = f"{header}.{payload}".encode()
sig = b64(hmac.new(secret.encode(), signing, hashlib.sha256).digest())
print(f"{header}.{payload}.{sig}")
PY
}

rand_hex() { python3 -c "import secrets;print(secrets.token_hex($1))"; }

# ---------------------------------------------------------------------------
migrate_only() {
  need_root
  say "Applying Data Brain migrations to self-hosted Supabase DB"
  local db_container
  db_container="$(docker ps --filter "name=${SUPA_PROJECT}" --filter "name=db" --format '{{.Names}}' | head -1)"
  if [[ -z "${db_container}" ]]; then
    echo "could not find the supabase db container for project ${SUPA_PROJECT}." >&2
    echo "bring supabase up first, or run migrations from Studio at 127.0.0.1:${STUDIO_PORT}." >&2
    exit 1
  fi
  local m
  for m in "${REPO_DIR}"/business-data-brain-template/supabase/migrations/*.sql; do
    echo "  -> $(basename "$m")"
    docker exec -i "${db_container}" psql -U postgres -d postgres < "$m"
  done
  echo "ok: migrations applied"
  exit 0
}
if [[ "${MODE}" == "migrate" ]]; then migrate_only; fi

# Dry run: validate, print the plan, and exit WITHOUT writing anything. Runs
# without root so it is safe in CI (M1-1 contract: --dry-run writes nothing).
if [[ "${DRY_RUN}" -eq 1 ]]; then
  say "DRY RUN: plan for the isolated C-Suite under ${ROOT} (no changes made)"
  echo "[dry-run] create user ${CSUITE_USER}; dirs under ${ROOT}, ${SECRETS_DIR}, ${AGENTS_ROOT}"
  echo "[dry-run] clone self-hosted Supabase; generate secrets; render ${ENV_FILE}"
  echo "[dry-run] assemble Data Brain build; create the csuite_readonly role"
  echo "[dry-run] docker compose up: csuite + hermes; sync agent profiles"
  exit 0
fi

# ---------------------------------------------------------------------------
need_root

say "1. csuite user + docker group + linger"
if ! id "${CSUITE_USER}" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "${CSUITE_USER}"
  echo "ok: created user ${CSUITE_USER}"
else
  echo "ok: user ${CSUITE_USER} exists"
fi
if getent group docker >/dev/null 2>&1; then
  usermod -aG docker "${CSUITE_USER}"; echo "ok: ${CSUITE_USER} in docker group"
fi
loginctl enable-linger "${CSUITE_USER}" 2>/dev/null || true

say "2. isolated directories"
mkdir -p "${ROOT}" "${BUILD_DB}" "${SECRETS_DIR}" "${AGENTS_ROOT}"
for a in ${CSUITE_AGENTS}; do mkdir -p "${AGENTS_ROOT}/${a}/data"; done
chown -R "${CSUITE_USER}:${CSUITE_USER}" "${ROOT}" "/home/${CSUITE_USER}/.config"
# Hermes runs as uid/gid 10000 inside the container; its bind-mounted data dirs
# must be writable by that uid.
chown -R 10000:10000 "${AGENTS_ROOT}"
chmod 700 "${SECRETS_DIR}"
echo "ok: ${ROOT}, ${SECRETS_DIR}, agent data dirs under ${AGENTS_ROOT}"

say "3. expect this repo at ${REPO_DIR}"
if [[ ! -d "${REPO_DIR}/business-data-brain-template" ]]; then
  echo "note: ${REPO_DIR} does not contain License-and-Scale yet." >&2
  echo "      place this folder there (git clone or copy) and re-run." >&2
  [[ "${DRY_RUN}" -eq 0 ]] && exit 1
fi

say "4. clone official self-hosted Supabase (docker)"
if [[ ! -d "${SUPA_DIR}" ]]; then
  command -v git >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y --no-install-recommends git; }
  git clone --depth 1 https://github.com/supabase/supabase "${SUPA_SRC}"
  echo "ok: cloned supabase -> ${SUPA_SRC}"
else
  echo "ok: ${SUPA_DIR} present"
fi
chown -R "${CSUITE_USER}:${CSUITE_USER}" "${SUPA_SRC}"

say "5. generate secrets + render env files"
if [[ -f "${ENV_FILE}" ]]; then
  echo "ok: ${ENV_FILE} exists - leaving in place (delete it to regenerate)"
else
  PG_PW="$(rand_hex 24)"
  JWT="$(rand_hex 40)"
  ANON_KEY="$(gen_jwt anon "${JWT}")"
  SERVICE_KEY="$(gen_jwt service_role "${JWT}")"
  DASH_PW="$(rand_hex 16)"
  AUTH_PASS="$(rand_hex 12)"
  AUTH_SECRET="$(rand_hex 24)"
  RO_PW="$(rand_hex 16)"

  # Render csuite.env from the example, filling generated values.
  sed \
    -e "s|^SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=${SERVICE_KEY}|" \
    -e "s|^NEXT_PUBLIC_SUPABASE_ANON_KEY=.*|NEXT_PUBLIC_SUPABASE_ANON_KEY=${ANON_KEY}|" \
    -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${PG_PW}|" \
    -e "s|^JWT_SECRET=.*|JWT_SECRET=${JWT}|" \
    -e "s|^SUPABASE_DASHBOARD_PASSWORD=.*|SUPABASE_DASHBOARD_PASSWORD=${DASH_PW}|" \
    -e "s|^DASHBOARD_AUTH_PASS=.*|DASHBOARD_AUTH_PASS=${AUTH_PASS}|" \
    -e "s|^DASHBOARD_AUTH_SECRET=.*|DASHBOARD_AUTH_SECRET=${AUTH_SECRET}|" \
    -e "s|csuite_readonly:CHANGE_ME@|csuite_readonly:${RO_PW}@|" \
    "${SCRIPT_DIR}/.env.csuite.example" > "${ENV_FILE}"
  chown "${CSUITE_USER}:${CSUITE_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "ok: wrote ${ENV_FILE} (chmod 600). FILL MC_AUTH_PASS / MC_AUTH_SECRET / CSUITE_DISPATCHER_SECRET."

  # Mirror the matching secrets into the Supabase stack .env.
  if [[ -f "${SUPA_DIR}/.env.example" ]]; then
    cp "${SUPA_DIR}/.env.example" "${SUPA_DIR}/.env"
    sed -i \
      -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${PG_PW}|" \
      -e "s|^JWT_SECRET=.*|JWT_SECRET=${JWT}|" \
      -e "s|^ANON_KEY=.*|ANON_KEY=${ANON_KEY}|" \
      -e "s|^SERVICE_ROLE_KEY=.*|SERVICE_ROLE_KEY=${SERVICE_KEY}|" \
      -e "s|^DASHBOARD_USERNAME=.*|DASHBOARD_USERNAME=${CSUITE_USER}|" \
      -e "s|^DASHBOARD_PASSWORD=.*|DASHBOARD_PASSWORD=${DASH_PW}|" \
      -e "s|^KONG_HTTP_PORT=.*|KONG_HTTP_PORT=${KONG_PORT}|" \
      -e "s|^STUDIO_PORT=.*|STUDIO_PORT=${STUDIO_PORT}|" \
      "${SUPA_DIR}/.env"
    chown "${CSUITE_USER}:${CSUITE_USER}" "${SUPA_DIR}/.env"
    chmod 600 "${SUPA_DIR}/.env"
    echo "ok: wrote ${SUPA_DIR}/.env (Kong on ${KONG_PORT})"
    echo "    NOTE: review API_EXTERNAL_URL / SITE_URL / SUPABASE_PUBLIC_URL in that"
    echo "    file and set them to the Tailscale-served Kong URL before browser use."
  fi
fi

say "6. assemble Data Brain build context"
cp -r "${REPO_DIR}/business-data-brain-template/." "${BUILD_DB}/"
rm -rf "${BUILD_DB}/.git"
cp "${SCRIPT_DIR}/data-brain.Dockerfile" "${BUILD_DB}/Dockerfile"
cp "${SCRIPT_DIR}/data-brain.dockerignore" "${BUILD_DB}/.dockerignore"
# Place our compose where docker compose will run from.
cp "${SCRIPT_DIR}/docker-compose.csuite.yml" "${ROOT}/docker-compose.csuite.yml"
chown -R "${CSUITE_USER}:${CSUITE_USER}" "${ROOT}"
echo "ok: ${BUILD_DB} ready"

say "7. stage Hermes compose (agent data dirs were created in step 2)"
cp "${SCRIPT_DIR}/docker-compose.hermes.yml" "${ROOT}/docker-compose.hermes.yml"
chown "${CSUITE_USER}:${CSUITE_USER}" "${ROOT}/docker-compose.hermes.yml"
echo "ok: agent data dirs under ${AGENTS_ROOT}; SOUL.md + skills are pushed later by hermes/sync-csuite.sh"

say "8. bring up self-hosted Supabase (project ${SUPA_PROJECT})"
sudo -u "${CSUITE_USER}" -H sh -c "cd '${SUPA_DIR}' && docker compose -p '${SUPA_PROJECT}' pull && docker compose -p '${SUPA_PROJECT}' up -d"

say "9. apply Data Brain migrations"
bash "$0" migrate || echo "warn: migrations step reported an issue - run '$0 migrate' after Supabase is healthy"

say "10. build + up the Data Brain (project ${OUR_PROJECT}, creates csuite_net)"
sudo -u "${CSUITE_USER}" -H sh -c "cd '${ROOT}' && docker compose -p '${OUR_PROJECT}' --env-file '${ENV_FILE}' -f docker-compose.csuite.yml up -d --build"

say "11. create the read-only DB role for the Data-Brain MCP"
RO_DSN="$(grep -E '^CSUITE_DB_DSN=' "${ENV_FILE}" | cut -d= -f2- || true)"
RO_PW_VAL="$(printf '%s' "${RO_DSN}" | sed -E 's|.*//csuite_readonly:([^@]*)@.*|\1|')"
DB_C="$(docker ps --filter "name=${SUPA_PROJECT}" --filter "name=db" --format '{{.Names}}' | head -1)"
if [[ -n "${DB_C}" && -n "${RO_PW_VAL}" && "${RO_PW_VAL}" != "CHANGE_ME" ]]; then
  docker exec -i "${DB_C}" psql -U postgres -d postgres <<SQL || echo "warn: readonly role step had issues"
do \$\$ begin
  if not exists (select from pg_roles where rolname = 'csuite_readonly') then
    create role csuite_readonly login password '${RO_PW_VAL}';
  else
    alter role csuite_readonly password '${RO_PW_VAL}';
  end if;
end \$\$;
grant connect on database postgres to csuite_readonly;
grant usage on schema public to csuite_readonly;
grant select on all tables in schema public to csuite_readonly;
alter default privileges in schema public grant select on tables to csuite_readonly;
SQL
  echo "ok: csuite_readonly role ready"
else
  echo "warn: skipped readonly role (db container not found or DSN password unset)"
fi

say "12. bring up the C-Suite Hermes agents (project ${OUR_PROJECT})"
sudo -u "${CSUITE_USER}" -H sh -c "cd '${ROOT}' && docker compose -p '${OUR_PROJECT}' --env-file '${ENV_FILE}' -f docker-compose.hermes.yml up -d" \
  || echo "warn: not all Hermes agents started - verify the public image run contract via 'docker inspect' (see docker-compose.hermes.yml header)"

say "13. push agent profiles into the agent data dirs"
bash "${SCRIPT_DIR}/hermes/sync-csuite.sh" --apply --restart \
  || echo "warn: sync reported issues (commonly: missing Codex auth.json - see csuite.env CODEX_AUTH_JSON_SRC)"

say "Done"
cat <<EOF

  C-Suite stack is up, isolated from production (Hermes runtime, passive agents).

  Next:
    1. Edit ${ENV_FILE}: set MC_AUTH_PASS, MC_AUTH_SECRET, CSUITE_DISPATCHER_SECRET.
    2. Provide the Codex/ChatGPT OAuth token once, point CODEX_AUTH_JSON_SRC at it
       in ${ENV_FILE}, then: bash ${SCRIPT_DIR}/hermes/sync-csuite.sh --apply --restart
       (OpenAI is reached via this subscription only - no OpenRouter, no API key.)
    3. Patch each agent's config.yaml per ${SCRIPT_DIR}/hermes/config.csuite.patch.md
       (scrub OpenRouter, set provider openai-codex, wire the data-brain MCP,
       channels empty - the agents are passive and driven by Mission Control).
    4. Expose Mission Control over Tailscale Serve (private):
         tailscale serve --bg --https=8443 http://127.0.0.1:3100        # Mission Control
         tailscale serve --bg --https=8543 http://127.0.0.1:${KONG_PORT}  # Supabase API
       Then set NEXT_PUBLIC_SUPABASE_URL in ${ENV_FILE} to the Supabase https URL
       and rebuild: docker compose -p ${OUR_PROJECT} -f ${ROOT}/docker-compose.csuite.yml up -d --build
    5. Open Mission Control and drive the agents from there (no Telegram).

EOF
