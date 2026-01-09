# 需求文档：全自动 Claude Code AI 开发团队系统（生产级）

## 0. 核心理念（Native Mode）

本系统利用 **Claude Code** 本身作为核心智能引擎，取代传统的 Python 脚本模拟 Agent。

*   **Driver（驱动者）**: Claude Code (CLI) 本身，由用户 Prompt 驱动。
*   **Constitution（宪法）**: `CLAUDE.md` (定义 Agent 行为与角色)。
*   **Muscles（执行力）**: Deterministic Scripts (`./scripts/*`) + `tools/state_manager.py`。
*   **Memory（记忆）**: `docs/ops/ai-team-state.json` (作为唯一的项目状态源)。

## 1. 核心目标

用户输入需求后，Claude Code 根据预定义角色（PM/Dev/QA），自动执行以下循环：

1.  **Analyst Mode (PM)**: 读取需求 -> 拆解 Todo -> 更新 `ai-team-state.json`。
2.  **Dev Mode (Dev)**: 领取 Todo -> 切换分支 -> 编写代码 -> 提交。
3.  **Review Mode (QA)**: 运行静态检查 (`./scripts/check`) -> 自我审查 -> 修正。
4.  **Delivery**: 所有 Todo 完成 -> 生成交付报告。

> **模板/规范是支撑**：用于让 agent 不漂移、让 review 有客观标准、让门禁可执行。

---

## 2. 系统边界与运行前提（明确约束）

### 2.1 运行环境与权限

系统运行于 Claude Code 环境，并具备以下能力：

*   可读写本地工作区文件
*   可执行命令（pnpm/mvn/docker/python3 等）
*   可执行 Git 操作（branch/commit/merge 等）

### 2.2 技术栈固定（不可漂移）

*   **Web**：Vue3 + Vite + TailwindCSS + Naive UI + Pinia + Axios 封装 + qs + dayjs + **纯 JS**
*   **Server**：Spring Boot + Java21 + MySQL + Redis + MyBatis-Flex + OpenAPI/Swagger + Flyway
*   **Monorepo**：`apps/web`、`apps/server`、`packages/api-contract`

---

## 3. 关键实体（不可变数据结构）

### 3.1 唯一事实来源：`ai-team-state.json`

*   路径固定：`docs/ops/ai-team-state.json`
*   **操作规则**：禁止 Claude 直接编辑 JSON 文本，**必须**使用 `tools/state_manager.py` 工具进行读写，以确保 Schema 一致性。

### 3.2 Todo 必须包含

*   **TODO-ID**：`TODO-<数字>`（唯一）
*   **Status**：`PLANNED` | `DOING` | `DONE` | `GATE_FAIL`
*   **Scope**：`in` (必须做) / `out` (不做)
*   **Verify**：验收标准与验证命令

---

## 4. Claude 角色定义（CLAUDE.md）

不实现独立的 Python 类，而是遵循 `CLAUDE.md` 定义的角色：

### 4.1 PM (Product Manager)
*   **触发**：用户输入需求或 "Analyze"。
*   **职责**：
    1.  读取需求。
    2.  调用 `state_manager.py add-todo` 拆解任务。
    3.  输出计划摘要。

### 4.2 Dev (Developer)
*   **触发**：用户输入 "Start work" 或 "Implement"。
*   **职责**：
    1.  调用 `state_manager.py read-next` 获取任务。
    2.  `git checkout -b feat/<TODO-ID>-<desc>`。
    3.  编写代码（Web + Server + Contract）。
    4.  调用 `./scripts/check` 自测。
    5.  `git commit`。
    6.  调用 `state_manager.py update-status ... COMMITTED`。

### 4.3 QA (Quality Assurance)
*   **触发**：用户输入 "Verify" 或 "Review"。
*   **职责**：
    1.  运行全量门禁 `./scripts/check`。
    2.  若 PASS：标记 `DONE`，生成报告。
    3.  若 FAIL：分析日志，指导 Dev 修复（标记 `GATE_FAIL`）。

---

## 5. 门禁与验证（自动化且确定性）

### 5.1 门禁脚本（单一入口）

仓库根目录必须提供，且 Claude 必须信任其 Exit Code：

*   `./scripts/check`：**全量门禁**（必须全部通过才能 DONE）
*   `./scripts/lint`：代码风格
*   `./scripts/test`：单元测试
*   `./scripts/build`：构建检查
*   `./scripts/contract-check`：OpenAPI 契约校验
*   `./scripts/migration-check`：DB 迁移脚本规范校验
*   `./scripts/state-validate`：状态文件 Schema 校验
*   `./scripts/config-validate`：配置文件 Schema 校验

### 5.2 门禁判定标准

*   **Lint**：任一 package lint 失败 → FAIL
*   **Test**：任一必须测试失败 → FAIL
*   **Build**：任一 build 失败 → FAIL
*   **Contract**：OpenAPI定义无效或与实现不一致 → FAIL
*   **Migration**：文件名不符 V<timestamp> 规范 → FAIL

---

## 6. Git 规范

1.  **Branch**：`feat/TODO-<id>-<desc>` 或 `fix/TODO-<id>-<desc>`
2.  **Commit**：`type(scope): TODO-<id> <message>`
    *   Example: `feat(web): TODO-123 add login page`
3.  **Merge**：推荐使用 Squash Merge 保持主干清晰。

---

## 7. 契约治理（Contract First）

1.  **Swagger/OpenAPI** (`packages/api-contract/openapi.yaml`) 是接口的**法律文件**。
2.  **流程**：先改 yaml 定义接口 -> 再写 Server 实现 -> 再写 Web 调用。
3.  **校验**：`./scripts/contract-check` 必须通过。

---

## 8. 目录结构规范

*   `apps/web/`：前端代码
*   `apps/server/`：后端代码
*   `packages/api-contract/`：共享契约
*   `docs/ops/`：
    *   `ai-team-state.json`：项目状态
    *   `ai-team-config.json`：项目配置
    *   `logs/`：门禁运行日志（必须落盘保留证据）
*   `tools/`：
    *   `state_manager.py`：状态管理工具
*   `scripts/`：门禁脚本

---

## 9. 终止与交付

*   **终止**：当 `./scripts/check` 连续失败且无法修复，或环境缺失关键依赖时，Claude 应停止并请求用户帮助。
*   **交付**：所有 Todo 状态为 `DONE` 时，生成 `delivery-report.md`，列出所有变更的 Commit Hash 和验证结果。
