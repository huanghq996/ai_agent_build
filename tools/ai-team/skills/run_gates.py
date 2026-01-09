#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: dict) -> None:
  path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_todos(state: dict):
  for epic in state.get("epics", []):
    for feature in epic.get("features", []):
      for todo in feature.get("todos", []):
        yield todo


def find_todo(state: dict, todo_id: str) -> dict | None:
  for todo in iter_todos(state):
    if todo.get("todoId") == todo_id:
      return todo
  return None


def now_run_id() -> str:
  return datetime.now().strftime("%Y%m%d-%H%M%S")


def run_cmd(cmd: str, env: dict[str, str]) -> tuple[int, str]:
  proc = subprocess.run(cmd, shell=True, text=True, capture_output=True, env=env)
  out = (proc.stdout or "") + (proc.stderr or "")
  return proc.returncode, out


def main() -> int:
  ap = argparse.ArgumentParser(description="Skill: RunGates (deterministic)")
  ap.add_argument("--todo", required=True, help="TODO-ID, e.g. TODO-123")
  ap.add_argument("--required-only", action="store_true", help="Run only config.gates.required (default)")
  ap.add_argument("--run-id", default="", help="Override run id (YYYYMMDD-HHMMSS)")
  args = ap.parse_args()

  config = load_json(Path("docs/ops/ai-team-config.json"))
  state_path = Path("docs/ops/ai-team-state.json")
  state = load_json(state_path)

  todo = find_todo(state, args.todo)
  if todo is None:
    print(f"TODO_NOT_FOUND: {args.todo}", file=sys.stderr)
    return 2

  run_id = args.run_id or now_run_id()
  required = config["gates"]["required"]
  commands = config["gates"]["commands"]
  fail_fast = bool(config["gates"]["policies"].get("failFast", True))

  results: dict[str, str] = {}
  overall_ok = True

  env = {**os.environ, **{"AI_TEAM_TODO_ID": args.todo, "AI_TEAM_RUN_ID": run_id}}

  for gate in required:
    cmd = commands.get(gate)
    if not cmd:
      results[gate] = "FAIL"
      overall_ok = False
      if fail_fast:
        break
      continue
    code, _ = run_cmd(cmd, env=env)
    results[gate] = "PASS" if code == 0 else "FAIL"
    if code != 0:
      overall_ok = False
      if fail_fast:
        break

  # write back
  for gate, result in results.items():
    if gate in todo["gates"]:
      todo["gates"][gate] = result
  save_json(state_path, state)

  payload = {"todoId": args.todo, "runId": run_id, "results": results, "overall": "PASS" if overall_ok else "FAIL"}
  print(json.dumps(payload, ensure_ascii=False))
  return 0 if overall_ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
