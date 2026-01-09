# 需求文档 v2：全自动 Claude Code 开发团队（Native 模式）

## 0. 核心理念

本系统利用 **Claude Code** 本身作为核心智能引擎，而不是编写外部 Python 脚本来模拟 Agent。

*   **Driver（驱动者）**: Claude Code (CLI) 本身。
*   **Constitution（宪法）**: `.clauderc.json` / `CLAUDE.md` (定义 Agent 行为与角色)。
*   **Muscles（执行力）**: Deterministic Scripts (`./scripts/*`) + MCP Tools。
*   **Memory（记忆）**: `docs/ops/ai-team-state.json` (作为唯一的项目状态源)。

## 1. 核心目标

用户输入需求后，Claude Code 根据预定义名为 "AutoDev" 的 Workflow 或指令，自动执行以下循环：
1.  **Analyst Mode**: 读取需求 -> 更新 `ai-team-state.json` (拆解 Todo)。
2.  **Dev Mode**: 领取 Todo -> 切换分支 -> 编写代码 -> 提交。
3.  **Review Mode**: 运行静态检查 (`./scripts/lint`等) -> 自我审查 -> 修正。
4.  **Delivery**: 所有 Todo 完成 -> 生成交付报告。

---

## 2. 关键实体（保留原设计，但由 Claude 维护）

### 2.1 唯一事实来源：`ai-team-state.json`
*   必须使用工具 (`./scripts/state-manager` 或直接文件编辑) 更新状态。
*   Schema 保持不变（Epics -> Features -> Todos）。

### 2.2 门禁系统 (The Guardrails)
*   所有客观检查必须脚本化，Claude **不得** 靠“肉眼”检查。
*   脚本清单：
    *   `./scripts/check` (全量检查)
    *   `./scripts/lint`
    *   `./scripts/test`
    *   `./scripts/build`
    *   `./scripts/contract-check` (OpenAPI 契约校验)

---

## 3. Claude Code 配置与角色定义

### 3.1 角色 (Personas)
不实现独立的 Python 类，而是定义 **Prompt 模板** 或 **CLAUDE.md Rules**。

1.  **PM (Product Manager)**:
    *   职责：读取 `Requirements.md`，更新 `state.json`，标记 Todo 为 `PLANNED`。
    *   关键指令：“Analyze requirements and update plan”
2.  **Dev (Developer)**:
    *   职责：读取 `state.json` 中第一个 `PLANNED` 的 Todo，创建分支，实现代码，运行测试。
    *   关键指令：“Pick up next todo”
3.  **QA (Quality Assurance)**:
    *   职责：运行 `./scripts/check`，分析失败原因，指导 Dev 修复。
    *   关键指令：“Verify current work”

---

## 4. 执行流程 (The Loop)

不再有 `cli.py` 主循环。流程由 Claude 的 **Workflow** 或用户的 **Prompt 驱动** 推进。

**示例对话流：**
> User: "Start working on the Health Check feature."

**Claude 的内部动作序列 (由 CLAUDE.md 指引)**:
1.  读取 `ai-team-state.json`，找到 `TODO-9001`。
2.  执行 `git checkout -b feat/TODO-9001-health-check`。
3.  调用 `view_file` 查看相关代码。
4.  修改代码 (Web + Server + Contract)。
5.  运行 `./scripts/check`。
    *   若失败：分析日志 -> 修复 -> 重试。
    *   若成功：执行 `git commit`。
6.  更新 `ai-team-state.json` 状态为 `DONE`。
7.  生成报告片段。

---

## 5. 必须实现的“硬能力” (Skills/Tools)

为了让 Claude 能够稳定工作，必须提供确定的脚本工具（Skills）：

1.  **State Manager** (`tools/state_manager.py`):
    *   提供便捷的 CLI 来读取/更新 `ai-team-state.json`，防止 Claude 手写 JSON 出错。
    *   用法：`python3 tools/state_manager.py update-status TODO-123 DONE --commit-hash abc1234`

2.  **Gatekeeper** (`scripts/check`):
    *   现有的 shell 脚本体系非常好，**必须保留并增强**。
    *   输出必须包含最后的总结行：`CHECK RESULT: PASS` 或 `CHECK RESULT: FAIL`。

3.  **Scaffolding** (`tools/scaffold.py`):
    *   (可选) 快速生成标准文件结构的脚本，减少 hallucinations。

---

## 6. 现在的任务

抛弃旧的 `cli.py` (那个假的 Python Agent)。
转而构建：
1.  **`CLAUDE.md`**: 包含项目宪法、Command 别名、角色定义。
2.  **`tools/state_manager.py`**: 让 Claude 安全操作状态文件。
3.  **`scripts/*`**: 完善 deterministic 校验脚本。
4.  **Demo**: 人工（作为 User）向 Claude 下达指令，验证 Claude 能否遵循 `CLAUDE.md` 的规则自动完成 Health Check 任务。
