#!/usr/bin/env bash
set -euo pipefail

ai_team_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "${script_dir}/.." && pwd)
}

ai_team_timestamp() {
  date +"%Y%m%d-%H%M%S"
}

ai_team_get_config_field() {
  local json_path="$1"
  python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))
cur = cfg
for part in "${json_path}".split("."):
    cur = cur[part]
print(cur)
PY
}

ai_team_log_base_dir() {
  ai_team_get_config_field "logging.dir"
}

ai_team_redact_file() {
  local in_file="$1"
  local out_file="$2"
  python3 - <<'PY' "$in_file" "$out_file"
import json
import re
import sys
from pathlib import Path

in_file = Path(sys.argv[1])
out_file = Path(sys.argv[2])

cfg = json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))
redactions = cfg["logging"]["redactions"]
text = in_file.read_text(encoding="utf-8", errors="replace")

if not redactions.get("enabled", False):
    out_file.write_text(text, encoding="utf-8")
    sys.exit(0)

patterns = redactions.get("patterns", [])
try:
    for pat in patterns:
        text = re.sub(pat, "***REDACTED***", text)
except re.error as e:
    print(f"REDACTION_REGEX_ERROR: {e}", file=sys.stderr)
    sys.exit(2)

out_file.write_text(text, encoding="utf-8")
print("REDACTION_OK")
PY
}

ai_team_run_logged() {
  local gate_name="$1"
  shift

  local repo_root
  repo_root="$(ai_team_repo_root)"
  export XDG_DATA_HOME="${repo_root}/.cache/xdg-data"
  export XDG_CACHE_HOME="${repo_root}/.cache/xdg-cache"
  export XDG_CONFIG_HOME="${repo_root}/.cache/xdg-config"
  export PNPM_HOME="${XDG_DATA_HOME}/pnpm"
  mkdir -p "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$PNPM_HOME"

  local todo_id="${AI_TEAM_TODO_ID:-system}"
  local run_id="${AI_TEAM_RUN_ID:-$(ai_team_timestamp)}"
  local log_base
  log_base="$(ai_team_log_base_dir)"

  local log_dir
  log_dir="${log_base}/${todo_id}/${run_id}/gates"
  mkdir -p "$log_dir"

  local tmp_file
  tmp_file="$(mktemp)"

  set +e
  "$@" >"$tmp_file" 2>&1
  local exit_code=$?
  set -e

  local log_file="${log_dir}/${gate_name}.log"
  local redact_tmp
  redact_tmp="$(mktemp)"
  ai_team_redact_file "$tmp_file" "$redact_tmp" >/dev/null 2>&1 || {
    rm -f "$tmp_file" "$redact_tmp"
    echo "GATE ${gate_name} FAIL (redaction) log=${log_file}"
    return 2
  }
  mv "$redact_tmp" "$log_file"
  rm -f "$tmp_file"

  if [[ $exit_code -eq 0 ]]; then
    echo "GATE ${gate_name} PASS log=${log_file}"
  else
    echo "GATE ${gate_name} FAIL log=${log_file}"
  fi

  return "$exit_code"
}
