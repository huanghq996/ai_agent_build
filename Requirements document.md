# 需求文档：全自动 Claude Code AI 开发团队系统（生产级）

## 0. 核心理念（Native Mode）

本系统利用 **Claude Code** 本身作为核心智能引擎，构建一个**全自动 AI 开发团队系统**.

*   **Driver（驱动者）**: Claude Code (CLI) 本身，由用户 Prompt 驱动。
*   **Constitution（宪法）**: `CLAUDE.md` (定义 Agent 行为与角色)。
*   **Muscles（执行力）**: Deterministic Scripts (`./scripts/*`) + `tools/state_manager.py`。
*   **Memory（记忆）**: `docs/ops/ai-team-state.json` (作为唯一的项目状态源)。

在用户只提供需求（或需求增量）后，系统能够自动完成：

1. 需求澄清与冻结（Scope Lock）
2. 任务拆解到“小 Todo”粒度（可提交、可审查、可验收）
3. 自动创建分支并按 Todo 提交（每 Todo 至少 1 commit）
4. 自动调用 Review Agent + 自动门禁（lint/test/build/migration）
5. Review 或门禁失败时，自动回路：

    * 汇总失败原因 → PM Agent 自动改写/强化指令 → Dev Agent 修复
    * 通过 `--amend`（优先）或追加 commit 再次审查
    * 循环直到 PASS 或达到“明确终止条件”
6. 全部 Todo 完成后自动出“交付报告”（变更说明、验证命令与结果、风险与回滚）

---

## 1. 核心目标

用户输入需求后，Claude Code 根据预定义角色（PM/Dev/QA），自动执行以下循环：

1.  **Analyst Mode (PM)**: 读取需求 -> 拆解 Todo -> 更新 `ai-team-state.json`。
2.  **Dev Mode (Dev)**: 领取 Todo -> 切换分支 -> 编写代码 -> 提交。
3.  **Review Mode (QA)**: 运行静态检查 (`./scripts/check`) -> agent审查 -> 修正。
4.  **Delivery**: 所有 Todo 完成 -> 生成交付报告。

---

## 2. 系统角色与职责（sub agent vs skill 的明确分工）

### 2.1 sub agents（负责决策与上下文）

必须存在以下 sub agent，且职责不可重叠. 为每个 sub agent 定义权限、职责。

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

### 2.2 skills（负责确定性执行）

必须存在的 skill 类别（实现形式由你决定，但效果必须可验证）：

* `Skill: RunGates`：统一执行 lint/test/build/migrationCheck，并结构化返回结果
* `Skill: GitOps`：创建分支、提交、amend、生成 PR（如果启用）
* `Skill: ContractSync`：更新/校验 openapi 与 error-codes（保证唯一事实来源）
* `Skill: Report`：生成交付报告（最终输出）

> 规则：**agent 不直接“凭感觉说通过/失败”**。门禁必须由 RunGates 产生客观结果；Git 操作必须由 GitOps 执行并返回哈希。

---

## 3. 系统边界与运行前提（明确约束）

### 3.1 运行环境与权限

系统运行于 Claude Code 环境，并具备以下能力：

*   可读写本地工作区文件
*   可执行命令（pnpm/mvn/docker/python3 等）
*   可执行 Git 操作（branch/commit/merge 等）

### 3.2 技术栈固定（不可漂移）

*   **Web**：Vue3 + Vite + TailwindCSS + Naive UI + Pinia + Axios 封装 + qs + dayjs + **纯 JS**
*   **Server**：Spring Boot + Java21 + MySQL + Redis + MyBatis-Flex + OpenAPI/Swagger + Flyway
*   **Monorepo**：`apps/web`、`apps/server`、`packages/api-contract`

---

## 4. 关键实体（不可变数据结构）

为保证系统可自动化和可判定，所有核心产物必须以结构化格式输出/存储。

### 4.1 Epic / Feature / Todo 定义

* **Epic**：大目标（可能包含多个 Feature）
* **Feature**：用户可感知功能块（包含多个 Todo）
* **Todo**：最小可交付单元（必须满足第 3 章）

### 4.2 TODO-ID（强制）

* 格式：`TODO-<数字>`，例如 `TODO-123`
* 每个 Todo 必须有唯一 TODO-ID
* TODO-ID 必须出现在：

    * 分支名
    * commit message
    * PR 标题（若使用 PR）
    * 交付报告条目

### 4.3 “团队状态文件”（单一事实来源）

