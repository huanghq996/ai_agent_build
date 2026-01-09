# ERROR_CODES（错误码规范）

## 1. 单一事实来源

- `packages/api-contract/error-codes.json`

## 2. JSON 结构（固定）

本仓库固定采用 **数组** 结构：

```json
[
  {
    "code": "SYS-0001",
    "message": "中文错误信息",
    "httpStatus": 400,
    "deprecated": false
  }
]
```

字段约束（可判定）：
- `code`：字符串，必须唯一
- `message`：字符串（中文）
- `httpStatus`：整数（100-599）
- `deprecated`：布尔值

## 3. 命名规则（可判定）

- 格式：`<MODULE>-<4位数字>`，例如：`SYS-0001`、`AUTH-0001`
- MODULE 仅允许大写字母

## 4. 演进规则（强制）

- 禁止删除已发布 code
- 只能将 `deprecated` 设为 `true`

