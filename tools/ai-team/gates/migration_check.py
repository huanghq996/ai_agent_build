import json
import re
import sys
from pathlib import Path


def load_config() -> dict:
  return json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))


def strip_sql_comments(sql: str) -> str:
  sql = re.sub(r"/\\*.*?\\*/", "", sql, flags=re.S)
  sql = re.sub(r"--.*?$", "", sql, flags=re.M)
  return sql


def main() -> int:
  cfg = load_config()
  migrations = cfg["migrations"]
  if not migrations.get("enabled", False):
    print("MIGRATION_CHECK_SKIP")
    return 0

  location = Path(migrations["location"])
  if not location.exists():
    print(f"MIGRATION_DIR_MISSING: {location}")
    return 1

  pattern = re.compile(migrations["naming"]["pattern"])
  rules = migrations["rules"]
  no_out_of_order = bool(rules.get("noOutOfOrder", True))
  no_repeatable = bool(rules.get("noRepeatable", True))
  non_empty_sql = bool(rules.get("nonEmptySql", True))

  sql_files = sorted([p for p in location.iterdir() if p.is_file() and p.suffix == ".sql"])
  failures: list[str] = []

  timestamps: list[str] = []
  seen_ts: set[str] = set()

  for p in sql_files:
    name = p.name
    if no_repeatable and name.startswith("R__"):
      failures.append(f"REPEATABLE_FORBIDDEN:{name}")
      continue
    m = pattern.match(name)
    if not m:
      failures.append(f"FILENAME_PATTERN_MISMATCH:{name}")
      continue
    ts = name[1:15]
    if ts in seen_ts:
      failures.append(f"TIMESTAMP_DUPLICATE:{ts}")
    seen_ts.add(ts)
    timestamps.append(ts)

    if non_empty_sql:
      content = p.read_text(encoding="utf-8", errors="replace")
      stripped = strip_sql_comments(content).strip()
      if not stripped:
        failures.append(f"EMPTY_SQL:{name}")

  if no_out_of_order and timestamps:
    sorted_ts = sorted(timestamps)
    if sorted_ts != timestamps:
      failures.append("TIMESTAMP_OUT_OF_ORDER")

  if failures:
    print("MIGRATION_RULES_FAIL")
    for f in failures:
      print(f" - {f}")
    return 1

  print("MIGRATION_OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

