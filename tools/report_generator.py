#!/usr/bin/env python3
"""报告生成工具 - AI 团队系统的 Report Skill"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("docs/ops/ai-team-state.json")
REPORTS_DIR = Path("docs/ops/reports")


def load_state() -> dict:
    """加载状态文件"""
    if not STATE_FILE.exists():
        print(f"ERROR: {STATE_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def get_all_todos(state: dict) -> list:
    """获取所有 Todo"""
    todos = []
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            todos.extend(feature.get("todos", []))
    return todos


def find_todo(state: dict, todo_id: str) -> dict | None:
    """查找 Todo"""
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            for todo in feature.get("todos", []):
                if todo.get("todoId") == todo_id:
                    return todo
    return None


def cmd_delivery_report(args):
    """生成交付报告"""
    state = load_state()
    todos = get_all_todos(state)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORTS_DIR / f"delivery-{timestamp}.md"

    lines = [
        "# 交付报告",
        f"\n生成时间: {datetime.now().isoformat()}",
        f"\n## 完成的 Todo\n"
    ]

    done_todos = [t for t in todos if t["status"] == "DONE"]
    for todo in done_todos:
        lines.append(f"### {todo['todoId']}: {todo['title']}")
        lines.append(f"- 分支: `{todo['branch']}`")
        lines.append(f"- Commits: {', '.join(todo['commits'])}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"DELIVERY_REPORT: {report_path}")


def cmd_blocked_report(args):
    """生成阻断报告"""
    state = load_state()
    todo = find_todo(state, args.todo_id)

    if not todo:
        print(f"ERROR: Todo {args.todo_id} not found.", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORTS_DIR / f"blocked-{args.todo_id}-{timestamp}.md"

    lines = [
        f"# 阻断报告: {args.todo_id}",
        f"\n生成时间: {datetime.now().isoformat()}",
        f"\n## Todo 信息",
        f"- ID: {todo['todoId']}",
        f"- 标题: {todo['title']}",
        f"- 状态: {todo['status']}",
        f"- 修复次数: {todo.get('fixCyclesUsed', 0)}",
        f"\n## Review 结果",
        f"- 最后结果: {todo['review']['lastResult']}",
    ]

    if todo['review']['blockers']:
        lines.append("\n### Blockers")
        for b in todo['review']['blockers']:
            lines.append(f"- {b}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"BLOCKED_REPORT: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Report Generator")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # generate-delivery-report
    subparsers.add_parser("generate-delivery-report")

    # generate-blocked-report
    p_blocked = subparsers.add_parser("generate-blocked-report")
    p_blocked.add_argument("todo_id", help="TODO-ID")

    args = parser.parse_args()

    if args.cmd == "generate-delivery-report":
        cmd_delivery_report(args)
    elif args.cmd == "generate-blocked-report":
        cmd_blocked_report(args)


if __name__ == "__main__":
    main()
