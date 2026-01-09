#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("docs/ops/ai-team-state.json")
CONFIG_FILE = Path("docs/ops/ai-team-config.json")

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"ERROR: {CONFIG_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse {CONFIG_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

def load_state() -> dict:
    if not STATE_FILE.exists():
        print(f"ERROR: {STATE_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse {STATE_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SUCCESS: Updated {STATE_FILE}")

def find_todo(state: dict, todo_id: str) -> dict | None:
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            for todo in feature.get("todos", []):
                if todo.get("todoId") == todo_id:
                    return todo
    return None

def cmd_update_status(args):
    state = load_state()
    todo = find_todo(state, args.todo)
    if not todo:
        print(f"ERROR: Todo {args.todo} not found.", file=sys.stderr)
        sys.exit(1)
    
    todo["status"] = args.status
    
    if args.commit:
        if "commits" not in todo:
            todo["commits"] = []
        if args.commit not in todo["commits"]:
            todo["commits"].append(args.commit)
            
    save_state(state)

def cmd_add_epic(args):
    """添加新的 Epic"""
    state = load_state()
    epics = state.setdefault("epics", [])

    # 检查是否已存在
    if any(e["epicId"] == args.epic_id for e in epics):
        print(f"ERROR: Epic {args.epic_id} already exists.", file=sys.stderr)
        sys.exit(1)

    epic = {"epicId": args.epic_id, "title": args.title, "features": []}
    epics.append(epic)
    save_state(state)
    print(f"SUCCESS: Added Epic {args.epic_id}")

def cmd_add_feature(args):
    """添加新的 Feature 到指定 Epic"""
    state = load_state()
    epics = state.get("epics", [])

    epic = next((e for e in epics if e["epicId"] == args.epic_id), None)
    if not epic:
        print(f"ERROR: Epic {args.epic_id} not found.", file=sys.stderr)
        sys.exit(1)

    features = epic.setdefault("features", [])
    if any(f["featureId"] == args.feature_id for f in features):
        print(f"ERROR: Feature {args.feature_id} already exists.", file=sys.stderr)
        sys.exit(1)

    feature = {"featureId": args.feature_id, "title": args.title, "todos": []}
    features.append(feature)
    save_state(state)
    print(f"SUCCESS: Added Feature {args.feature_id} to {args.epic_id}")

def cmd_add_todo(args):
    state = load_state()

    # 支持指定 epic 和 feature (argparse 将 --epic-id 转为 epic_id)
    epic_id = getattr(args, 'epic_id', None) or "EPIC-1"
    feat_id = getattr(args, 'feature_id', None) or "FEAT-1"

    target_feature = None

    # Ensure Epic exists
    epics = state.setdefault("epics", [])
    epic = next((e for e in epics if e["epicId"] == epic_id), None)
    if not epic:
        epic = {"epicId": epic_id, "title": "Default Epic", "features": []}
        epics.append(epic)

    # Ensure Feature exists
    features = epic.setdefault("features", [])
    feature = next((f for f in features if f["featureId"] == feat_id), None)
    if not feature:
        feature = {"featureId": feat_id, "title": "Default Feature", "todos": []}
        features.append(feature)

    target_feature = feature
    
    new_todo = {
        "todoId": args.todo_id,
        "title": args.title,
        "status": "PLANNED",
        "scope": {"in": args.scope_in, "out": args.scope_out},
        "acceptanceCriteria": args.ac,
        "affectedAreas": {
            "web": [], "server": [], "contract": [], "dbMigration": []
        },
        "branch": f"feat/{args.todo_id}-impl",
        "commits": [],
        "review": {"lastResult": "NONE", "blockers": [], "suggestions": []},
        "gates": {
             "lint": "SKIP", "test": "SKIP", "build": "SKIP", 
             "migrationCheck": "SKIP", "contractCheck": "SKIP",
             "stateSchemaCheck": "SKIP", "configSchemaCheck": "SKIP"
        },
        "fixCyclesUsed": 0
    }
    
    target_feature["todos"].append(new_todo)
    save_state(state)

