#!/usr/bin/env bash
# sync-csuite.sh - push repo-managed agent profiles into the isolated C-Suite
# Hermes containers. Adapted from the production sync-operator.sh, scoped to OUR
# own csuite-hermes-* containers and OUR data dirs. Never touches production.
#
# Repo is the source of truth for each agent's SOUL.md + the shared data-brain
# MCP skill + the Codex auth.json. Like sync-operator.sh it NEVER touches the
# agent's config.yaml (patched once per config.csuite.patch.md), .env, sessions,
# state, or memories.
#
# Safe by design: DRY-RUN by default; --apply to write; backs up before apply;
# per-skill scoped rsync --delete (generic Hermes library skills untouched).
#
# Usage:
#   bash sync-csuite.sh                   # dry-run, all agents
#   bash sync-csuite.sh --apply           # write
#   bash sync-csuite.sh --apply --restart # write + restart each csuite agent
#   bash sync-csuite.sh --agent rex --apply
set -euo pipefail

REPO_CSUITE="${REPO_CSUITE:-/opt/voxhorizon-csuite/repo/_csuite}"
AGENTS_ROOT="${AGENTS_ROOT:-/opt/voxhorizon-csuite/agents}"
ENV_FILE="${ENV_FILE:-/home/csuite/.config/voxhorizon-csuite/csuite.env}"
OWNER="10000:10000"   # hermes uid/gid inside the data dir
APPLY=0; RESTART=0; ONLY_AGENT=""

AGENTS=(rex dash closer vault bob pulse)
EXCLUDES=(--exclude '__pycache__/' --exclude '*.pyc' --exclude 'tests/' --exclude '*.log')

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --restart) RESTART=1 ;;
    --agent) ONLY_AGENT="$2"; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
log() { printf '\n== %s ==\n' "$*"; }
DRY="--dry-run"; [ "$APPLY" -eq 1 ] && DRY=""

command -v rsync >/dev/null || { echo "rsync not installed" >&2; exit 1; }
[ -d "$REPO_CSUITE/hermes" ] || { echo "repo not found at $REPO_CSUITE" >&2; exit 1; }

# Codex auth.json source (the ChatGPT/Codex OAuth token shared by the agents).
CODEX_AUTH_JSON_SRC=""
[ -f "$ENV_FILE" ] && CODEX_AUTH_JSON_SRC="$(grep -E '^CODEX_AUTH_JSON_SRC=' "$ENV_FILE" | cut -d= -f2- || true)"

for a in "${AGENTS[@]}"; do
  [ -n "$ONLY_AGENT" ] && [ "$a" != "$ONLY_AGENT" ] && continue
  SOUL_SRC="$REPO_CSUITE/hermes/agents/$a/SOUL.md"
  DATA="$AGENTS_ROOT/$a/data"

  if [ ! -f "$SOUL_SRC" ]; then echo "skip $a: no SOUL.md yet ($SOUL_SRC)"; continue; fi
  $SUDO test -d "$DATA" || { echo "skip $a: data dir missing ($DATA) - run bootstrap first"; continue; }

  log "agent $a ${DRY:+(dry-run)}"

  # backup the repo-owned surface before writing
  if [ "$APPLY" -eq 1 ]; then
    TS="$(date -u +%Y%m%dT%H%M%SZ)"
    $SUDO mkdir -p /opt/voxhorizon-csuite/backups
    $SUDO tar czf "/opt/voxhorizon-csuite/backups/$a-presync-$TS.tar.gz" -C "$DATA" \
      SOUL.md skills/data-brain-mcp 2>/dev/null || echo "  (no prior surface to back up)"
  fi

  # SOUL.md
  if [ "$APPLY" -eq 1 ]; then $SUDO cp "$SOUL_SRC" "$DATA/SOUL.md"; else $SUDO diff -u "$DATA/SOUL.md" "$SOUL_SRC" 2>/dev/null || true; fi

  # shared data-brain MCP skill (scoped --delete inside the skill dir only)
  $SUDO mkdir -p "$DATA/skills/data-brain-mcp"
  $SUDO rsync -a --delete $DRY --itemize-changes "${EXCLUDES[@]}" \
    "$REPO_CSUITE/hermes/data-brain-mcp/" "$DATA/skills/data-brain-mcp/"

  # Codex auth.json (the subscription token) - never printed, just placed
  if [ -n "$CODEX_AUTH_JSON_SRC" ] && $SUDO test -f "$CODEX_AUTH_JSON_SRC"; then
    if [ "$APPLY" -eq 1 ]; then $SUDO cp "$CODEX_AUTH_JSON_SRC" "$DATA/auth.json"; echo "  auth.json placed"; else echo "  would place auth.json from $CODEX_AUTH_JSON_SRC"; fi
  else
    echo "  WARN: no Codex auth.json found (set CODEX_AUTH_JSON_SRC in csuite.env). Agent cannot reach OpenAI without it."
  fi

  if [ "$APPLY" -eq 1 ]; then
    $SUDO chown -R "$OWNER" "$DATA/SOUL.md" "$DATA/skills/data-brain-mcp" 2>/dev/null || true
    [ -f "$DATA/auth.json" ] && $SUDO chown "$OWNER" "$DATA/auth.json" || true
    if [ "$RESTART" -eq 1 ]; then
      log "restart csuite-hermes-$a"
      docker restart "csuite-hermes-$a" >/dev/null 2>&1 || echo "  (container csuite-hermes-$a not running yet)"
    fi
  fi
done

[ "$APPLY" -eq 0 ] && echo && echo "DRY-RUN complete. Re-run with --apply (optionally --restart)."
log done
