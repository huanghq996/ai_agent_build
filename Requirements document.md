# 需求文档：全自动 Claude Code AI 开发团队系统（生产级）

## 0. 核心目标（唯一优先级）

构建一个**全自动 AI 开发团队系统**，在用户只提供需求（或需求增量）后，系统能够自动完成：

1. 需求澄清与冻结（Scope Lock）
2. 任务拆解到“小 Todo”粒度（可提交、可审查、可验收）
3. 自动创建分支并按 Todo 提交（每 Todo 至少 1 commit）
4. 自动调用 Review Agent + 自动门禁（lint/test/build/migration）
5. Review 或门禁失败时，自动回路：
   
    * 汇总失败原因 → PM Agent 自动改写/强化指令 → Dev Agent 修复
    * 通过 `--amend`（优先）或追加 commit 再次审查
    * 循环直到 PASS 或达到“明确终止条件”
6. 全部 Todo 完成后自动出“交付报告”（变更说明、验证命令与结果、风险与回滚）
   
> **模板/规范是支撑**：用于让 agent 不漂移、让 review 有客观标准、让门禁可执行。

---

## 1. 系统边界与运行前提（明确约束）

### 1.1 运行环境与权限

系统运行于 Claude Code（含 sub agents 与 skills 机制），并具备以下能力：

* 可读写本地工作区文件
* 可执行命令（pnpm/mvn/docker 等）
* 可执行 Git 操作（branch/commit/amend/merge/rebase 可配置）
* 可在 PR/CI 环境运行（若接入 GitHub Actions）
  
  若环境不具备某项能力，必须在运行开始时输出**阻断清单**并终止（见 12.2）。
  
### 1.2 技术栈固定（不可漂移）

* Web：Vue3 + Vite + TailwindCSS + Naive UI + Pinia + Axios 封装 + qs + dayjs + **纯 JS**
* Server：Spring Boot + Java21 + MySQL + Redis + MyBatis-Flex + OpenAPI/Swagger + DB Migration（Flyway）
* Monorepo：`apps/web`、`apps/server`、`packages/api-contract`
  
---

## 2. 关键实体（不可变数据结构）

为保证系统可自动化和可判定，所有核心产物必须以结构化格式输出/存储。

### 2.1 Epic / Feature / Todo 定义

* **Epic**：大目标（可能包含多个 Feature）
* **Feature**：用户可感知功能块（包含多个 Todo）
* **Todo**：最小可交付单元（必须满足第 3 章）
  
### 2.2 TODO-ID（强制）

* 格式：`TODO-<数字>`，例如 `TODO-123`
* 每个 Todo 必须有唯一 TODO-ID
* TODO-ID 必须出现在：
  
    * 分支名
    * commit message
    * PR 标题（若使用 PR）
    * 交付报告条目
      
### 2.3 “团队状态文件”（单一事实来源）

系统必须在仓库中维护一个状态文件，作为所有 agent 协作的**单一真相**：

* 路径固定：`docs/ops/ai-team-state.json`
* 内容必须符合后文定义的 JSON Schema（见 2.4）
* 每次状态变更（例如 Todo 状态从 DOING → REVIEW_FAIL）必须落盘写入该文件
  
### 2.4 ai-team-state.json Schema（必须实现）

字段定义（不可缺省）：

