#!/usr/bin/env python3
"""Git 操作工具 - AI 团队系统的 GitOps Skill"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

STATE_FILE = Path("docs/ops/ai-team-state.json")


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """执行 git 命令"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"GIT_ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result


def load_state() -> dict:
    """加载状态文件"""
    if not STATE_FILE.exists():
        print(f"ERROR: {STATE_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def find_todo(state: dict, todo_id: str) -> dict | None:
    """查找 Todo"""
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            for todo in feature.get("todos", []):
                if todo.get("todoId") == todo_id:
                    return todo
    return None


def cmd_create_branch(args):
    """创建分支"""
    branch_name = f"{args.type}/{args.todo_id}-{args.desc}"

    # 检查分支是否已存在
    result = run_git(["branch", "--list", branch_name], check=False)
    if result.stdout.strip():
        print(f"BRANCH_EXISTS: {branch_name}")
        run_git(["checkout", branch_name])
        return

    # 创建并切换到新分支
    run_git(["checkout", "-b", branch_name])
    print(f"BRANCH_CREATED: {branch_name}")


def cmd_commit(args):
    """提交代码"""
    # 添加所有变更
    run_git(["add", "-A"])

    # 检查是否有变更
    result = run_git(["status", "--porcelain"], check=False)
    if not result.stdout.strip():
        print("NO_CHANGES")
        return

    # 提交
    run_git(["commit", "-m", args.message])

    # 获取 commit hash
    result = run_git(["rev-parse", "--short", "HEAD"])
    commit_hash = result.stdout.strip()
    print(f"COMMIT_HASH: {commit_hash}")


def cmd_amend(args):
    """修改最后提交"""
    run_git(["add", "-A"])
    run_git(["commit", "--amend", "-m", args.message])

    result = run_git(["rev-parse", "--short", "HEAD"])
    commit_hash = result.stdout.strip()
    print(f"AMENDED_HASH: {commit_hash}")


def cmd_branch_status(args):
    """获取分支状态"""
    # 获取当前分支
    result = run_git(["branch", "--show-current"])
    branch = result.stdout.strip()

    # 获取 commit 数量
    result = run_git(["rev-list", "--count", "HEAD"], check=False)
    commits = result.stdout.strip() if result.returncode == 0 else "0"

    # 获取 ahead 数量（相对于 master）
    result = run_git(["rev-list", "--count", "master..HEAD"], check=False)
    ahead = result.stdout.strip() if result.returncode == 0 else "0"

    print(f"BRANCH: {branch}, COMMITS: {commits}, AHEAD: {ahead}")


def main():
    parser = argparse.ArgumentParser(description="Git Operations Tool")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # create-branch
    p_branch = subparsers.add_parser("create-branch")
    p_branch.add_argument("todo_id", help="TODO-ID")
    p_branch.add_argument("type", choices=["feat", "fix", "chore"])
    p_branch.add_argument("desc", help="Branch description (kebab-case)")

    # commit
    p_commit = subparsers.add_parser("commit")
    p_commit.add_argument("todo_id", help="TODO-ID")
    p_commit.add_argument("message", help="Commit message")

    # amend
    p_amend = subparsers.add_parser("amend")
    p_amend.add_argument("todo_id", help="TODO-ID")
    p_amend.add_argument("message", help="New commit message")

    # branch-status
    p_status = subparsers.add_parser("branch-status")
    p_status.add_argument("todo_id", help="TODO-ID", nargs="?")

    args = parser.parse_args()

    if args.cmd == "create-branch":
        cmd_create_branch(args)
    elif args.cmd == "commit":
        cmd_commit(args)
    elif args.cmd == "amend":
        cmd_amend(args)
    elif args.cmd == "branch-status":
        cmd_branch_status(args)


if __name__ == "__main__":
    main()
