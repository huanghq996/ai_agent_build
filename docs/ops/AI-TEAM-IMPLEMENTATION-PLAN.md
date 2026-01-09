# AI 开发团队系统 - 实现计划

## 1. 项目概述

基于 Claude Code 构建全自动 AI 开发团队系统，利用：
- **ralph-wiggum 插件**：驱动主循环
- **状态文件驱动**：`ai-team-state.json` 作为单一事实来源
- **规则驱动调度**：CLAUDE.md 定义 agent 选择规则
- **混合实现**：sub-agent 用 Task tool + prompt，skill 用 shell/Python

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ralph-wiggum 循环                         │
│  /ralph-loop "执行 AI 团队主循环" --max-iterations 100       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLAUDE.md (宪法)                         │
│  定义：角色规则、状态转移规则、调度规则、输出协议              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    主循环控制器逻辑                          │
│  1. 读取 state.json 获取当前状态                             │
│  2. 根据规则决定下一步动作                                   │
│  3. 调用对应 sub-agent 或 skill                              │
│  4. 更新 state.json                                          │
│  5. 输出状态摘要，等待下一次迭代                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │Sub-Agents│   │  Skills  │   │  Tools   │
        │(决策层)  │   │(执行层)  │   │(原子操作)│
        └──────────┘   └──────────┘   └──────────┘
```

## 3. 核心组件清单

### 3.1 Sub-Agents（通过 Task tool + prompt 实现）

| Agent | 职责 | 触发条件 |
|-------|------|----------|
| PM Agent | 范围冻结、任务分配、修复指令改写、终止决策 | 新需求输入、REVIEW_FAIL/GATE_FAIL 需要改写指令 |
| Spec Agent | 需求拆解为 Todo、写 AC、写接口清单 | PM 派工拆解需求 |
| Architect Agent | API 契约、数据模型、迁移策略 | 涉及契约/数据库变更的 Todo |
| Dev-Web Agent | 前端实现 | Todo.affectedAreas.web 非空 |
| Dev-Server Agent | 后端实现 | Todo.affectedAreas.server 非空 |
| Review Agent | 静态审查、规范检查 | Todo 状态为 COMMITTED |
| QA Agent | 测试用例清单、边界场景 | Todo 完成后补充测试 |

### 3.2 Skills（通过 shell/Python 脚本实现）

| Skill | 功能 | 实现方式 |
|-------|------|----------|
| RunGates | 执行 lint/test/build/migration-check | `./scripts/check` 封装 |
| GitOps | 创建分支、提交、amend | `tools/git_ops.py` |
| ContractSync | 更新/校验 openapi | `tools/contract_sync.py` |
| StateManager | 状态文件 CRUD | `tools/state_manager.py`（已有） |
| Report | 生成交付报告 | `tools/report_generator.py` |

### 3.3 关键文件

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 宪法：定义所有 agent 行为规则 |
| `docs/ops/ai-team-state.json` | 状态文件（已有） |
| `docs/ops/ai-team-config.json` | 配置文件（已有） |
| `tools/state_manager.py` | 状态管理工具（需扩展） |
| `tools/git_ops.py` | Git 操作工具（新建） |
| `tools/report_generator.py` | 报告生成工具（新建） |

## 4. 状态驱动调度规则

### 4.1 主循环决策树

```
读取 state.json
    │
    ├─ 存在 BLOCKED/ABORTED 的 Todo？
    │   └─ 是 → 输出阻断报告，终止循环
    │
    ├─ 存在 DOING 状态的 Todo？
    │   └─ 是 → 检查是否超时/异常 → 继续或标记 BLOCKED
    │
    ├─ 存在 COMMITTED 状态的 Todo？
    │   └─ 是 → 触发 Review Agent → 更新为 REVIEWING
    │
    ├─ 存在 REVIEWING 状态的 Todo？
    │   └─ 是 → 执行 RunGates → 判定 DONE/REVIEW_FAIL/GATE_FAIL
    │
    ├─ 存在 REVIEW_FAIL/GATE_FAIL 状态的 Todo？
    │   └─ 是 → 检查 fixCyclesUsed
    │       ├─ < maxAutoFixCyclesPerTodo → PM 改写指令 → DOING
    │       └─ >= maxAutoFixCyclesPerTodo → BLOCKED
    │
    ├─ 存在 PLANNED 状态的 Todo？
    │   └─ 是 → PM 派工 → Dev Agent 执行 → DOING
    │
    └─ 所有 Todo 都是 DONE？
        └─ 是 → 生成交付报告 → 输出 "ALL_DONE" → 终止循环