```json
{
  "project": {
    "name": "string",
    "repoType": "monorepo",
    "stack": {
      "web": ["vue3","vite","tailwindcss","naive-ui","pinia","axios","qs","dayjs","js"],
      "server": ["spring-boot","java21","mysql","redis","mybatis-flex","flyway","openapi"]
    }
  },
  "workflow": {
    "mode": "full-auto",
    "mergeStrategy": "squash",
    "amendOnReviewFix": true,
    "maxAutoFixCyclesPerTodo": 5
  },
  "epics": [
    {
      "epicId": "EPIC-1",
      "title": "string",
      "features": [
        {
          "featureId": "FEAT-1",
          "title": "string",
          "todos": [
            {
              "todoId": "TODO-123",
              "title": "string",
              "status": "PLANNED|DOING|COMMITTED|REVIEWING|REVIEW_FAIL|GATE_FAIL|DONE|BLOCKED|ABORTED",
              "scope": {
                "in": ["string"],
                "out": ["string"]
              },
              "acceptanceCriteria": ["string"],
              "affectedAreas": {
                "web": ["string"],
                "server": ["string"],
                "contract": ["string"],
                "dbMigration": ["string"]
              },
              "branch": "string",
              "commits": ["string"],
              "review": {
                "lastResult": "PASS|FAIL|NONE",
                "blockers": ["string"],
                "suggestions": ["string"]
              },
              "gates": {
                "lint": "PASS|FAIL|SKIP",
                "test": "PASS|FAIL|SKIP",
                "build": "PASS|FAIL|SKIP",
                "migrationCheck": "PASS|FAIL|SKIP"
              },
              "fixCyclesUsed": 0
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 3. 小 Todo 的严格定义（可判定、无歧义）

一个 Todo 被允许进入 DOING 状态，必须满足以下全部条件（否则标记 BLOCKED）：

1. **范围明确**：`scope.in` 与 `scope.out` 非空且互不冲突
2. **验收标准明确**：`acceptanceCriteria` 至少 3 条，且每条为可验证句子
3. **影响面明确**：affectedAreas 中至少一个非空（web/server/contract/migration）
4. **验证命令明确**：为该 Todo 指定至少 1 条验证命令（见第 8 章脚本标准）
5. **可提交性**：预计改动可在单 PR 内完成（若系统判定超过，必须拆分为多个 Todo）
   
---

## 4. 系统角色与职责（sub agent vs skill 的明确分工）

### 4.1 sub agents（负责决策与上下文）

必须存在以下 sub agent，且职责不可重叠：

1. **PM Agent（主模型/项目经理）**
   
    * 负责：范围冻结、任务分配、回路指令改写、收敛风险、终止决策
2. **Spec Agent（需求拆解/验收定义）**
   
    * 负责：将需求拆成 Todo、写 AC、写接口/页面清单
3. **Architect Agent（契约与边界）**
   
    * 负责：API 契约、错误码、数据模型、迁移策略、跨模块边界
4. **Dev Agent - Web**
   
    * 负责：前端实现，严格遵循 WEB_GUIDE
5. **Dev Agent - Server**
   
    * 负责：后端实现，严格遵循 SERVER_GUIDE
6. **Review Agent（质量守门）**
   
    * 负责：静态审查（规范/结构/安全/一致性），输出 PASS/FAIL
7. **QA Agent（测试与回归）**
   
    * 负责：测试用例清单、边界场景、最小回归集（可先不写自动化但必须写清单）
      
### 4.2 skills（负责确定性执行）

必须存在的 skill 类别（实现形式由你决定，但效果必须可验证）：

* `Skill: RunGates`：统一执行 lint/test/build/migrationCheck，并结构化返回结果
* `Skill: GitOps`：创建分支、提交、amend、生成 PR（如果启用）
* `Skill: ContractSync`：更新/校验 openapi 与 error-codes（保证唯一事实来源）
* `Skill: Report`：生成交付报告（最终输出）
  
> 规则：**agent 不直接“凭感觉说通过/失败”**。门禁必须由 RunGates 产生客观结果；Git 操作必须由 GitOps 执行并返回哈希。

---

## 5. 输入输出协议（所有 agent 必须严格遵守）

### 5.1 PM → Spec/Dev/Review 指令协议（结构化，必须字段齐全）

所有派工指令必须包含以下字段（缺一则判定为 INVALID，系统必须重发）：

```
TODO-ID:
TITLE:
CONTEXT:
SCOPE_IN:
SCOPE_OUT:
AC: (>=3条)
FILES_EXPECTED: (可空，但若已知必须给出)
CONTRACT_CHANGES: (none|describe)
MIGRATION: (none|required with reason)
VERIFY_COMMANDS: (>=1)
COMMIT_MESSAGE:
```

### 5.2 Dev Agent 输出协议（必须含“证据”）

Dev Agent 完成一个 Todo 的实现后，必须输出：

```
TODO-ID:
CHANGES_SUMMARY: (要点列表)
COMMAND_RESULTS: (每条 verify command 的输出摘要 + PASS/FAIL)
GIT:
  BRANCH:
  COMMIT_HASH:
NEXT: (request review)
```

> 禁止只说“已完成”。必须提供命令结果与 commit hash。

### 5.3 Review Agent 输出协议（严格可机器解析）

* PASS：
  
```
RESULT: PASS
CHECKS:
- ...
```

* FAIL：
  
```
RESULT: FAIL
BLOCKERS:
1) ...
2) ...
SUGGESTIONS:
- ...
REQUIRED_CHANGES:
- file: path
  change: exact requirement
