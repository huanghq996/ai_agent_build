#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

import deterministic_review
import logging_utils
import state_store


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(cmd, text=True, capture_output=True)


def git(cmd: list[str], git_log: Path | None = None, config: dict | None = None) -> str:
  r = sh(["git", *cmd])
  if git_log is not None and config is not None:
    logging_utils.append_log(config, git_log, f"$ git {' '.join(cmd)}\n{r.stdout}{r.stderr}\n")
  if r.returncode != 0:
    raise RuntimeError(r.stderr.strip() or f"git {' '.join(cmd)} failed")
  return r.stdout.strip()


def ensure_base_branch(config: dict, git_log: Path | None = None) -> None:
  base = config["project"]["baseBranch"]
  cur = git(["rev-parse", "--abbrev-ref", "HEAD"], git_log, config)
  if cur != base:
    git(["checkout", base], git_log, config)


def ensure_demo_todo(state: dict, config: dict) -> str:
  demo = config["demo"]["todo"]
  todo_id = demo["todoId"]
  if state_store.find_todo(state, todo_id) is not None:
    return todo_id

  _, feature = state_store.ensure_epic_feature(state, "EPIC-2", "Demo", "FEAT-2", "Demo loop")
  feature["todos"].append(
    {
      "todoId": todo_id,
      "title": demo["title"],
      "status": "PLANNED",
      "scope": {"in": demo["scopeIn"], "out": demo["scopeOut"]},
      "acceptanceCriteria": [
        "./scripts/check PASS",
        "Review PASS + Gates PASS",
        "docs/ops/logs/<TODO-ID>/<run>/ 证据齐全"
      ],
      "affectedAreas": {
        "web": ["apps/web/*"],
        "server": ["apps/server/*"],
        "contract": ["packages/api-contract/*"],
        "dbMigration": []
      },
      "branch": f"feat/{todo_id}-health-check-demo",
      "commits": [],
      "review": {"lastResult": "NONE", "blockers": [], "suggestions": []},
      "gates": {
        "lint": "SKIP",
        "test": "SKIP",
        "build": "SKIP",
        "migrationCheck": "SKIP",
        "contractCheck": "SKIP",
        "stateSchemaCheck": "SKIP",
        "configSchemaCheck": "SKIP"
      },
      "fixCyclesUsed": 0
    }
  )
  return todo_id


def cmd_init(_args) -> int:
  config = state_store.load_config()
  run_id = logging_utils.now_run_id()
  run_log = logging_utils.log_base_dir(config) / "system" / run_id / "run.log"

  logging_utils.write_log(config, run_log, f"INIT_START run={run_id}\n")

  r1 = subprocess.run(["./scripts/config-validate"])
  r2 = subprocess.run(["./scripts/state-validate"])
  if r1.returncode != 0 or r2.returncode != 0:
    logging_utils.append_log(config, run_log, "INIT_FAIL\n")
    return 1

  logging_utils.append_log(config, run_log, "INIT_OK\n")
  print("INIT_OK")
  return 0


def cmd_plan(args) -> int:
  config = state_store.load_config()
  state = state_store.load_state()

  if args.demo:
    todo_id = ensure_demo_todo(state, config)
    state_store.save_state(state)
    print(f"PLAN_OK demo todo={todo_id}")
    return 0

  print("PLAN_NOOP")
  return 0


def cmd_gates(args) -> int:
  r = subprocess.run(["python3", "tools/ai-team/skills/run_gates.py", "--todo", args.todo])
  return r.returncode


def cmd_report(args) -> int:
  r = subprocess.run(["python3", "tools/ai-team/skills/report.py", "--out", args.out])
  return r.returncode