```

### 4.2 状态转移规则（严格）

| 当前状态 | 允许转移到 | 触发条件 |
|----------|-----------|----------|
| PLANNED | DOING | PM 派工，scope/AC 完整 |
| DOING | COMMITTED | Dev 完成，commit hash 写入 |
| COMMITTED | REVIEWING | 触发 Review Agent |
| REVIEWING | DONE | Review PASS + Gates PASS |
| REVIEWING | REVIEW_FAIL | Review FAIL |
| REVIEWING | GATE_FAIL | Review PASS + Gates FAIL |
| REVIEW_FAIL | DOING | PM 改写指令，fixCyclesUsed++ |
| GATE_FAIL | DOING | PM 改写指令，fixCyclesUsed++ |
| * | BLOCKED | fixCyclesUsed >= max 或环境阻断 |
| * | ABORTED | 人工终止 |

## 5. CLAUDE.md 设计（宪法）

CLAUDE.md 是整个系统的"宪法"，定义 Claude 在每次迭代中的行为规则。

### 5.1 结构大纲

```markdown
# CLAUDE.md

## 1. 系统身份
- 你是 AI 开发团队的主控制器
- 每次迭代读取 state.json，执行一个动作，更新状态

## 2. 核心规则
- 禁止直接编辑 state.json，必须使用 state_manager.py
- 禁止跳过状态转移
- 禁止在 scope.out 范围内做事

## 3. 角色定义（7 个 sub-agent 的 prompt 模板）
- PM_AGENT_PROMPT
- SPEC_AGENT_PROMPT
- ARCHITECT_AGENT_PROMPT
- DEV_WEB_AGENT_PROMPT
- DEV_SERVER_AGENT_PROMPT
- REVIEW_AGENT_PROMPT
- QA_AGENT_PROMPT

## 4. 调度规则（决策树）
- 根据 state.json 当前状态决定调用哪个 agent

## 5. 输入输出协议
- PM → Dev 的派工格式
- Dev → Review 的提交格式
- Review 的 PASS/FAIL 输出格式

