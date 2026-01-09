import json
import re
from datetime import datetime
from pathlib import Path


def now_run_id() -> str:
  return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_config() -> dict:
  return json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))


def redact_text(text: str, config: dict) -> str:
  redactions = config["logging"]["redactions"]
  if not redactions.get("enabled", False):
    return text
  for pat in redactions.get("patterns", []):
    text = re.sub(pat, "***REDACTED***", text)
  return text


def log_base_dir(config: dict) -> Path:
  return Path(config["logging"]["dir"])


def log_path(config: dict, todo_id: str, run_id: str, category: str, filename: str) -> Path:
  base = log_base_dir(config)
  return base / todo_id / run_id / category / filename


def write_log(config: dict, path: Path, content: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(redact_text(content, config), encoding="utf-8")


def append_log(config: dict, path: Path, content: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
  path.write_text(existing + redact_text(content, config), encoding="utf-8")

