# DEFINITION OF DONE（DoD）

本文件定义：
- **Todo 级 DoD**：单个 Todo 完成所需的最小可验收证据
- **系统级 DoD**：仓库作为“全自动 AI 开发团队系统”整体交付所需证据

## 1. Todo 级 DoD（每个 Todo 必须满足）

### 1.1 需求与范围
- `docs/ops/ai-team-state.json` 中对应 Todo：
  - `scope.in` 与 `scope.out` 非空
  - `acceptanceCriteria` ≥ 3 且为可验证句子
  - `affectedAreas` 至少一个非空（以路径/模块标注）

### 1.2 Git 与状态一致性
- 分支名符合：`(feat|fix|chore)/TODO-<id>-<kebab-desc>`
- 至少 1 次 commit，commit message 符合 V2 9.2（Conventional Commits + scope + TODO-ID）
- commit hash 写入 `docs/ops/ai-team-state.json` 对应 `todo.commits`

### 1.3 Review 与门禁
- Review 证据落盘：`docs/ops/logs/<TODO-ID>/<run>/review/review.md`
- Gate 证据落盘：`docs/ops/logs/<TODO-ID>/<run>/gates/<gate>.log`
- `./scripts/check`（或对该 Todo 的等价 gates）均为 PASS

### 1.4 契约/迁移一致性（按影响面触发）
- 若 affectedAreas.contract 非空：
  - `packages/api-contract/openapi.yaml` 变更同步
  - `./scripts/contract-check` PASS
- 若 affectedAreas.dbMigration 非空：
  - 迁移文件满足命名与规则（V2 23）
  - `./scripts/migration-check` PASS

## 2. 系统级 DoD（仓库交付必须满足）

### 2.1 必备文件存在（V2 20.1 / 11）
- 根：`.nvmrc`、`pnpm-workspace.yaml`、`package.json`
- 宪法：`docs/spec/*`（7 个文件）
- ops：`docs/ops/ai-team-config.json`、`docs/ops/ai-team-state.json`、`docs/ops/schema/*`
- 工程：`apps/web/*`、`apps/server/*`、`packages/api-contract/*`
- 脚本：`scripts/*`（V2 21.2 清单）

### 2.2 自动闭环（V2 15.1 / 14.7）
- 可运行主循环驱动：`./scripts/ai-team run --demo`
- demo 至少包含 web+server+contract+迁移（至少各 1 项）
- 至少触发 1 次故意失败并自动修复成功（可为 lint/gate fail）

### 2.3 可重复验证（V2 15.2）
- 在干净环境执行：`./scripts/check` 必须 PASS

### 2.4 最终交付报告（V2 12.3）
- 生成 `docs/ops/delivery-report.md`，包含：
  - 完成的 Todo 列表（TODO-ID、标题、commit hash）
  - 关键变更点（web/server/contract/migration）
  - 门禁执行记录摘要（每类 PASS）
  - 回滚说明（涉及迁移必须列出）
  - 已知风险与后续建议（必须具体）