## 6. 终止条件
- ALL_DONE：所有 Todo 完成
- BLOCKED：达到修复上限
- ABORTED：人工终止
```

## 6. 实现步骤

### Phase 1: 基础设施完善

**Step 1.1: 扩展 state_manager.py**
- 添加 `get-current-action` 命令：返回当前应执行的动作
- 添加 `update-review` 命令：更新 review 结果
- 添加 `update-gates` 命令：更新门禁结果
- 添加 `increment-fix-cycle` 命令：增加修复计数

**Step 1.2: 创建 git_ops.py**
- `create-branch <todo-id>`：创建分支
- `commit <todo-id> <message>`：提交代码
- `amend <todo-id> <message>`：修改最后提交
- `get-branch-status`：获取分支状态

**Step 1.3: 创建 report_generator.py**
- `generate-delivery-report`：生成交付报告
- `generate-blocked-report <todo-id>`：生成阻断报告

### Phase 2: CLAUDE.md 编写

**Step 2.1: 系统身份与核心规则**
- 定义主控制器身份
- 定义禁止行为清单
- 定义状态文件操作规范

**Step 2.2: Sub-Agent Prompt 模板**
- 为每个 agent 编写详细的 prompt 模板
- 包含：角色、职责、输入格式、输出格式、约束

**Step 2.3: 调度规则**
- 编写决策树的文字描述
- 定义每种状态对应的动作

### Phase 3: 集成与测试

**Step 3.1: ralph-wiggum 集成**
- 安装插件：`/plugin install ralph-wiggum@anthropics`
- 配置启动命令模板
- 测试基本循环

**Step 3.2: 端到端测试**
- 创建测试 Todo（如 TODO-9002）
- 运行完整循环验证状态转移
- 验证修复循环机制

### Phase 4: 文档完善

**Step 4.1: 更新现有规范文档**
- 补充 WORKFLOW.md 中的 ralph-loop 集成说明
- 更新 REVIEW_CHECKLIST.md 添加 agent 相关规则

**Step 4.2: 创建使用指南**
- 如何启动 AI 团队
- 如何添加新需求
- 如何处理 BLOCKED 状态

## 7. 关键文件清单

### 7.1 需要新建的文件

| 文件路径 | 用途 |
|----------|------|
| `CLAUDE.md` | 宪法：定义所有 agent 行为规则 |
| `tools/git_ops.py` | Git 操作工具 |
| `tools/report_generator.py` | 报告生成工具 |
| `docs/ops/USAGE.md` | AI 团队使用指南 |

### 7.2 需要修改的文件

| 文件路径 | 修改内容 |
|----------|----------|
| `tools/state_manager.py` | 扩展命令 |
| `docs/spec/WORKFLOW.md` | 添加 ralph-loop 集成说明 |
| `docs/ops/ai-team-config.json` | 添加 ralph-loop 相关配置 |

## 8. Sub-Agent 详细设计

### 8.1 PM Agent

**职责**：范围冻结、任务分配、修复指令改写、终止决策

**触发条件**：
- 新需求输入时
- REVIEW_FAIL/GATE_FAIL 需要改写指令时

**输出格式**：
```
TODO-ID: TODO-xxx
TITLE: xxx
CONTEXT: xxx
SCOPE_IN: [...]
SCOPE_OUT: [...]
AC: [>=3条]
FILES_EXPECTED: [...]
CONTRACT_CHANGES: none|describe
MIGRATION: none|required with reason
VERIFY_COMMANDS: [>=1]
COMMIT_MESSAGE: xxx
```

### 8.2 Dev Agent (Web/Server)

**职责**：根据 PM 派工指令实现代码

**触发条件**：Todo 状态为 DOING

**输出格式**：
```
TODO-ID: TODO-xxx
CHANGES_SUMMARY: [要点列表]
COMMAND_RESULTS: [每条 verify command 的输出摘要 + PASS/FAIL]
GIT:
  BRANCH: xxx
  COMMIT_HASH: xxx
NEXT: request review
```

### 8.3 Review Agent

**职责**：静态审查、规范检查

**触发条件**：Todo 状态为 COMMITTED

**输出格式（PASS）**：
```
RESULT: PASS
CHECKS: [...]
```

**输出格式（FAIL）**：
```
RESULT: FAIL
BLOCKERS: [...]
SUGGESTIONS: [...]
REQUIRED_CHANGES:
- file: path
  change: exact requirement
VERIFY_COMMANDS: [...]
```

## 9. ralph-loop 集成

### 9.1 启动命令

```bash
/ralph-loop "执行 AI 团队主循环：
1. 读取 docs/ops/ai-team-state.json
2. 根据 CLAUDE.md 规则决定下一步动作
3. 执行动作并更新状态
4. 输出状态摘要
" --max-iterations 100
```

### 9.2 终止条件

- 输出 `ALL_DONE` 时终止（所有 Todo 完成）
- 输出 `BLOCKED_REPORT` 时终止（达到修复上限）
- 达到 max-iterations 时终止

## 10. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 无限循环 | max-iterations 限制 + fixCyclesUsed 上限 |
| 状态文件损坏 | Schema 校验 + 每次操作前备份 |
| Agent 输出不规范 | 严格的输出格式校验 |
| 范围蔓延 | scope.out 强制检查 |

## 11. 并行执行设计

### 11.1 并行策略

- 支持多个 Todo 并行开发
- 配置项：`workflow.execution.parallelTodos = true`
- 最大并行数：`workflow.execution.maxParallel`

### 11.2 并行调度规则

```
读取所有 PLANNED 状态的 Todo
    │
    ├─ 检查当前 DOING 状态的 Todo 数量
    │   └─ < maxParallel → 可以启动新 Todo
    │
    ├─ 检查依赖关系（如果有）
    │   └─ 无阻塞依赖 → 可以并行
    │
    └─ 为每个可启动的 Todo 分配 Dev Agent