VERIFY_COMMANDS:
- ...
```

Review 输出必须包含 `REQUIRED_CHANGES`，且每条都能落到具体文件路径或模块。

---

## 6. 全自动主循环（状态机，必须实现）

系统必须按状态机驱动，每个 Todo 的状态转移如下（不可跳跃）：

1. `PLANNED` → `DOING`：PM 派工给 Dev
2. `DOING` → `COMMITTED`：Dev 完成实现并 commit
3. `COMMITTED` → `REVIEWING`：触发 Review Agent
4. `REVIEWING` → `REVIEW_FAIL`：Review FAIL
5. `REVIEWING` → `GATE_FAIL`：Review PASS，但 RunGates FAIL
6. `REVIEWING` → `DONE`：Review PASS 且 RunGates PASS
7. `REVIEW_FAIL|GATE_FAIL` → `DOING`：PM 改写指令并派工修复（fix cycle +1）
   
### 6.1 自动修复循环上限（必须）

* 每个 Todo 最多自动修复循环 `maxAutoFixCyclesPerTodo` 次（默认 5）
* 达到上限仍 FAIL：Todo 状态设为 `BLOCKED`，并输出阻断报告（见第 12 章）
  
### 6.2 “amend”规则（必须）

当 Todo 在 `REVIEW_FAIL` 或 `GATE_FAIL` 后进入修复：

* 若修改属于“修复/补齐/规范调整”，必须使用 `git commit --amend`
* 若修改属于“新增大块未覆盖内容”，允许追加 commit，但必须同 TODO-ID，且 state.json 记录新 commit hash
  
  由 PM Agent 根据 Review 输出自动判定属于哪类：
  
* 只涉及 REQUIRED_CHANGES 的：视为修复 → amend
* 引入新文件/新模块/新接口：视为扩展 → 追加 commit
  
---

## 7. “范围冻结”与变更控制（避免 AI 发散）

### 7.1 Scope Lock（必须）

在进入 Dev 前，PM 必须写出并落盘：

* `scope.in`：必须实现清单
* `scope.out`：明确不做清单（至少 2 条）
  
  Dev Agent 只能在 `scope.in` 内做事。若发现必须改动超出 scope：
  
* Dev 必须停止并向 PM 报告 “SCOPE_CONFLICT”，不得自行扩大范围
  
### 7.2 变更请求（CR）流程（必须）

当用户追加需求或发现不可行：

* Spec Agent 生成变更请求条目（CR-ID）
* PM 决定：新增 Todo / 修改现有 Todo / 拒绝变更
* 所有变更必须写入 `docs/ops/change-log.md`（按日期追加）
  
---

## 8. 门禁与验证（全自动、可重复）

### 8.1 必须存在统一脚本（单一入口）

仓库根目录必须提供：

* `./scripts/check`：等价于全套门禁
* `./scripts/lint`
* `./scripts/test`
* `./scripts/build`
* `./scripts/migration-check`
  
### 8.2 门禁判定标准（严格）

RunGates skill 必须按以下规则判定：

* lint：任一 package lint 失败 → FAIL
* test：任一必须测试失败 → FAIL
* build：任一 build 失败 → FAIL
* migration-check：检测到迁移脚本不符合命名/顺序/可识别 → FAIL
  
  输出必须结构化写入 `ai-team-state.json` 的 `gates` 字段。
  
---

## 9. Git 自动化与 PR 策略（全自动执行细则）

### 9.1 分支命名（强制）

`<type>/TODO-<id>-<kebab-desc>`

* type ∈ {feat, fix, chore}
  
### 9.2 commit message（强制）

Conventional Commits + scope + TODO-ID：

* `feat(web): TODO-123 ...`
* `feat(server): TODO-123 ...`
* `chore: TODO-123 ...`
  
### 9.3 合并策略（强制）

* `mergeStrategy = squash`
* squash 后标题必须保留 TODO-ID
* 合并前必须满足：Review PASS + Gates PASS
  
---

## 10. 契约治理（生产级最优方案：契约先行，自动校验）

### 10.1 单一契约源（必须）

* `packages/api-contract/openapi.yaml` 为接口唯一事实来源
* `packages/api-contract/error-codes.json` 为错误码唯一事实来源
  
### 10.2 契约更新顺序（必须）

凡涉及新增/修改接口：

1. Architect Agent 先修改 openapi.yaml（并更新必要 schema）
2. Dev Agent - Server 实现接口
3. Dev Agent - Web 调用接口
4. RunGates 增加“契约一致性检查”（可基于 openapi 生成/比对）
   
---

## 11. 模板与规范文件（作为团队“宪法”，不可缺失）

这些文件必须存在，且 Review Agent 必须以它们作为审查依据：

* `docs/spec/WORKFLOW.md`
* `docs/spec/DEFINITION_OF_DONE.md`
* `docs/spec/WEB_GUIDE.md`
* `docs/spec/SERVER_GUIDE.md`
* `docs/spec/API_CONTRACT.md`
* `docs/spec/ERROR_CODES.md`
* `docs/spec/REVIEW_CHECKLIST.md`
  
> 本版本不再赘述每个文件内容清单（上一版已有），但在实施时仍必须生成并覆盖生产级细则；Review Checklist 必须能判定 PASS/FAIL。

---

## 12. 终止条件、阻断与报告（必须输出、不可含糊）

### 12.1 终止条件（必须）

系统必须在以下任一条件满足时终止自动循环，并输出终止报告：

* 某 Todo `fixCyclesUsed` 达到上限仍 FAIL → BLOCKED
* 环境缺失关键能力（如没有 pnpm/mvn/docker/mysql）且无法自动安装/启动 → BLOCKED
* 发现需求与技术栈矛盾且无法在 scope 内解决 → BLOCKED
  
### 12.2 阻断报告格式（严格）

```
STATUS: BLOCKED
TODO-ID: TODO-xxx (若适用)
REASON:
- ...
REQUIRED_USER_ACTION:
- ...
EVIDENCE:
- command output summary / logs
```

### 12.3 交付报告（全部 DONE 时必须生成）

当所有 Todo 为 DONE，必须生成 `docs/ops/delivery-report.md`，包含：

* 完成的 Todo 列表（TODO-ID、标题、commit hash）
* 关键变更点（web/server/contract/migration）
* 门禁执行记录摘要（每类 PASS）
* 回滚说明（涉及迁移必须列出）
* 已知风险与后续建议（必须具体，不允许空泛）
  
---

## 13. 生产级非功能性要求（必须纳入 Review Checklist）

### 13.1 安全与隐私（必须）

* 日志不得输出敏感字段（token/password）
* Redis key 必须带前缀与 TTL
* 全局异常必须带 traceId
* API 错误信息对外不可暴露堆栈
  
### 13.2 可维护性（必须）

* 代码必须遵循目录边界，不允许跨层调用（controller 不能直连 mapper）
* API 调用必须走 axios 封装（web）
* 迁移脚本必须可追溯、可审计
  
---

## 14. 实施任务拆解（给 Codex/Claude Code 的执行计划）

系统实现必须按以下顺序执行（不可乱序）：

1. 初始化仓库结构与状态文件 `docs/ops/ai-team-state.json`
2. 生成规范“宪法”文档（docs/spec/*）
3. 生成模板工程（apps/web、apps/server、packages/api-contract）
4. 生成脚本（scripts/*）并确保可运行
5. 实现 skills：RunGates、GitOps、ContractSync、Report（效果可验证即可）
6. 实现主循环驱动（按第 6 章状态机）
7. 自检：跑一条示例 Todo（例如：新增健康检查接口 + 前端展示），验证闭环可自动完成并产生交付报告
   
---

## 15. 验收标准（系统级，必须全部满足）

### 15.1 自动闭环验收（必须）

给系统输入一个包含至少 3 个 Todo 的需求（同时包含 web+server+contract+迁移至少各 1 项），系统必须能：

* 自动拆解与落盘 state.json
* 每个 Todo 自动分支+提交+审查+门禁
* 至少触发 1 次故意失败（例如 lint 失败）并自动修复成功
* 最终所有 Todo DONE 并生成 delivery-report.md
  
### 15.2 可重复性验收（必须）

在干净环境重新 clone 仓库，执行 `./scripts/check`，必须 PASS。

### 15.3 无歧义验收（必须）

Review Agent 仅依赖 docs/spec 与 state.json，即可稳定判定 PASS/FAIL，不允许出现“看情况”“建议”类主观结论。


## 16. 运行配置文件（必须，唯一可调参数源）

### 16.1 配置文件路径（强制）

* 路径固定：`docs/ops/ai-team-config.json`
* 规则：
  
    1. **任何会影响流程行为的参数**（是否 PR、最大循环、门禁命令、合并策略、基础分支、并发策略、日志策略……）都必须在此文件中声明。
    2. 除该文件外，任何 agent/skill/脚本不得硬编码流程参数。
    3. config 未通过 Schema 校验：系统必须终止并输出阻断报告（按 12.2 格式）。
       
### 16.2 ai-team-config.json（生产默认值规范，字段不可缺省）

> 下方是“完整默认值样例”，可以作为仓库初始版本直接落盘。

```json
{
  "version": "1.0.0",
  "project": {
    "name": "ai-team-monorepo",
    "repoType": "monorepo",
    "baseBranch": "main",
    "timezone": "Asia/Shanghai"
  },
  "toolchain": {
    "node": {
      "versionFile": ".nvmrc",
      "packageManager": "pnpm",
      "pnpmVersion": "9.15.0",
      "corepack": true
    },
    "java": {
      "version": 21,
      "mavenWrapper": true,
      "mavenArgs": "-B -ntp"
    }
  },
  "workflow": {
    "mode": "full-auto",
    "usePR": false,
    "requireRemote": false,
    "mergeStrategy": "squash",
    "amendOnReviewFix": true,
    "maxAutoFixCyclesPerTodo": 5,
    "execution": {
      "parallelTodos": false,
      "maxParallel": 1
    },
    "git": {
      "branchPrefix": "",
      "branchTypes": ["feat", "fix", "chore"],
      "commitScopes": ["web", "server", "contract", "ops"],
      "allowRebase": false
    }
  },
  "gates": {
    "required": ["lint", "test", "build", "migrationCheck", "contractCheck", "stateSchemaCheck", "configSchemaCheck"],
    "commands": {
      "check": "./scripts/check",
      "lint": "./scripts/lint",
      "test": "./scripts/test",
      "build": "./scripts/build",
      "migrationCheck": "./scripts/migration-check",
      "contractCheck": "./scripts/contract-check",
      "stateSchemaCheck": "./scripts/state-validate",
      "configSchemaCheck": "./scripts/config-validate"
    },
    "policies": {
      "failFast": true,
      "allowSkip": ["test"],
      "skipReasonRequired": true
    }
  },
  "logging": {
    "dir": "docs/ops/logs",
    "keepDays": 30,
    "keepLatestPerTodo": 50,
    "captureStdout": true,
    "captureStderr": true,
    "redactions": {
      "enabled": true,
      "patterns": [
        "(?i)password\\s*[:=]\\s*[^\\s]+",
        "(?i)token\\s*[:=]\\s*[^\\s]+",
        "(?i)secret\\s*[:=]\\s*[^\\s]+",
        "(?i)authorization\\s*[:=]\\s*[^\\s]+"
      ]
    }
  },
  "contracts": {
    "openapiPath": "packages/api-contract/openapi.yaml",
    "errorCodesPath": "packages/api-contract/error-codes.json",
    "spectralRulesPath": "packages/api-contract/.spectral.yaml",
    "generated": {
      "enabled": true,
      "webClientOutDir": "apps/web/src/api/generated"
    }
  },
  "migrations": {
    "enabled": true,
    "tool": "flyway",
    "location": "apps/server/src/main/resources/db/migration",
    "naming": {
      "mode": "timestamp",
      "pattern": "^V\\d{14}__([a-z0-9]+(-[a-z0-9]+)*)\\.sql$",
      "example": "V20260109103045__create_user_table.sql"
    },
    "rules": {
      "noOutOfOrder": true,
      "noRepeatable": true,
      "nonEmptySql": true
    }
  },
  "demo": {
    "enabled": true,
    "todo": {
      "todoId": "TODO-9001",
      "title": "Health Check API + Web Display",
      "scopeIn": [
        "新增 GET /health 接口，返回 {status:'ok', time:'ISO8601'}",
        "web 页面展示 health 状态与时间",
        "openapi.yaml 与 error-codes.json（如需要）同步",
        "通过 scripts/check"
      ],
      "scopeOut": [
        "不做登录鉴权",
        "不做国际化",
        "不做复杂 UI 设计"
      ]
    }
  }
}
```

---

## 17. Schema 校验（必须，config/state 都必须可机器校验）

### 17.1 Schema 文件路径（强制）

* `docs/ops/schema/ai-team-config.schema.json`
* `docs/ops/schema/ai-team-state.schema.json`
  
### 17.2 `./scripts/config-validate`（必须）

* 功能：对 `docs/ops/ai-team-config.json` 进行 JSON Schema 校验
* 失败即退出码非 0，并输出校验错误明细（至少包含：路径、期望、实际）
  
### 17.3 `./scripts/state-validate`（必须）

* 功能：对 `docs/ops/ai-team-state.json` 进行 JSON Schema 校验
* 失败即退出码非 0，并输出校验错误明细
  
---

## 18. ai-team-config.schema.json（完整 Schema，禁止额外字段）

> 这是**可直接落盘**的生产级 Schema（严格 required + additionalProperties=false）。
> 如需扩展，必须先升级 schema version，并在变更日志记录。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "ai-team-config.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["version", "project", "toolchain", "workflow", "gates", "logging", "contracts", "migrations", "demo"],
  "properties": {
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "project": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "repoType", "baseBranch", "timezone"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "repoType": { "const": "monorepo" },
        "baseBranch": { "type": "string", "minLength": 1 },
        "timezone": { "type": "string", "minLength": 1 }
      }
    },
    "toolchain": {
      "type": "object",
      "additionalProperties": false,
      "required": ["node", "java"],
      "properties": {
        "node": {
          "type": "object",
          "additionalProperties": false,
          "required": ["versionFile", "packageManager", "pnpmVersion", "corepack"],
          "properties": {
            "versionFile": { "type": "string", "minLength": 1 },
            "packageManager": { "const": "pnpm" },
            "pnpmVersion": { "type": "string", "minLength": 1 },
            "corepack": { "type": "boolean" }
          }
        },
        "java": {
          "type": "object",
          "additionalProperties": false,
          "required": ["version", "mavenWrapper", "mavenArgs"],
          "properties": {
            "version": { "type": "integer", "const": 21 },
            "mavenWrapper": { "type": "boolean" },
            "mavenArgs": { "type": "string" }
          }
        }
      }
    },
    "workflow": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mode", "usePR", "requireRemote", "mergeStrategy", "amendOnReviewFix", "maxAutoFixCyclesPerTodo", "execution", "git"],
      "properties": {
        "mode": { "const": "full-auto" },
        "usePR": { "type": "boolean" },
        "requireRemote": { "type": "boolean" },
        "mergeStrategy": { "enum": ["squash"] },
        "amendOnReviewFix": { "type": "boolean" },
        "maxAutoFixCyclesPerTodo": { "type": "integer", "minimum": 1, "maximum": 20 },
        "execution": {
          "type": "object",
          "additionalProperties": false,
          "required": ["parallelTodos", "maxParallel"],
          "properties": {
            "parallelTodos": { "type": "boolean" },
            "maxParallel": { "type": "integer", "minimum": 1, "maximum": 8 }
          }
        },
        "git": {
          "type": "object",
          "additionalProperties": false,
          "required": ["branchPrefix", "branchTypes", "commitScopes", "allowRebase"],
          "properties": {
            "branchPrefix": { "type": "string" },
            "branchTypes": {
              "type": "array",
              "items": { "enum": ["feat", "fix", "chore"] },
              "minItems": 1
            },
            "commitScopes": {
              "type": "array",
              "items": { "type": "string", "minLength": 1 },
              "minItems": 1
            },
            "allowRebase": { "type": "boolean" }
          }
        }
      }
    },
    "gates": {
      "type": "object",
      "additionalProperties": false,
      "required": ["required", "commands", "policies"],
      "properties": {
        "required": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "minItems": 1
        },
        "commands": {
          "type": "object",
          "additionalProperties": false,
          "required": ["check", "lint", "test", "build", "migrationCheck", "contractCheck", "stateSchemaCheck", "configSchemaCheck"],
          "properties": {
            "check": { "type": "string", "minLength": 1 },
            "lint": { "type": "string", "minLength": 1 },
            "test": { "type": "string", "minLength": 1 },
            "build": { "type": "string", "minLength": 1 },
            "migrationCheck": { "type": "string", "minLength": 1 },
            "contractCheck": { "type": "string", "minLength": 1 },
            "stateSchemaCheck": { "type": "string", "minLength": 1 },
            "configSchemaCheck": { "type": "string", "minLength": 1 }
          }
        },
        "policies": {
          "type": "object",
          "additionalProperties": false,
          "required": ["failFast", "allowSkip", "skipReasonRequired"],
          "properties": {
            "failFast": { "type": "boolean" },
            "allowSkip": { "type": "array", "items": { "type": "string" } },
            "skipReasonRequired": { "type": "boolean" }
          }
        }
      }
    },
    "logging": {
      "type": "object",
      "additionalProperties": false,
      "required": ["dir", "keepDays", "keepLatestPerTodo", "captureStdout", "captureStderr", "redactions"],
      "properties": {
        "dir": { "type": "string", "minLength": 1 },
        "keepDays": { "type": "integer", "minimum": 1, "maximum": 365 },
        "keepLatestPerTodo": { "type": "integer", "minimum": 1, "maximum": 500 },
        "captureStdout": { "type": "boolean" },
        "captureStderr": { "type": "boolean" },
        "redactions": {
          "type": "object",
          "additionalProperties": false,
          "required": ["enabled", "patterns"],
          "properties": {
            "enabled": { "type": "boolean" },
            "patterns": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },
    "contracts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["openapiPath", "errorCodesPath", "spectralRulesPath", "generated"],
      "properties": {
        "openapiPath": { "type": "string", "minLength": 1 },
        "errorCodesPath": { "type": "string", "minLength": 1 },
        "spectralRulesPath": { "type": "string", "minLength": 1 },
        "generated": {
          "type": "object",
          "additionalProperties": false,
          "required": ["enabled", "webClientOutDir"],
          "properties": {
            "enabled": { "type": "boolean" },
            "webClientOutDir": { "type": "string", "minLength": 1 }
          }
        }
      }
    },
    "migrations": {
      "type": "object",
      "additionalProperties": false,
      "required": ["enabled", "tool", "location", "naming", "rules"],
      "properties": {
        "enabled": { "type": "boolean" },
        "tool": { "const": "flyway" },
        "location": { "type": "string", "minLength": 1 },
        "naming": {
          "type": "object",
          "additionalProperties": false,
          "required": ["mode", "pattern", "example"],
          "properties": {
            "mode": { "enum": ["timestamp"] },
            "pattern": { "type": "string", "minLength": 1 },
            "example": { "type": "string", "minLength": 1 }
          }
        },
        "rules": {
          "type": "object",
          "additionalProperties": false,
          "required": ["noOutOfOrder", "noRepeatable", "nonEmptySql"],
          "properties": {
            "noOutOfOrder": { "type": "boolean" },
            "noRepeatable": { "type": "boolean" },
            "nonEmptySql": { "type": "boolean" }
          }
        }
      }
    },
    "demo": {
      "type": "object",
      "additionalProperties": false,
      "required": ["enabled", "todo"],
      "properties": {
        "enabled": { "type": "boolean" },
        "todo": {
          "type": "object",
          "additionalProperties": false,
          "required": ["todoId", "title", "scopeIn", "scopeOut"],
          "properties": {
            "todoId": { "type": "string", "pattern": "^TODO-\\d+$" },
            "title": { "type": "string", "minLength": 1 },
            "scopeIn": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 },
            "scopeOut": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 }
          }
        }
      }
    }
  }
}
```

