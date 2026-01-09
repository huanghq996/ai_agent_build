#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(cmd, text=True, capture_output=True)


def require_clean_worktree() -> None:
  r = sh(["git", "status", "--porcelain=v1"])
  if r.returncode != 0:
    print(r.stderr.strip(), file=sys.stderr)
    raise SystemExit(2)
  if r.stdout.strip():
    print("GIT_WORKTREE_DIRTY", file=sys.stderr)
    print(r.stdout.strip(), file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
  ap = argparse.ArgumentParser(description="Skill: GitOps (deterministic local git operations)")
  sub = ap.add_subparsers(dest="cmd", required=True)

  sub.add_parser("status", help="Print current branch and porcelain status")

  p_branch = sub.add_parser("create-branch", help="Create and checkout branch for a TODO")
  p_branch.add_argument("--type", required=True, choices=["feat", "fix", "chore"])
  p_branch.add_argument("--todo", required=True)
  p_branch.add_argument("--desc", required=True, help="kebab-case description")
  p_branch.add_argument("--require-clean", action="store_true", help="Fail if worktree is dirty")

  p_commit = sub.add_parser("commit", help="Create a commit (adds paths)")
  p_commit.add_argument("--type", required=True, choices=["feat", "fix", "chore"])
  p_commit.add_argument("--scope", default="", help="scope, e.g. ops/web/server/contract")
  p_commit.add_argument("--todo", required=True)
  p_commit.add_argument("--message", required=True, help="Commit subject without TODO prefix")
  p_commit.add_argument("--add", action="append", default=[], help="Paths to add (repeatable)")

  p_amend = sub.add_parser("amend", help="Amend last commit (adds paths)")
  p_amend.add_argument("--add", action="append", default=[], help="Paths to add (repeatable)")

  args = ap.parse_args()

  if args.cmd == "status":
    b = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    s = sh(["git", "status", "--porcelain=v1"])
    if b.returncode != 0:
      print(b.stderr.strip(), file=sys.stderr)
      return 2
    print(f"BRANCH {b.stdout.strip()}")
    print(s.stdout.rstrip())
    return 0

  if args.cmd == "create-branch":
    if args.require_clean:
      require_clean_worktree()
    if not re.fullmatch(r"TODO-\\d+", args.todo):
      print("INVALID_TODO_ID", file=sys.stderr)
      return 2
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.desc):
      print("INVALID_DESC_KEBAB", file=sys.stderr)
      return 2
    branch = f"{args.type}/{args.todo}-{args.desc}"
    r = sh(["git", "checkout", "-b", branch])
    if r.returncode != 0:
      print(r.stderr.strip(), file=sys.stderr)
      return 1
    print(f"BRANCH_CREATED {branch}")
    return 0

  if args.cmd == "commit":
    for p in args.add:
      r = sh(["git", "add", p])
      if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        return 1
    scope = f"({args.scope})" if args.scope else ""
    subject = f"{args.type}{scope}: {args.todo} {args.message}"
    r = sh(["git", "commit", "-m", subject])
    if r.returncode != 0:
      print(r.stderr.strip(), file=sys.stderr)
      return 1
    h = sh(["git", "rev-parse", "--short", "HEAD"])
    print(f"COMMIT_OK {h.stdout.strip()}")
    return 0

  if args.cmd == "amend":
    for p in args.add:
      r = sh(["git", "add", p])
      if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        return 1
    r = sh(["git", "commit", "--amend", "--no-edit"])
    if r.returncode != 0:
      print(r.stderr.strip(), file=sys.stderr)
      return 1
    h = sh(["git", "rev-parse", "--short", "HEAD"])
    print(f"AMEND_OK {h.stdout.strip()}")
    return 0

  print("UNKNOWN_CMD", file=sys.stderr)
  return 2


if __name__ == "__main__":
  raise SystemExit(main())

