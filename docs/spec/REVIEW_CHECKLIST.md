# REVIEW_CHECKLIST（可判定 PASS/FAIL）

> 每条规则必须包含：RULE_ID / DESCRIPTION / CHECK_METHOD / PASS_CONDITION / FAIL_OUTPUT

## RULE-OPS-SCHEMA-001

- DESCRIPTION: ai-team-config.json 必须通过 JSON Schema 校验
- CHECK_METHOD: `./scripts/config-validate`
- PASS_CONDITION: exit code = 0
- FAIL_OUTPUT: `CONFIG_SCHEMA_FAIL`

## RULE-OPS-SCHEMA-002

- DESCRIPTION: ai-team-state.json 必须通过 JSON Schema 校验
- CHECK_METHOD: `./scripts/state-validate`
- PASS_CONDITION: exit code = 0
- FAIL_OUTPUT: `STATE_SCHEMA_FAIL`

## RULE-OPS-GATES-001

- DESCRIPTION: ./scripts/check 必须按固定顺序执行 gates
- CHECK_METHOD: `./scripts/check --print-plan`
- PASS_CONDITION: 输出顺序等于 config 默认顺序（config-validate → state-validate → contract-check → migration-check → lint → test → build）
- FAIL_OUTPUT: `CHECK_ORDER_MISMATCH`

## RULE-CONTRACT-OPENAPI-001

- DESCRIPTION: openapi.yaml 必须可解析且包含 info/version/paths
- CHECK_METHOD: `./scripts/contract-check`
- PASS_CONDITION: exit code = 0 且摘要包含 `OPENAPI_OK`
- FAIL_OUTPUT: `OPENAPI_INVALID`

## RULE-CONTRACT-ERRORCODES-001

- DESCRIPTION: error-codes.json 必须为数组且 code 唯一
- CHECK_METHOD: `./scripts/contract-check`
- PASS_CONDITION: exit code = 0 且摘要包含 `ERROR_CODES_OK`
- FAIL_OUTPUT: `ERROR_CODES_INVALID`

## RULE-CONTRACT-SERVER-SYNC-001

- DESCRIPTION: server controller 暴露的 path+method 必须出现在 openapi.yaml
- CHECK_METHOD: `./scripts/contract-check`
- PASS_CONDITION: exit code = 0 且摘要包含 `SERVER_SYNC_OK`
- FAIL_OUTPUT: `SERVER_OPENAPI_MISMATCH`

## RULE-MIGRATION-001

- DESCRIPTION: 迁移目录内所有 SQL 文件必须满足命名与递增规则
- CHECK_METHOD: `./scripts/migration-check`
- PASS_CONDITION: exit code = 0
- FAIL_OUTPUT: `MIGRATION_RULES_FAIL`

## RULE-WEB-API-001

- DESCRIPTION: apps/web 内禁止直连 axios（仅允许 src/api/http.js）
- CHECK_METHOD: `rg -n \"(from\\s+'axios'|require\\(\\s*'axios'\\s*\\))\" apps/web | rg -v \"apps/web/src/api/http\\.js\"`
- PASS_CONDITION: 无输出
- FAIL_OUTPUT: `WEB_AXIOS_DIRECT_IMPORT`

## RULE-SERVER-LAYER-001

- DESCRIPTION: controller 不得直接依赖 mapper
- CHECK_METHOD: `rg -n \"import .*\\.mapper\\.\" apps/server/src/main/java | rg -n \"/controller/\"`
- PASS_CONDITION: 无输出
- FAIL_OUTPUT: `SERVER_LAYER_VIOLATION_CONTROLLER_TO_MAPPER`

## RULE-STATE-COMMIT-001

- DESCRIPTION: Todo commits 字段必须为 7-40 位 git hash
- CHECK_METHOD: `./scripts/state-validate`
- PASS_CONDITION: exit code = 0
- FAIL_OUTPUT: `STATE_INVALID_COMMIT_HASH`

## RULE-LOG-REDACTION-001

- DESCRIPTION: gates 日志落盘必须执行脱敏（password/token/secret/authorization）
- CHECK_METHOD: `./scripts/check --selftest-redaction`
- PASS_CONDITION: selftest exit code = 0
- FAIL_OUTPUT: `LOG_REDACTION_FAIL`