---

## 19. ai-team-state.schema.json

### 19.1 关键强化点（相对 V2）

* 所有 enum 固化；所有 required 固化；禁止额外字段（`additionalProperties=false`）
* `todo.branch` 必须匹配分支命名规范
* `commits` 必须是合法 git hash（允许短 hash，但推荐 7-40）
* `fixCyclesUsed` 必须与状态机一致（进入 DOING 视作 cycle 次数由 PM 增量）
* `gates` 必须包含 config 里 required gates（不允许漏写）
  
  以下是schema 核心定义，你需要继续展开到每个子字段最细
  
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "ai-team-state.schema.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["project", "workflow", "epics"],
  "properties": {
    "project": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "repoType", "stack"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "repoType": { "const": "monorepo" },
        "stack": {
          "type": "object",
          "additionalProperties": false,
          "required": ["web", "server"],
          "properties": {
            "web": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
            "server": { "type": "array", "items": { "type": "string" }, "minItems": 1 }
          }
        }
      }
    },
    "workflow": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mode", "mergeStrategy", "amendOnReviewFix", "maxAutoFixCyclesPerTodo"],
      "properties": {
        "mode": { "const": "full-auto" },
        "mergeStrategy": { "enum": ["squash"] },
        "amendOnReviewFix": { "type": "boolean" },
        "maxAutoFixCyclesPerTodo": { "type": "integer", "minimum": 1, "maximum": 20 }
      }
    },
    "epics": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["epicId", "title", "features"],
        "properties": {
          "epicId": { "type": "string", "pattern": "^EPIC-\\d+$" },
          "title": { "type": "string", "minLength": 1 },
          "features": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["featureId", "title", "todos"],
              "properties": {
                "featureId": { "type": "string", "pattern": "^FEAT-\\d+$" },
                "title": { "type": "string", "minLength": 1 },
                "todos": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "todoId","title","status","scope","acceptanceCriteria","affectedAreas",
                      "branch","commits","review","gates","fixCyclesUsed"
                    ],
                    "properties": {
                      "todoId": { "type": "string", "pattern": "^TODO-\\d+$" },
                      "title": { "type": "string", "minLength": 1 },
                      "status": {
                        "enum": ["PLANNED","DOING","COMMITTED","REVIEWING","REVIEW_FAIL","GATE_FAIL","DONE","BLOCKED","ABORTED"]
                      },
                      "scope": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["in", "out"],
                        "properties": {
                          "in": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 },
                          "out": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 }
                        }
                      },
                      "acceptanceCriteria": { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 3 },
                      "affectedAreas": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["web","server","contract","dbMigration"],
                        "properties": {
                          "web": { "type": "array", "items": { "type": "string" } },
                          "server": { "type": "array", "items": { "type": "string" } },
                          "contract": { "type": "array", "items": { "type": "string" } },
                          "dbMigration": { "type": "array", "items": { "type": "string" } }
                        }
                      },
                      "branch": {
                        "type": "string",
                        "pattern": "^(feat|fix|chore)/TODO-\\d+-[a-z0-9]+(-[a-z0-9]+)*$"
                      },
                      "commits": {
                        "type": "array",
                        "items": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" }
                      },
                      "review": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["lastResult","blockers","suggestions"],
                        "properties": {
                          "lastResult": { "enum": ["PASS","FAIL","NONE"] },
                          "blockers": { "type": "array", "items": { "type": "string" } },
                          "suggestions": { "type": "array", "items": { "type": "string" } }
                        }
                      },
                      "gates": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["lint","test","build","migrationCheck","contractCheck","stateSchemaCheck","configSchemaCheck"],
                        "properties": {
                          "lint": { "enum": ["PASS","FAIL","SKIP"] },
                          "test": { "enum": ["PASS","FAIL","SKIP"] },
                          "build": { "enum": ["PASS","FAIL","SKIP"] },
                          "migrationCheck": { "enum": ["PASS","FAIL","SKIP"] },
                          "contractCheck": { "enum": ["PASS","FAIL","SKIP"] },
                          "stateSchemaCheck": { "enum": ["PASS","FAIL","SKIP"] },
                          "configSchemaCheck": { "enum": ["PASS","FAIL","SKIP"] }
                        }
                      },
                      "fixCyclesUsed": { "type": "integer", "minimum": 0, "maximum": 20 }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 20. Monorepo 工程与版本锁定（必须，保证可重复）

