# WORKFLOW（全自动 AI 开发团队工作流）

本文件定义团队的**状态机**、**修复循环**、**Git 规则**、**门禁执行**与**终止条件**。所有自动化与审查以此为准。

## 1. 单一事实来源（SSOT）

- 团队状态：`docs/ops/ai-team-state.json`
- 运行配置：`docs/ops/ai-team-config.json`
- Schema：`docs/ops/schema/ai-team-*.schema.json`
- 门禁统一入口：`./scripts/check`（其余 gate 由 `./scripts/*` 暴露）

## 2. Todo 状态机（V2 第 6 章，禁止跳跃）

允许的状态集合：
`PLANNED` → `DOING` → `COMMITTED` → `REVIEWING` → (`DONE` | `REVIEW_FAIL` | `GATE_FAIL`) → `DOING`（循环）

### 2.1 状态定义

- `PLANNED`：已创建 Todo，范围与验收明确，尚未派工实施。
- `DOING`：正在实现中（PM 已派工，Dev 执行）。
- `COMMITTED`：Dev 已完成并产生 commit（commit hash 必须写入 state）。
- `REVIEWING`：触发 Review（确定性审查优先，见 REVIEW_CHECKLIST）。
- `REVIEW_FAIL`：Review 失败，必须进入修复循环（回到 DOING）。
- `GATE_FAIL`：Review 通过但门禁失败（回到 DOING）。
- `DONE`：Review PASS 且 Gates PASS。
- `BLOCKED`：达到终止条件或环境阻断，输出阻断报告（V2 12.2）。
- `ABORTED`：人为终止（必须记录原因）。

### 2.2 进入/退出条件（可判定）

- `PLANNED` → `DOING`
  - 条件：scope.in/scope.out/acceptanceCriteria/affectedAreas 具备且满足“小 Todo 定义”（V2 第 3 章）
- `DOING` → `COMMITTED`
  - 条件：至少 1 个 commit 已创建，且 commit message 符合 V2 9.2；commit hash 写入 `todo.commits`
- `COMMITTED` → `REVIEWING`
  - 条件：确定性审查开始，必须输出并落盘 review 证据（V2 25.3）
- `REVIEWING` → `REVIEW_FAIL`
  - 条件：任一确定性审查规则 FAIL
- `REVIEWING` → `GATE_FAIL`
  - 条件：Review PASS 且任一 required gate FAIL（见 `ai-team-config.json.gates.required`）
- `REVIEWING` → `DONE`
  - 条件：Review PASS 且所有 required gate PASS
- `REVIEW_FAIL|GATE_FAIL` → `DOING`
  - 条件：PM 改写/强化修复指令；`fixCyclesUsed += 1`；达到上限则转 `BLOCKED`

## 3. 修复循环（Fix Cycle）

- 上限：`docs/ops/ai-team-config.json.workflow.maxAutoFixCyclesPerTodo`
- 计数规则：
  - 初次从 `PLANNED` 进入 `DOING`：`fixCyclesUsed` 不增加
  - 从 `REVIEW_FAIL|GATE_FAIL` 回到 `DOING`：`fixCyclesUsed += 1`
- 终止：
  - `fixCyclesUsed >= maxAutoFixCyclesPerTodo` 且仍 FAIL → `BLOCKED`，并按 V2 12.2 输出阻断报告

## 4. amend 规则（V2 6.2）

当 `REVIEW_FAIL` 或 `GATE_FAIL` 后进入修复：

- 若修改属于“修复/补齐/规范调整”：必须 `git commit --amend`
- 若修改属于“新增大块未覆盖内容”：允许追加 commit，但必须同 TODO-ID，且追加 hash 写入 state

判定口径（必须可判定）：
- 仅涉及 checklist 的 REQUIRED_CHANGES：视为修复 → amend
- 引入新接口/新模块/新目录结构：视为扩展 → 追加 commit

## 5. PR 策略（usePR true/false）

配置源：`docs/ops/ai-team-config.json.workflow.usePR`

- `usePR=false`（默认）
  - 只做本地分支与提交，不依赖远程
- `usePR=true`
  - 必须具备 remote 可用与凭证；否则视为环境阻断并转 `BLOCKED`
  - PR 标题必须包含 TODO-ID

## 6. 门禁执行与日志证据（V2 第 21/22 章）

- `./scripts/check` 必须顺序执行（默认）：
  `config-validate` → `state-validate` → `contract-check` → `migration-check` → `lint` → `test` → `build`
- 所有脚本：
  - exit code：0=PASS，非 0=FAIL
  - stdout：必须输出简短摘要
  - 完整输出：必须落盘到 `docs/ops/logs/...`，并按配置做脱敏

## 7. 终止条件（V2 12.1）

任一满足即终止自动循环：
- fixCyclesUsed 达到上限仍 FAIL → `BLOCKED`
- 环境缺失关键能力且无法继续 → `BLOCKED`
- 发现需求与技术栈矛盾且无法在 scope 内解决 → `BLOCKED`

## 8. ralph-loop 集成

### 8.1 启动命令
```bash
/ralph-loop "执行 AI 团队主循环" --max-iterations 100
```

### 8.2 循环逻辑
每次迭代：
1. 运行 `python3 tools/state_manager.py get-current-action`
2. 根据返回值执行对应动作
3. 更新状态文件
4. 输出状态摘要

### 8.3 终止条件
- `ALL_DONE`：所有 Todo 完成
- `BLOCKED`：达到修复上限
- 达到 max-iterations