def _apply_demo_todo_9001(config: dict) -> None:
  import json
  import yaml

  # Contract: ensure /health is defined
  openapi_path = Path("packages/api-contract/openapi.yaml")
  openapi = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
  if not isinstance(openapi, dict):
    raise RuntimeError("OPENAPI_INVALID")
  openapi.setdefault("paths", {})
  if not isinstance(openapi["paths"], dict):
    raise RuntimeError("OPENAPI_PATHS_INVALID")
  openapi["paths"]["/health"] = {
    "get": {
      "operationId": "getHealth",
      "summary": "Health check",
      "responses": {
        "200": {
          "description": "OK",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["status", "time"],
                "properties": {"status": {"type": "string"}, "time": {"type": "string"}}
              }
            }
          }
        }
      }
    }
  }
  openapi_path.write_text(yaml.safe_dump(openapi, sort_keys=False, allow_unicode=True), encoding="utf-8")

  # Server: add controller
  ctrl = Path("apps/server/src/main/java/com/example/agb/controller/HealthController.java")
  ctrl.parent.mkdir(parents=True, exist_ok=True)
  ctrl.write_text(
    "\n".join(
      [
        "package com.example.agb.controller;",
        "",
        "import java.time.Instant;",
        "import java.util.Map;",
        "",
        "import org.springframework.web.bind.annotation.GetMapping;",
        "import org.springframework.web.bind.annotation.RestController;",
        "",
        "@RestController",
        "public class HealthController {",
        "  @GetMapping(\"/health\")",
        "  public Map<String, Object> health() {",
        "    return Map.of(",
        "      \"status\", \"ok\",",
        "      \"time\", Instant.now().toString()",
        "    );",
        "  }",
        "}",
        "",
      ]
    ),
    encoding="utf-8",
  )

  # Contract: codegen web client if enabled
  if config["contracts"]["generated"]["enabled"]:
    r = subprocess.run(["python3", "tools/ai-team/skills/contract_sync.py", "generate"])
    if r.returncode != 0:
      raise RuntimeError("CODEGEN_FAIL")

  # Web: use generated client (intentionally add trailing whitespace once)
  app_vue = Path("apps/web/src/App.vue")
  app_vue.write_text(
    "\n".join(
      [
        "<template>",
        "  <main class=\"p-4\">",
        "    <h1 class=\"text-xl font-semibold\">Demo: Health Check</h1>",
        "    <p class=\"mt-2 text-sm text-gray-600\">status: {{ state.status }}</p>",
        "    <p class=\"text-sm text-gray-600\">time: {{ state.time }}</p>",
        "  </main>",
        "</template>",
        "",
        "<script>",
        "import { onMounted, reactive } from \"vue\";",
        "import { getHealth } from \"./api/generated/index.js\";",
        "",
        "export default {",
        "  name: \"App\",",
        "  setup() {",
        "    const state = reactive({ status: \"loading\", time: \"-\" });",
        "    onMounted(async () => {",
        "      const data = await getHealth();  ",
        "      state.status = data.status;",
        "      state.time = data.time;",
        "    });",
        "    return { state };",
        "  },",
        "};",
        "</script>",
        "",
      ]
    ),
    encoding="utf-8",
  )


def _strip_trailing_whitespace_repo() -> int:
  fixed = 0
  ignore_dirs = {".git", "node_modules", "logs", ".cache"}

  def should_skip_dir(p: Path) -> bool:
    parts = set(p.parts)
    if ".git" in parts or "node_modules" in parts or ".cache" in parts:
      return True
    if p.parts[:3] == ("docs", "ops", "logs"):
      return True
    return False

  for root in [Path("apps"), Path("packages"), Path("docs"), Path("scripts"), Path("tools"), Path("Requirements document.md")]:
    if not root.exists():
      continue
    if root.is_file():
      candidates = [root]
    else:
      candidates = [p for p in root.rglob("*") if p.is_file()]
    for p in candidates:
      if not p.is_file():
        continue
      if should_skip_dir(p):
        continue
      if p.suffix.lower() not in (".md", ".json", ".yaml", ".yml", ".js", ".vue", ".sh", ".py", ".xml"):
        continue
      text = p.read_text(encoding="utf-8", errors="replace")
      lines = [ln.rstrip() for ln in text.splitlines()]
      out = "\n".join(lines) + "\n"
      if out != text:
        p.write_text(out, encoding="utf-8")
        fixed += 1
  return fixed