```

### 11.3 并行冲突处理

- 同一文件被多个 Todo 修改：后提交的 Todo 需要 rebase
- Git 冲突：标记为 BLOCKED，等待人工处理

## 12. 人工介入点

- **仅 BLOCKED 状态**：达到修复上限或环境阻断时暂停
- 其他状态全自动流转

## 13. CLAUDE.md 完整模板

以下是 CLAUDE.md 的完整内容模板，可直接使用：

```markdown
# CLAUDE.md - AI 开发团队宪法

## 1. 系统身份

你是 **AI 开发团队主控制器**。你的职责是：
- 读取 `docs/ops/ai-team-state.json` 获取当前项目状态
- 根据本文件定义的规则决定下一步动作
- 调用对应的 Sub-Agent 或 Skill 执行任务
- 更新状态文件并输出状态摘要

## 2. 核心规则（不可违反）

### 2.1 状态文件操作
- **禁止**直接编辑 `ai-team-state.json`
- **必须**使用 `python3 tools/state_manager.py <command>` 进行状态操作

### 2.2 状态转移
- **禁止**跳过状态转移（如 PLANNED 直接到 DONE）
- **必须**按照状态机规则逐步转移

### 2.3 范围控制
- **禁止**在 `scope.out` 范围内做任何事
- 发现需要超出 scope 时，**必须**报告 SCOPE_CONFLICT 并停止

## 3. 主循环逻辑

每次迭代执行以下步骤：

1. 运行 `python3 tools/state_manager.py get-current-action`
2. 根据返回的动作类型，调用对应的 Agent 或 Skill
3. 执行完成后更新状态
4. 输出状态摘要

## 4. 调度规则

根据 `get-current-action` 返回值决定动作：

| 返回值 | 动作 |
|--------|------|
| `DISPATCH_TODO:<id>` | 调用 PM Agent 派工 |
| `DEV_TODO:<id>` | 调用 Dev Agent 实现 |
| `REVIEW_TODO:<id>` | 调用 Review Agent 审查 |
| `RUN_GATES:<id>` | 执行 `./scripts/check --todo <id>` |
| `FIX_TODO:<id>` | 调用 PM Agent 改写修复指令 |
| `ALL_DONE` | 生成交付报告，终止循环 |
| `BLOCKED:<id>` | 生成阻断报告，终止循环 |

## 5. Sub-Agent 调用方式

使用 Claude Code 的 Task tool 调用 Sub-Agent：

### 5.1 PM Agent
触发：`DISPATCH_TODO` 或 `FIX_TODO`

### 5.2 Dev Agent
触发：`DEV_TODO`
根据 `affectedAreas` 决定调用 Dev-Web 还是 Dev-Server

### 5.3 Review Agent
触发：`REVIEW_TODO`

## 6. 输出协议

### 6.1 每次迭代结束时输出
STATUS_SUMMARY:
  ITERATION: <n>
  ACTION: <执行的动作>
  TODO: <处理的 TODO-ID>
  RESULT: <SUCCESS|FAIL>
  NEXT: <下一步动作>

### 6.2 全部完成时输出
ALL_DONE
DELIVERY_REPORT: docs/ops/delivery-report-<timestamp>.md

### 6.3 阻断时输出
BLOCKED_REPORT
TODO: <TODO-ID>
REASON: <阻断原因>
FIX_CYCLES_USED: <n>
```

## 14. state_manager.py 扩展设计

### 14.1 新增命令

```bash
# 获取当前应执行的动作
python3 tools/state_manager.py get-current-action
# 返回: DISPATCH_TODO:TODO-123 | DEV_TODO:TODO-123 | ALL_DONE | BLOCKED:TODO-123

# 更新 review 结果
python3 tools/state_manager.py update-review TODO-123 PASS
python3 tools/state_manager.py update-review TODO-123 FAIL \
  --blocker "缺少错误处理" \
  --blocker "未遵循命名规范" \
  --suggestion "建议添加单元测试"

