#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("docs/ops/ai-team-state.json")

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

def cmd_add_todo(args):
    state = load_state()
    # Simple logic: add to first feature of first epic for now, or find specific parent
    # Ideally should specify epic/feature ID
    
    epic_id = "EPIC-1" # Default fallback
    feat_id = "FEAT-1" # Default fallback
    
    target_feature = None
    
    # Ensure EPIC-1 exists
    epics = state.setdefault("epics", [])
    epic = next((e for e in epics if e["epicId"] == epic_id), None)
    if not epic:
        epic = {"epicId": epic_id, "title": "Default Epic", "features": []}
        epics.append(epic)
    
    # Ensure FEAT-1 exists
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

def main():
    parser = argparse.ArgumentParser(description="AI Team State Manager")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    # update-status
    p_update = subparsers.add_parser("update-status")
    p_update.add_argument("todo", help="TODO-ID")
    p_update.add_argument("status", choices=["PLANNED","DOING","COMMITTED","REVIEWING","REVIEW_FAIL","GATE_FAIL","DONE","BLOCKED","ABORTED"])
    p_update.add_argument("--commit", help="Commit hash to add")
    
    # add-todo
    p_add = subparsers.add_parser("add-todo")
    p_add.add_argument("todo_id")
    p_add.add_argument("title")
    p_add.add_argument("--scope-in", action="append", required=True)
    p_add.add_argument("--scope-out", action="append", required=True)
    p_add.add_argument("--ac", action="append", required=True, help="Acceptance Criteria")
    
    # read-next
    p_next = subparsers.add_parser("read-next")
    
    args = parser.parse_args()
    
    if args.cmd == "update-status":
        cmd_update_status(args)
    elif args.cmd == "add-todo":
        cmd_add_todo(args)
    elif args.cmd == "read-next":
        cmd_read_next(args)

if __name__ == "__main__":
    main()