def cmd_run(args) -> int:
  config = state_store.load_config()
  state = state_store.load_state()

  if args.demo:
    todo_id = ensure_demo_todo(state, config)
    state_store.save_state(state)
  else:
    todo_id = args.todo

  if not todo_id:
    print("RUN_NO_TODO", file=sys.stderr)
    return 2

  todo = state_store.find_todo(state, todo_id)
  if todo is None:
    print(f"TODO_NOT_FOUND: {todo_id}", file=sys.stderr)
    return 2

  run_id = logging_utils.now_run_id()
  system_log = logging_utils.log_base_dir(config) / "system" / run_id / "run.log"
  logging_utils.write_log(config, system_log, f"RUN_START todo={todo_id} run={run_id}\n")

  todo_git_log = logging_utils.log_path(config, todo_id, run_id, "git", "git.log")

  ensure_base_branch(config, todo_git_log)

  # checkout/create branch
  branch = todo["branch"]
  existing = sh(["git", "rev-parse", "--verify", branch])
  if existing.returncode == 0:
    git(["checkout", branch], todo_git_log, config)
  else:
    git(["checkout", "-b", branch], todo_git_log, config)

  # State: PLANNED -> DOING
  if todo["status"] == "PLANNED":
    todo["status"] = "DOING"
    state_store.save_state(state)
    logging_utils.append_log(config, system_log, "STATE PLANNED->DOING\n")

  # Apply demo changes (once)
  if todo_id == "TODO-9001":
    _apply_demo_todo_9001(config)
  else:
    raise RuntimeError(f"RUN_UNSUPPORTED_TODO: {todo_id}")

  # Commit
  commit_subject = f"feat(ops): {todo_id} demo health check loop"
  git(["add", "packages/api-contract/openapi.yaml"], todo_git_log, config)
  git(["add", "apps/server/src/main/java/com/example/agb/controller/HealthController.java"], todo_git_log, config)
  git(["add", "apps/web/src/App.vue"], todo_git_log, config)
  if config["contracts"]["generated"]["enabled"]:
    git(["add", config["contracts"]["generated"]["webClientOutDir"]], todo_git_log, config)
  git(["commit", "-m", commit_subject], todo_git_log, config)

  head = git(["rev-parse", "--short", "HEAD"], todo_git_log, config)
  todo["commits"] = [head]
  todo["status"] = "COMMITTED"
  state_store.save_state(state)

  while True:
    todo["status"] = "REVIEWING"
    state_store.save_state(state)

    review_result, blockers, suggestions = deterministic_review.run_review(config, todo_id, run_id)
    todo["review"]["lastResult"] = review_result
    todo["review"]["blockers"] = blockers
    todo["review"]["suggestions"] = suggestions
    state_store.save_state(state)

    if review_result != "PASS":
      todo["status"] = "REVIEW_FAIL"
      state_store.save_state(state)
    else:
      gates_rc = subprocess.run(
        ["python3", "tools/ai-team/skills/run_gates.py", "--todo", todo_id, "--run-id", run_id]
      ).returncode
      state = state_store.load_state()
      todo = state_store.find_todo(state, todo_id)
      if todo is None:
        raise RuntimeError("TODO_DISAPPEARED")
      if gates_rc == 0:
        todo["status"] = "DONE"
        state_store.save_state(state)
        logging_utils.append_log(config, system_log, "STATE REVIEWING->DONE\n")
        print(f"RUN_DONE todo={todo_id} run={run_id}")
        return 0
      todo["status"] = "GATE_FAIL"
      state_store.save_state(state)

    # fix cycle
    if todo["fixCyclesUsed"] >= config["workflow"]["maxAutoFixCyclesPerTodo"]:
      todo["status"] = "BLOCKED"
      state_store.save_state(state)
      print("STATUS: BLOCKED")
      print(f"TODO-ID: {todo_id}")
      print("REASON:")
      print("- maxAutoFixCyclesPerTodo reached")
      return 1

    todo["fixCyclesUsed"] += 1
    todo["status"] = "DOING"
    state_store.save_state(state)

    fixed = _strip_trailing_whitespace_repo()
    logging_utils.append_log(config, system_log, f"AUTO_FIX_TRAILING_WS files_fixed={fixed}\n")

    git(["add", "-A"], todo_git_log, config)
    git(["commit", "--amend", "--no-edit"], todo_git_log, config)

    head = git(["rev-parse", "--short", "HEAD"], todo_git_log, config)
    todo["commits"] = [head]
    todo["status"] = "COMMITTED"
    state_store.save_state(state)


def main() -> int:
  ap = argparse.ArgumentParser(prog="./scripts/ai-team", description="AI Team main loop driver")
  sub = ap.add_subparsers(dest="cmd", required=True)

  sub.add_parser("init")

  p_plan = sub.add_parser("plan")
  p_plan.add_argument("--demo", action="store_true")

  p_run = sub.add_parser("run")
  p_run.add_argument("--demo", action="store_true")
  p_run.add_argument("--todo", default="")

  p_gates = sub.add_parser("gates")
  p_gates.add_argument("--todo", required=True)

  p_report = sub.add_parser("report")
  p_report.add_argument("--out", default="docs/ops/delivery-report.md")

  args = ap.parse_args()

  if args.cmd == "init":
    return cmd_init(args)
  if args.cmd == "plan":
    return cmd_plan(args)
  if args.cmd == "run":
    return cmd_run(args)
  if args.cmd == "gates":
    return cmd_gates(args)
  if args.cmd == "report":
    return cmd_report(args)

  print("UNKNOWN_CMD", file=sys.stderr)
  return 2


if __name__ == "__main__":
  raise SystemExit(main())