def cmd_read_next(args):
    state = load_state()
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            for todo in feature.get("todos", []):
                if todo["status"] == "PLANNED":
                    print(json.dumps(todo, indent=2, ensure_ascii=False))
                    return
    print("NO_PLANNED_TODOS")

def get_all_todos(state: dict) -> list:
    """获取所有 Todo 的扁平列表"""
    todos = []
    for epic in state.get("epics", []):
        for feature in epic.get("features", []):
            todos.extend(feature.get("todos", []))
    return todos

def cmd_get_current_action(args):
    """根据状态文件决定当前应执行的动作"""
    state = load_state()
    config = load_config()
    max_fix = config.get("workflow", {}).get("maxAutoFixCyclesPerTodo", 5)

    todos = get_all_todos(state)

    # 1. 检查 BLOCKED/ABORTED
    for todo in todos:
        if todo["status"] in ("BLOCKED", "ABORTED"):
            print(f"BLOCKED:{todo['todoId']}")
            return

    # 2. 检查 REVIEW_FAIL/GATE_FAIL（需要修复）
    for todo in todos:
        if todo["status"] in ("REVIEW_FAIL", "GATE_FAIL"):
            if todo.get("fixCyclesUsed", 0) >= max_fix:
                print(f"BLOCKED:{todo['todoId']}")
            else:
                print(f"FIX_TODO:{todo['todoId']}")
            return

    # 3. 检查 REVIEWING（需要运行门禁）
    for todo in todos:
        if todo["status"] == "REVIEWING":
            print(f"RUN_GATES:{todo['todoId']}")
            return

    # 4. 检查 COMMITTED（需要审查）
    for todo in todos:
        if todo["status"] == "COMMITTED":
            print(f"REVIEW_TODO:{todo['todoId']}")
            return

    # 5. 检查 DOING（继续开发）
    for todo in todos:
        if todo["status"] == "DOING":
            print(f"DEV_TODO:{todo['todoId']}")
            return

    # 6. 检查 PLANNED（需要派工）
    for todo in todos:
        if todo["status"] == "PLANNED":
            print(f"DISPATCH_TODO:{todo['todoId']}")
            return

    # 7. 所有都是 DONE
    all_done = all(t["status"] == "DONE" for t in todos) if todos else False
    if all_done:
        print("ALL_DONE")
    else:
        print("NO_ACTION")

def cmd_update_review(args):
    """更新 Todo 的 review 结果"""
    state = load_state()
    todo = find_todo(state, args.todo)
    if not todo:
        print(f"ERROR: Todo {args.todo} not found.", file=sys.stderr)
        sys.exit(1)

    todo["review"]["lastResult"] = args.result
    todo["review"]["blockers"] = args.blocker or []
    todo["review"]["suggestions"] = args.suggestion or []

    # 根据结果更新状态
    if args.result == "PASS":
        todo["status"] = "REVIEWING"
    else:
        todo["status"] = "REVIEW_FAIL"

    save_state(state)

def cmd_update_gates(args):
    """更新 Todo 的门禁结果"""
    state = load_state()
    todo = find_todo(state, args.todo)
    if not todo:
        print(f"ERROR: Todo {args.todo} not found.", file=sys.stderr)
        sys.exit(1)

    gates = todo["gates"]
    if args.lint:
        gates["lint"] = args.lint
    if args.test:
        gates["test"] = args.test
    if args.build:
        gates["build"] = args.build
    if args.migration_check:
        gates["migrationCheck"] = args.migration_check
    if args.contract_check:
        gates["contractCheck"] = args.contract_check

    # 判断是否全部通过
    required = ["lint", "test", "build"]
    all_pass = all(gates.get(g) in ("PASS", "SKIP") for g in required)

    if all_pass and todo["review"]["lastResult"] == "PASS":
        todo["status"] = "DONE"
    elif not all_pass:
        todo["status"] = "GATE_FAIL"

    save_state(state)