### 20.1 必须存在的根目录文件（缺一阻断）

* `.nvmrc`（node 版本）
* `pnpm-workspace.yaml`
* `package.json`（必须含 `packageManager` 字段锁定 pnpm 版本）
* `apps/web/package.json`
* `apps/server/pom.xml` + `apps/server/mvnw`（如启用 Maven Wrapper）
* `packages/api-contract/*`
* `scripts/*`（第 21 章定义）
  
### 20.2 pnpm-workspace.yaml（强制）

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

### 20.3 根 package.json（强制脚本接口）

必须至少包含（可追加但不得改名）：

* `lint`, `test`, `build`, `contract:check`, `state:validate`, `config:validate`
* 且 `./scripts/*` 只调用这些入口，不得散落自定义命令
  
---

## 21. scripts 规范（必须，单一入口，机器可判定）

### 21.1 scripts 目录（强制）

* 所有脚本必须可在仓库根目录执行：`./scripts/<name>`
* 脚本必须满足：
  
    1. exit code：0=PASS，非 0=FAIL
    2. 必须输出一段简短摘要到 stdout（便于日志检索）
    3. 必须将完整输出落盘到 `docs/ops/logs/...`（见第 22 章）
       
### 21.2 必须实现的脚本清单（强制）

* `./scripts/check`：顺序执行所有 required gates（来自 config.gates.required）
* `./scripts/lint`
* `./scripts/test`
* `./scripts/build`
* `./scripts/migration-check`
* `./scripts/contract-check`
* `./scripts/state-validate`
* `./scripts/config-validate`
  
