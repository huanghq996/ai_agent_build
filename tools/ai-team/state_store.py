import json
from pathlib import Path


def load_json(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: dict) -> None:
  path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_config() -> dict:
  return load_json(Path("docs/ops/ai-team-config.json"))


def load_state() -> dict:
  return load_json(Path("docs/ops/ai-team-state.json"))


def save_state(state: dict) -> None:
  save_json(Path("docs/ops/ai-team-state.json"), state)


def iter_todos(state: dict):
  for epic in state.get("epics", []):
    for feature in epic.get("features", []):
      for todo in feature.get("todos", []):
        yield epic, feature, todo


def find_todo(state: dict, todo_id: str) -> dict | None:
  for _, _, todo in iter_todos(state):
    if todo.get("todoId") == todo_id:
      return todo
  return None


def ensure_epic_feature(state: dict, epic_id: str, epic_title: str, feature_id: str, feature_title: str) -> tuple[dict, dict]:
  epic = next((e for e in state.get("epics", []) if e.get("epicId") == epic_id), None)
  if epic is None:
    epic = {"epicId": epic_id, "title": epic_title, "features": []}
    state.setdefault("epics", []).append(epic)
  feature = next((f for f in epic.get("features", []) if f.get("featureId") == feature_id), None)
  if feature is None:
    feature = {"featureId": feature_id, "title": feature_title, "todos": []}
    epic.setdefault("features", []).append(feature)
  return epic, feature