def cmd_increment_fix_cycle(args):
    """增加修复计数"""
    state = load_state()
    todo = find_todo(state, args.todo)
    if not todo:
        print(f"ERROR: Todo {args.todo} not found.", file=sys.stderr)
        sys.exit(1)

    todo["fixCyclesUsed"] = todo.get("fixCyclesUsed", 0) + 1
    todo["status"] = "DOING"
    print(f"FIX_CYCLE: {todo['fixCyclesUsed']}")
    save_state(state)

def main():
    parser = argparse.ArgumentParser(description="AI Team State Manager")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    # update-status
    p_update = subparsers.add_parser("update-status")
    p_update.add_argument("todo", help="TODO-ID")
    p_update.add_argument("status", choices=["PLANNED","DOING","COMMITTED","REVIEWING","REVIEW_FAIL","GATE_FAIL","DONE","BLOCKED","ABORTED"])
    p_update.add_argument("--commit", help="Commit hash to add")
    
    # add-epic
    p_epic = subparsers.add_parser("add-epic")
    p_epic.add_argument("epic_id")
    p_epic.add_argument("title")

    # add-feature
    p_feat = subparsers.add_parser("add-feature")
    p_feat.add_argument("epic_id")
    p_feat.add_argument("feature_id")
    p_feat.add_argument("title")

    # add-todo
    p_add = subparsers.add_parser("add-todo")
    p_add.add_argument("todo_id")
    p_add.add_argument("title")
    p_add.add_argument("--epic-id", help="Epic ID")
    p_add.add_argument("--feature-id", help="Feature ID")
    p_add.add_argument("--scope-in", action="append", required=True)
    p_add.add_argument("--scope-out", action="append", required=True)
    p_add.add_argument("--ac", action="append", required=True, help="Acceptance Criteria")
    
    # read-next
    p_next = subparsers.add_parser("read-next")

    # get-current-action
    p_action = subparsers.add_parser("get-current-action")

    # update-review
    p_review = subparsers.add_parser("update-review")
    p_review.add_argument("todo", help="TODO-ID")
    p_review.add_argument("result", choices=["PASS", "FAIL"])
    p_review.add_argument("--blocker", action="append", help="Blocker message")
    p_review.add_argument("--suggestion", action="append", help="Suggestion")

    # update-gates
    p_gates = subparsers.add_parser("update-gates")
    p_gates.add_argument("todo", help="TODO-ID")
    p_gates.add_argument("--lint", choices=["PASS", "FAIL", "SKIP"])
    p_gates.add_argument("--test", choices=["PASS", "FAIL", "SKIP"])
    p_gates.add_argument("--build", choices=["PASS", "FAIL", "SKIP"])
    p_gates.add_argument("--migration-check", choices=["PASS", "FAIL", "SKIP"])
    p_gates.add_argument("--contract-check", choices=["PASS", "FAIL", "SKIP"])

    # increment-fix-cycle
    p_fix = subparsers.add_parser("increment-fix-cycle")
    p_fix.add_argument("todo", help="TODO-ID")

    args = parser.parse_args()
    
    if args.cmd == "update-status":
        cmd_update_status(args)
    elif args.cmd == "add-epic":
        cmd_add_epic(args)
    elif args.cmd == "add-feature":
        cmd_add_feature(args)
    elif args.cmd == "add-todo":
        cmd_add_todo(args)
    elif args.cmd == "read-next":
        cmd_read_next(args)
    elif args.cmd == "get-current-action":
        cmd_get_current_action(args)
    elif args.cmd == "update-review":
        cmd_update_review(args)
    elif args.cmd == "update-gates":
        cmd_update_gates(args)
    elif args.cmd == "increment-fix-cycle":
        cmd_increment_fix_cycle(args)

if __name__ == "__main__":
    main()
