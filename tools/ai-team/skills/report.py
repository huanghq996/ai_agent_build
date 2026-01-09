#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def iter_todos(state: dict):
  for epic in state.get("epics", []):
    for feature in epic.get("features", []):
      for todo in feature.get("todos", []):
        yield epic, feature, todo


def main() -> int:
  ap = argparse.ArgumentParser(description="Skill: Report (generate delivery report)")
  ap.add_argument("--out", default="docs/ops/delivery-report.md")
  args = ap.parse_args()

  state = json.loads(Path("docs/ops/ai-team-state.json").read_text(encoding="utf-8"))

  lines: list[str] = []
  lines.append("# 交付报告（Delivery Report）")
  lines.append("")
  lines.append("## Todo 列表")
  lines.append("")
  for epic, feature, todo in iter_todos(state):
    commits = todo.get("commits") or []
    commit = commits[0] if commits else "-"
    lines.append(f"- {todo['todoId']} | {todo['status']} | {todo['title']} | {commit}")

  out_path = Path(args.out)
  out_path.parent.mkdir(parents=True, exist_ok=True)
  out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(f"REPORT_OK {out_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
