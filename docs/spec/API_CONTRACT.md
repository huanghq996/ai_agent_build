# API_CONTRACT（契约治理）

## 1. 单一契约源（SSOT）

- OpenAPI：`packages/api-contract/openapi.yaml`
- 错误码：`packages/api-contract/error-codes.json`

## 2. 契约优先顺序（强制）

任何接口变更必须按顺序：
1. 先修改 `openapi.yaml`
2. 再实现 server
3. 再实现 web 调用
4. 通过 `./scripts/contract-check`

## 3. OpenAPI 组织方式（强制）

- `info.version` 必须存在
- `paths` 必须存在
- 每个 path+method 必须有：
  - `operationId`
  - `responses`

## 4. 契约校验（确定性）

`./scripts/contract-check` 必须覆盖：
- YAML 可解析
- 必填字段存在
- `.spectral.yaml` 规则集可解析并被应用（可为“spectral-lite”实现，但输出必须可判定 PASS/FAIL）
- 与 server 实现最小一致性：server controller 中暴露的路径/方法必须出现在 openapi 中

