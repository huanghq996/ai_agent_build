#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime
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

  config = json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))
  state = json.loads(Path("docs/ops/ai-team-state.json").read_text(encoding="utf-8"))

  # Run gates summary (single source: ./scripts/check)
  check = subprocess.run(["./scripts/check"], text=True, capture_output=True)
  check_output = (check.stdout or "") + (check.stderr or "")
  check_summary = [
    ln
    for ln in check_output.splitlines()
    if ln.startswith("GATE ") or ln.startswith("CHECK ")
  ]

  done = []
  for epic, feature, todo in iter_todos(state):
    if todo.get("status") == "DONE":
      done.append((epic, feature, todo))

  affected = {"web": set(), "server": set(), "contract": set(), "dbMigration": set()}
  for _, _, todo in done:
    aa = todo.get("affectedAreas") or {}
    for k in affected.keys():
      for v in aa.get(k, []) or []:
        affected[k].add(v)

  lines: list[str] = []
  lines.append("# 交付报告（Delivery Report）")
  lines.append("")
  lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  lines.append(f"- 项目：{state['project']['name']}")
  lines.append("")

  lines.append("## 完成的 Todo")
  lines.append("")
  if not done:
    lines.append("- (none)")
  else:
    for _, _, todo in done:
      commits = todo.get("commits") or []
      commit_str = ", ".join(commits) if commits else "-"
      lines.append(f"- {todo['todoId']} | {todo['title']} | {commit_str}")

  lines.append("")
  lines.append("## 关键变更点（按影响面）")
  lines.append("")
  for k, title in [("web", "Web"), ("server", "Server"), ("contract", "Contract"), ("dbMigration", "DB Migration")]:
    items = sorted(affected[k])
    lines.append(f"### {title}")
    if not items:
      lines.append("- (none)")
    else:
      for it in items:
        lines.append(f"- {it}")
    lines.append("")

  lines.append("## 门禁执行记录摘要（./scripts/check）")
  lines.append("")
  lines.append(f"- exitCode: {check.returncode}")
  for ln in check_summary:
    lines.append(f"- {ln}")
  lines.append("")

  lines.append("## 回滚说明")
  lines.append("")
  lines.append("- DB Migration：如涉及新增迁移，回滚需提供对应逆向 SQL；本次 demo 未新增 .sql 迁移文件。")
  lines.append("")

  lines.append("## 已知风险与后续建议（具体）")
  lines.append("")
  lines.append("- 网络受限环境下不可执行依赖下载型门禁（pnpm install/mvn dependency fetch）；当前门禁采用本地确定性校验为主。")
  lines.append("- Docker socket 无权限时无法通过 docker CLI 验证 MySQL/Redis 容器（如需联调请确保当前用户可访问 /var/run/docker.sock）。")
  lines.append("- 如需生产级编译门禁：将 `./scripts/build` 扩展为真实的 web/server build（需要可用的依赖缓存或联网）。")
  lines.append("")

  out_path = Path(args.out)
  out_path.parent.mkdir(parents=True, exist_ok=True)
  out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(f"REPORT_OK {out_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