系统必须在仓库中维护一个状态文件，作为所有 agent 协作的**单一真相**：

* 路径固定：`docs/ops/ai-team-state.json`
* 内容必须符合后文定义的 JSON Schema（见 4.4）
* 每次状态变更（例如 Todo 状态从 DOING → REVIEW_FAIL）必须落盘写入该文件
* **操作规则**：禁止 Claude 直接编辑 JSON 文本，**必须**使用 `tools/state_manager.py` 工具进行读写，以确保 Schema 一致性。

---

## 5. 小 Todo 的严格定义（可判定、无歧义）

一个 Todo 被允许进入 DOING 状态，必须满足以下全部条件（否则标记 BLOCKED）：

1. **范围明确**：`scope.in` 与 `scope.out` 非空且互不冲突
2. **验收标准明确**：`acceptanceCriteria` 至少 3 条，且每条为可验证句子
3. **影响面明确**：affectedAreas 中至少一个非空（web/server/contract/migration）
4. **验证命令明确**：为该 Todo 指定至少 1 条验证命令（见第 8 章脚本标准）
5. **可提交性**：预计改动可在单 PR 内完成（若系统判定超过，必须拆分为多个 Todo）

## 6. 输入输出协议（所有 agent 必须严格遵守）

### 6.1 PM → Spec/Dev/Review 指令协议（结构化，必须字段齐全）

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

### 6.2 Dev Agent 输出协议（必须含“证据”）

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

### 6.3 Review Agent 输出协议（严格可机器解析）

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

# 9. Git 自动化与 PR 策略（全自动执行细则）

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

## 10. 契约治理（Contract First）

1.  **Swagger/OpenAPI** (`packages/api-contract/openapi.yaml`) 是接口的**法律文件**。
2.  **流程**：先改 yaml 定义接口 -> 再写 Server 实现 -> 再写 Web 调用。
3.  **校验**：`./scripts/contract-check` 必须通过。

---
## 11. 规范文档内容要求（文件必须存在且内容必须覆盖）

### 11.1 `docs/spec/WORKFLOW.md`（必须包含）

* TODO-ID 规则
* 分支/commit/PR 规则
* Review 不通过处理（amend/追加规则）
* Gate 清单（本地 + CI）
* agent 闭环流程图（文字步骤即可）

### 11.2 `docs/spec/DEFINITION_OF_DONE.md`

必须列出 DoD 勾选项（至少 25 条），覆盖：

* 功能完成/AC 完成
* 前后端错误处理
* migration/回滚说明
* 文档更新
* 门禁通过
* 安全/脱敏/日志

### 11.3 `docs/spec/WEB_GUIDE.md`

必须写清楚：

* 目录结构与职责
* axios/http 规范（含错误处理、401 策略、统一弹窗）
* 页面必须具备的状态（loading/empty/error）
* Pinia 使用规范
* Tailwind + NaiveUI 的边界
* env 配置与 baseURL 约定

### 11.4 `docs/spec/SERVER_GUIDE.md`

必须写清楚：

* 分层结构与职责边界
* 统一响应体与异常处理
* 错误码体系与映射
* DTO/VO 与校验
* Redis key 与 TTL 规范
* Flyway 迁移规范与回滚策略
* 日志与 traceId 规范
* swagger/openapi 规范

### 11.5 `docs/spec/API_CONTRACT.md`

* OpenAPI 文件位置与更新流程
* 分页标准、排序标准、过滤标准
* 字段命名：snake_case vs camelCase（必须写死一种，建议：API 返回 camelCase，DB 用 snake_case，映射清楚）
* 统一响应体在契约中的表达方式

### 11.6 `docs/spec/REVIEW_CHECKLIST.md`

* Review Agent 必须逐条检查的清单（FE/BE/契约/迁移/门禁/安全）
* BLOCKERS 判定标准（什么情况必须 FAIL）

---

## 16. 运行配置文件（必须，唯一可调参数源）

### 16.1 配置文件路径（强制）

* 路径固定：`docs/ops/ai-team-config.json`
* 规则：

    1. **任何会影响流程行为的参数**（是否 PR、最大循环、门禁命令、合并策略、基础分支、并发策略、日志策略……）都必须在此文件中声明。
    2. 除该文件外，任何 agent/skill/脚本不得硬编码流程参数。
    3. config 未通过 Schema 校验：系统必须终止并输出阻断报告（按 12.2 格式）。


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