### 21.3 check 的执行顺序（强制，且与 config 同步）

默认顺序（可配置但必须固定化）：
`config-validate` → `state-validate` → `contract-check` → `migration-check` → `lint` → `test` → `build`

---

## 22. 日志证据留存（必须，生产可追溯）

### 22.1 目录结构（强制）

所有命令执行必须按如下结构落盘（缺失视为门禁 FAIL）：

* `docs/ops/logs/<TODO-ID>/<YYYYMMDD-HHMMSS>/gates/<gate>.log`
* `docs/ops/logs/<TODO-ID>/<YYYYMMDD-HHMMSS>/review/review.md`
* `docs/ops/logs/<TODO-ID>/<YYYYMMDD-HHMMSS>/git/git.log`
* `docs/ops/logs/system/<YYYYMMDD-HHMMSS>/run.log`
  
### 22.2 脱敏（强制）

* 若 `config.logging.redactions.enabled=true`：脚本必须在落盘前对 stdout/stderr 做正则脱敏（按 config.patterns）
* 脱敏失败：阻断（防止泄露）
  
### 22.3 保留策略（强制）

* 自动清理策略：保留 `keepDays` 天内日志，并且每个 TODO 至多保留 `keepLatestPerTodo` 份运行记录
* 清理动作由 `./scripts/check` 在开始前执行（或提供 `./scripts/logs-prune` 作为内部步骤）
  
