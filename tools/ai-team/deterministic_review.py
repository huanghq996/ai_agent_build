import re
from pathlib import Path

import logging_utils


def _scan_web_axios_direct_imports() -> list[str]:
  violations: list[str] = []
  root = Path("apps/web")
  if not root.exists():
    return violations

  allowed = Path("apps/web/src/api/http.js").resolve()
  for p in root.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in (".js", ".vue"):
      continue
    if p.resolve() == allowed:
      continue
    text = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\\bfrom\\s+['\\\"]axios['\\\"]", text) or re.search(r"\\brequire\\(\\s*['\\\"]axios['\\\"]\\s*\\)", text):
      violations.append(str(p))
  return violations


def _scan_server_controller_import_mapper() -> list[str]:
  violations: list[str] = []
  root = Path("apps/server/src/main/java")
  if not root.exists():
    return violations

  for p in root.rglob("*.java"):
    if "/controller/" not in str(p).replace("\\\\", "/"):
      continue
    text = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\\bimport\\s+.*\\.mapper\\.", text):
      violations.append(str(p))
  return violations


def run_review(config: dict, todo_id: str, run_id: str) -> tuple[str, list[str], list[str]]:
  blockers: list[str] = []
  suggestions: list[str] = []

  web_violations = _scan_web_axios_direct_imports()
  if web_violations:
    blockers.append("WEB_AXIOS_DIRECT_IMPORT: " + ", ".join(sorted(web_violations)))

  server_violations = _scan_server_controller_import_mapper()
  if server_violations:
    blockers.append("SERVER_LAYER_VIOLATION_CONTROLLER_TO_MAPPER: " + ", ".join(sorted(server_violations)))

  result = "PASS" if not blockers else "FAIL"

  review_md = []
  review_md.append(f"# Review ({result})")
  review_md.append("")
  review_md.append(f"- TODO-ID: {todo_id}")
  review_md.append(f"- RUN: {run_id}")
  review_md.append("")
  review_md.append("## Blockers")
  review_md.extend([f"- {b}" for b in blockers] or ["- (none)"])
  review_md.append("")
  review_md.append("## Suggestions")
  review_md.extend([f"- {s}" for s in suggestions] or ["- (none)"])
  review_md.append("")

  out_path = logging_utils.log_path(config, todo_id, run_id, "review", "review.md")
  logging_utils.write_log(config, out_path, "\n".join(review_md) + "\n")

  return result, blockers, suggestions