# 更新门禁结果
python3 tools/state_manager.py update-gates TODO-123 \
  --lint PASS --test PASS --build FAIL

# 增加修复计数
python3 tools/state_manager.py increment-fix-cycle TODO-123
```

## 15. git_ops.py 设计

```bash
# 创建分支
python3 tools/git_ops.py create-branch TODO-123 feat "add-user-api"
# 输出: BRANCH_CREATED: feat/TODO-123-add-user-api

# 提交代码
python3 tools/git_ops.py commit TODO-123 "feat(server): TODO-123 add user API"
# 输出: COMMIT_HASH: abc1234

# 修改最后提交
python3 tools/git_ops.py amend TODO-123 "feat(server): TODO-123 add user API (fix lint)"
# 输出: AMENDED_HASH: def5678

# 获取分支状态
python3 tools/git_ops.py branch-status TODO-123
# 输出: BRANCH: feat/TODO-123-add-user-api, COMMITS: 2, AHEAD: 2
```

## 16. 实现优先级

1. **P0 - 核心循环**
   - state_manager.py 扩展
   - CLAUDE.md 编写
   - ralph-wiggum 集成

2. **P1 - 工具链**
   - git_ops.py
   - report_generator.py

3. **P2 - 文档**
   - USAGE.md
   - WORKFLOW.md 更新

## 17. Sub-Agent Prompt 模板

### 17.1 PM Agent Prompt

```
你是 PM Agent，负责任务派工和修复指令改写。

当前 Todo: {todo_json}
动作类型: {DISPATCH_TODO | FIX_TODO}

如果是 DISPATCH_TODO:
- 检查 scope/AC 是否完整
- 生成派工指令（格式见下）
- 调用 state_manager.py update-status TODO-xxx DOING

如果是 FIX_TODO:
- 分析 review.blockers 和 gates 失败原因
- 改写修复指令，明确指出需要修改的文件和内容
- 调用 state_manager.py increment-fix-cycle TODO-xxx

输出格式:
TODO-ID: ...
TITLE: ...
CONTEXT: ...
SCOPE_IN: [...]
SCOPE_OUT: [...]
AC: [>=3条]
FILES_EXPECTED: [...]
CONTRACT_CHANGES: none|describe
MIGRATION: none|required
VERIFY_COMMANDS: [>=1]
COMMIT_MESSAGE: ...
```

### 17.2 Dev Agent Prompt

```
你是 Dev Agent，负责代码实现。

当前 Todo: {todo_json}
派工指令: {dispatch_instruction}
类型: {web | server}

执行步骤:
1. 创建分支: python3 tools/git_ops.py create-branch {todo_id} feat "{desc}"
2. 按照派工指令实现代码
3. 运行验证命令
4. 提交代码: python3 tools/git_ops.py commit {todo_id} "{message}"
5. 更新状态: python3 tools/state_manager.py update-status {todo_id} COMMITTED --commit {hash}

约束:
- 只能在 scope.in 范围内做事
- 发现需要超出 scope 时，报告 SCOPE_CONFLICT 并停止
- 必须遵循 WEB_GUIDE.md 或 SERVER_GUIDE.md

输出格式:
TODO-ID: ...
CHANGES_SUMMARY: [...]
COMMAND_RESULTS: [...]
GIT:
  BRANCH: ...
  COMMIT_HASH: ...
NEXT: request review
```

### 17.3 Review Agent Prompt

```
你是 Review Agent，负责代码审查。

当前 Todo: {todo_json}
变更文件: {changed_files}

审查清单（参考 REVIEW_CHECKLIST.md）:
1. 代码是否在 scope.in 范围内
2. 是否满足所有 AC
3. 是否遵循 WEB_GUIDE/SERVER_GUIDE
4. 是否有安全问题
5. 是否有明显 bug

执行步骤:
1. 读取变更文件
2. 逐条检查审查清单
3. 输出 PASS 或 FAIL

输出格式（PASS）:
RESULT: PASS
CHECKS: [...]

输出格式（FAIL）:
RESULT: FAIL
BLOCKERS: [...]
REQUIRED_CHANGES:
- file: ...
  change: ...
```

---

**计划完成。可以交给其他 AI 实现。**