---

## 23. Flyway 迁移规范（生产级、可校验）

### 23.1 迁移目录（强制）

* 迁移脚本目录必须为：`apps/server/src/main/resources/db/migration`
  
### 23.2 命名规范（强制）

* 使用 timestamp 模式（与 config 一致）：
  
    * `VYYYYMMDDHHMMSS__kebab-name.sql`
* 必须符合 config.migrations.naming.pattern
* 必须包含至少一条有效 SQL（禁止空文件、只有注释视为空）
  
### 23.3 migration-check 校验项（强制 PASS/FAIL）

必须校验并 FAIL：

1. 文件名不匹配 pattern
2. timestamp 不递增（存在 out-of-order）且 config.rules.noOutOfOrder=true
3. 存在 repeatable migration（以 `R__` 开头）且 config.rules.noRepeatable=true
4. 空文件/空 SQL
5. 同一 timestamp 重复
   
---

## 24. 契约治理细则（生产级：校验 + 生成 + 一致性）

### 24.1 OpenAPI 校验（强制）

`./scripts/contract-check` 必须包含：

* OpenAPI 结构校验（yaml 可解析、必填字段齐全）
* Spectral 规则校验（使用 `packages/api-contract/.spectral.yaml`）
* 与 server 实现一致性校验（最少要求：所有 controller 暴露的路径/方法必须在 openapi 存在；若做不到反射解析，则至少保证新增/变更接口必须先改 openapi，Review 必须检查到）
  
### 24.2 生成客户端（强制，若 config.contracts.generated.enabled=true）

* 根据 openapi 生成 web 的 API client 到 `apps/web/src/api/generated`
* 生成物必须可被 lint/build 通过
* 生成物禁止手改：必须加注释头（例如 `// Generated by ... DO NOT EDIT`）
  
### 24.3 error-codes.json 规范（强制）

* 必须为数组或对象（二选一，但必须写死并在 ERROR_CODES.md 定义）
* 必须校验：
  
    * code 唯一
    * 每个 code 必须有 message（中文）与 httpStatus
    * 禁止删除已发布 code（只能标记 deprecated）
      
---

