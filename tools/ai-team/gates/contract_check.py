import json
import re
import sys
from pathlib import Path

import yaml


def load_config() -> dict:
  return json.loads(Path("docs/ops/ai-team-config.json").read_text(encoding="utf-8"))


def get_by_given(obj: object, given: str) -> object:
  if given == "$":
    return obj
  if not given.startswith("$."):
    return None
  cur = obj
  for part in given[2:].split("."):
    if not isinstance(cur, dict) or part not in cur:
      return None
    cur = cur[part]
  return cur


def apply_spectral_lite(openapi: dict, spectral_rules: dict) -> list[str]:
  failures: list[str] = []
  rules = spectral_rules.get("rules") if isinstance(spectral_rules, dict) else None
  if not isinstance(rules, dict):
    return ["SPECTRAL_RULES_INVALID"]

  for rule_id, rule in rules.items():
    if not isinstance(rule, dict):
      failures.append(f"SPECTRAL_RULE_INVALID:{rule_id}")
      continue
    given = rule.get("given")
    then = rule.get("then")
    if not isinstance(given, str) or not isinstance(then, dict):
      failures.append(f"SPECTRAL_RULE_INVALID:{rule_id}")
      continue
    field = then.get("field")
    fn = then.get("function")
    if not isinstance(field, str) or not isinstance(fn, str):
      failures.append(f"SPECTRAL_RULE_INVALID:{rule_id}")
      continue

    target = get_by_given(openapi, given)
    if not isinstance(target, dict):
      failures.append(f"SPECTRAL_FAIL:{rule_id}")
      continue

    if fn == "truthy":
      if field not in target:
        failures.append(f"SPECTRAL_FAIL:{rule_id}")
        continue
      value = target.get(field)
      if value is None:
        failures.append(f"SPECTRAL_FAIL:{rule_id}")
        continue
      if isinstance(value, str) and not value.strip():
        failures.append(f"SPECTRAL_FAIL:{rule_id}")
      continue

    failures.append(f"SPECTRAL_UNSUPPORTED_FUNCTION:{rule_id}:{fn}")

  return failures


def validate_openapi(openapi: object) -> list[str]:
  if not isinstance(openapi, dict):
    return ["OPENAPI_NOT_OBJECT"]
  info = openapi.get("info")
  paths = openapi.get("paths")
  if not isinstance(info, dict):
    return ["OPENAPI_MISSING_INFO"]
  if not info.get("version"):
    return ["OPENAPI_MISSING_INFO_VERSION"]
  if not info.get("title"):
    return ["OPENAPI_MISSING_INFO_TITLE"]
  if not isinstance(paths, dict):
    return ["OPENAPI_MISSING_PATHS"]
  return []


def validate_error_codes(obj: object) -> list[str]:
  if not isinstance(obj, list):
    return ["ERROR_CODES_NOT_ARRAY"]
  seen: set[str] = set()
  failures: list[str] = []
  for i, item in enumerate(obj):
    if not isinstance(item, dict):
      failures.append(f"ERROR_CODES_ITEM_NOT_OBJECT:{i}")
      continue
    code = item.get("code")
    message = item.get("message")
    http_status = item.get("httpStatus")
    deprecated = item.get("deprecated")
    if not isinstance(code, str) or not code:
      failures.append(f"ERROR_CODES_CODE_INVALID:{i}")
    if not isinstance(message, str) or not message:
      failures.append(f"ERROR_CODES_MESSAGE_INVALID:{i}")
    if not isinstance(http_status, int) or http_status < 100 or http_status > 599:
      failures.append(f"ERROR_CODES_HTTPSTATUS_INVALID:{i}")
    if not isinstance(deprecated, bool):
      failures.append(f"ERROR_CODES_DEPRECATED_INVALID:{i}")
    if isinstance(code, str):
      if code in seen:
        failures.append(f"ERROR_CODES_CODE_DUPLICATE:{code}")
      seen.add(code)
  return failures


def discover_server_endpoints(server_src_root: Path) -> set[tuple[str, str]]:
  endpoints: set[tuple[str, str]] = set()
  if not server_src_root.exists():
    return endpoints
  pattern_map = {
    "get": re.compile(r"@GetMapping\\s*\\(\\s*\"([^\"]*)\"\\s*\\)"),
    "post": re.compile(r"@PostMapping\\s*\\(\\s*\"([^\"]*)\"\\s*\\)"),
    "put": re.compile(r"@PutMapping\\s*\\(\\s*\"([^\"]*)\"\\s*\\)"),
    "delete": re.compile(r"@DeleteMapping\\s*\\(\\s*\"([^\"]*)\"\\s*\\)"),
  }

  for java_file in server_src_root.rglob("*.java"):
    text = java_file.read_text(encoding="utf-8", errors="replace")
    for method, pat in pattern_map.items():
      for m in pat.finditer(text):
        path = m.group(1).strip() or "/"
        if not path.startswith("/"):
          path = "/" + path
        endpoints.add((method, path))
  return endpoints


def validate_server_sync(openapi: dict, endpoints: set[tuple[str, str]]) -> list[str]:
  failures: list[str] = []
  paths = openapi.get("paths")
  if not isinstance(paths, dict):
    return ["OPENAPI_MISSING_PATHS"]
  for method, path in sorted(endpoints):
    path_item = paths.get(path)
    if not isinstance(path_item, dict):
      failures.append(f"SERVER_OPENAPI_MISSING_PATH:{method.upper()} {path}")
      continue
    if method not in path_item:
      failures.append(f"SERVER_OPENAPI_MISSING_METHOD:{method.upper()} {path}")
  return failures


def main() -> int:
  cfg = load_config()
  openapi_path = Path(cfg["contracts"]["openapiPath"])
  error_codes_path = Path(cfg["contracts"]["errorCodesPath"])
  spectral_path = Path(cfg["contracts"]["spectralRulesPath"])

  try:
    openapi = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
  except Exception as e:
    print(f"OPENAPI_PARSE_FAIL: {e}", file=sys.stderr)
    return 1

  openapi_failures = validate_openapi(openapi)
  if openapi_failures:
    print("OPENAPI_INVALID")
    for f in openapi_failures:
      print(f" - {f}")
    return 1

  try:
    spectral = yaml.safe_load(spectral_path.read_text(encoding="utf-8"))
  except Exception as e:
    print(f"SPECTRAL_RULES_PARSE_FAIL: {e}", file=sys.stderr)
    return 1

  spectral_failures = apply_spectral_lite(openapi, spectral)
  if spectral_failures:
    print("SPECTRAL_FAIL")
    for f in spectral_failures:
      print(f" - {f}")
    return 1

  try:
    error_codes = json.loads(error_codes_path.read_text(encoding="utf-8"))
  except Exception as e:
    print(f"ERROR_CODES_PARSE_FAIL: {e}", file=sys.stderr)
    return 1

  error_failures = validate_error_codes(error_codes)
  if error_failures:
    print("ERROR_CODES_INVALID")
    for f in error_failures:
      print(f" - {f}")
    return 1

  endpoints = discover_server_endpoints(Path("apps/server/src/main/java"))
  sync_failures = validate_server_sync(openapi, endpoints)
  if sync_failures:
    print("SERVER_OPENAPI_MISMATCH")
    for f in sync_failures:
      print(f" - {f}")
    return 1

  print("OPENAPI_OK ERROR_CODES_OK SERVER_SYNC_OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