## 25. Review 机制落地（生产级：确定性为主，LLM 为辅）

### 25.1 Review 分两层（强制）

1. **Deterministic Review（硬规则审查）**：必须机器可执行
2. **LLM Review（文字建议）**：可选，但不得作为唯一 gate
   
### 25.2 Deterministic Review 必须覆盖的规则（FAIL 即阻断）

* 目录边界：
  
    * server：controller/service/mapper 分层禁止跨层直连（controller 不得直接依赖 mapper）
    * web：API 调用必须走 axios 封装层（在 WEB_GUIDE 明确路径）
* 变更一致性：
  
    * 变更接口 => openapi.yaml 必须同时变更
    * 变更错误 => error-codes.json 必须同步
    * 变更迁移 => migration-check 必须 PASS
* 状态一致性：
  
    * 每次 commit 后必须更新 state.json（commit hash、状态）
    * state/config schema 校验必须 PASS
* 安全：日志脱敏、traceId、错误响应不暴露堆栈
  
### 25.3 Review 输出必须落盘（强制）

* 保存到：`docs/ops/logs/<TODO-ID>/<run>/review/review.md`
* 并将关键信息同步写入 state.json 的 `review.*`
  
---

## 26. “宪法文件”生产级内容清单（必须补全，直接用于 PASS/FAIL）

### 26.1 `docs/spec/WORKFLOW.md`（必须包含）

* 状态机：每个状态的进入条件、退出条件、允许的下一跳
* Fix cycle：计数规则、amend/追加 commit 判定规则
* PR 策略：usePR true/false 两种模式的行为差异（必须写清）
* 终止条件：与 12.1 对齐
  
### 26.2 `docs/spec/DEFINITION_OF_DONE.md`

* 对每个 Todo 的 DoD：必须满足哪些门禁、哪些文档同步、哪些日志证据必须存在
* 对系统级 DoD：第 15 章验收项逐条映射到可执行命令/文件证据
  
### 26.3 `docs/spec/WEB_GUIDE.md`

* 技术栈固定
* 目录结构规范：页面、组件、store、api、utils 的固定路径
* axios 封装路径与用法（强制）
* 错误处理与统一提示规范（对接 error-codes）
* lint 规则：必须用哪些 eslint 规则、禁止哪些写法（例如 any、未使用变量等）
  
### 26.4 `docs/spec/SERVER_GUIDE.md`

* 三层结构：controller/service/mapper 规则
* 统一响应格式（如 `ApiResponse<T>`）
* 全局异常处理：必须带 traceId，外部不暴露堆栈
* Redis key 前缀与 TTL 强制策略
* Flyway 规则与迁移模板
  
### 26.5 `docs/spec/API_CONTRACT.md`

* openapi.yaml 的组织方式（tags、schemas、responses）
* 版本策略（例如 `/api/v1` 或 openapi info.version）
* 契约优先顺序：先改 openapi 再实现（强制）
  
### 26.6 `docs/spec/ERROR_CODES.md`

* error-codes.json 的结构定义与示例
* code 命名规则、模块前缀规则
* deprecated 策略（不可删除）
  
### 26.7 `docs/spec/REVIEW_CHECKLIST.md`（必须机器可判定）

必须以“可判定条目”写：每条包含：

* RULE_ID
* DESCRIPTION
* CHECK_METHOD（命令/grep/脚本）
* PASS_CONDITION
* FAIL_OUTPUT（失败时打印什么）
  
> 例：
> `RULE-WEB-API-001`：检查 `apps/web` 内所有请求必须走 `src/api/http.js`（检查方法：grep 直连 axios 视为 FAIL）

---

## 27. 主循环驱动（必须提供 CLI，可一次跑通 demo）

### 27.1 必须提供的 CLI 命令（强制）

建议固定入口：`./scripts/ai-team`，必须支持：

* `./scripts/ai-team init`：初始化 state/config/schema/spec/scripts 等骨架
* `./scripts/ai-team plan`：根据输入需求生成 epics/features/todos 并落盘 state.json
* `./scripts/ai-team run`：驱动状态机直到 DONE/BLOCKED（写日志证据）
* `./scripts/ai-team gates --todo TODO-xxx`：只跑门禁并写回 state.json
* `./scripts/ai-team report`：生成 delivery-report.md
  
### 27.2 run 的确定性要求（强制）

* 默认 **串行执行** todos（除非 config.workflow.execution.parallelTodos=true）
* 每一次状态迁移必须：
  
    1. 写入 state.json
    2. 落盘日志证据
    3. 输出一行摘要到 stdout（便于 grep）
       
---

## 28. CI 接入（生产建议：可选启用，但规范必须写清）

若你准备接 GitHub Actions，要求：

* `.github/workflows/ci.yml` 必须执行 `./scripts/check`
* CI 失败等价于 gate fail
* 若 usePR=true：必须在 PR 上跑 CI 并阻止合并
  
  （如果你暂时不开 CI，usePR=false 也没问题，但 WORKFLOW.md 必须写清两种模式差异。）
  
---

## 29. 补充验收

新增系统级验收项（必须全部满足）：

1. `./scripts/check` 能在干净环境运行，且日志证据目录结构完全符合第 22 章
2. `./scripts/state-validate` 与 `./scripts/config-validate` 必须纳入 gates.required，并且在 `ai-team-state.json` 的 gates 字段可见
3. demo todo（config.demo.enabled=true）必须能跑通：
   
    * 生成 openapi 变更
    * server 实现
    * web 展示
    * 最终 delivery-report.md 写明 commit hash、验证命令与结果、日志路径