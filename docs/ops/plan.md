# 实施计划（严格按 V2 第 14 章顺序）

> 目标：在当前仓库内实现《需求文档：全自动 Claude Code AI 开发团队系统（生产级）》。
>
> 约束：
> - 必须按“第 14 章”顺序执行：14.1 → 14.2 → 14.3 → 14.4 → 14.5 → 14.6 → 14.7
> - 所有门禁只能通过统一脚本入口执行：`./scripts/check` / `./scripts/lint` / `./scripts/test` / `./scripts/build` / `./scripts/migration-check`（并补齐 V2 第 21 章要求的其它脚本）
> - 每个最小 Todo 至少 1 次 git commit，commit message 必须符合 V2 9.2，且完成后更新 `docs/ops/ai-team-state.json` 对应 Todo 状态与 commit hash

---

## 14.1 初始化仓库结构与状态文件（docs/ops/*）

### 文件清单（新增/修改）
- 新增：`docs/ops/plan.md`
- 新增：`docs/ops/ai-team-config.json`
- 新增：`docs/ops/ai-team-state.json`
- 新增：`docs/ops/schema/ai-team-config.schema.json`
- 新增：`docs/ops/schema/ai-team-state.schema.json`
- 新增：`docs/ops/change-log.md`

### 验收命令
- `python3 -m jsonschema -i docs/ops/ai-team-config.json docs/ops/schema/ai-team-config.schema.json`
- `python3 -m jsonschema -i docs/ops/ai-team-state.json docs/ops/schema/ai-team-state.schema.json`

---

## 14.2 生成“宪法”文档（docs/spec/*）

### 文件清单（新增/修改）
- 新增：`docs/spec/WORKFLOW.md`
- 新增：`docs/spec/DEFINITION_OF_DONE.md`
- 新增：`docs/spec/WEB_GUIDE.md`
- 新增：`docs/spec/SERVER_GUIDE.md`
- 新增：`docs/spec/API_CONTRACT.md`
- 新增：`docs/spec/ERROR_CODES.md`
- 新增：`docs/spec/REVIEW_CHECKLIST.md`（必须可判定 PASS/FAIL）

### 验收命令
- `test -f docs/spec/WORKFLOW.md`
- `test -f docs/spec/REVIEW_CHECKLIST.md`
- `rg -n \"^RULE-\" docs/spec/REVIEW_CHECKLIST.md`

---

## 14.3 生成模板工程（apps/web、apps/server、packages/api-contract）

### 文件清单（新增/修改）
- 新增：`.nvmrc`
- 新增：`pnpm-workspace.yaml`
- 新增：`package.json`
- 新增：`.gitignore`
- 新增：`apps/web/package.json`
- 新增：`apps/web/index.html`
- 新增：`apps/web/src/main.js`
- 新增：`apps/web/src/App.vue`
- 新增：`apps/web/src/api/http.js`
- 新增：`apps/server/pom.xml`
- 新增：`apps/server/src/main/java/com/example/agb/AgbApplication.java`
- 新增：`apps/server/src/main/resources/application.yml`
- 新增：`apps/server/src/main/resources/db/migration/.gitkeep`
- 新增：`packages/api-contract/openapi.yaml`
- 新增：`packages/api-contract/error-codes.json`
- 新增：`packages/api-contract/.spectral.yaml`

### 验收命令
- `test -f .nvmrc && test -f pnpm-workspace.yaml && test -f package.json`
- `test -f apps/web/package.json && test -f apps/server/pom.xml`
- `python3 -c \"import yaml; yaml.safe_load(open('packages/api-contract/openapi.yaml','r',encoding='utf-8'))\"`
- `python3 -c \"import json; json.load(open('packages/api-contract/error-codes.json','r',encoding='utf-8'))\"`

---

## 14.4 生成门禁脚本（scripts/*）并确保可运行

### 文件清单（新增/修改）
- 新增：`scripts/check`
- 新增：`scripts/lint`
- 新增：`scripts/test`
- 新增：`scripts/build`
- 新增：`scripts/migration-check`
- 新增：`scripts/contract-check`
- 新增：`scripts/state-validate`
- 新增：`scripts/config-validate`
- 新增：`tools/ai-team/gates/*.py`（作为 package.json 脚本的确定性实现）

### 验收命令
- `./scripts/check`

---

## 14.5 实现 skills：RunGates、GitOps、ContractSync、Report

### 文件清单（新增/修改）
- 新增：`tools/ai-team/skills/run_gates.py`
- 新增：`tools/ai-team/skills/git_ops.py`
- 新增：`tools/ai-team/skills/contract_sync.py`
- 新增：`tools/ai-team/skills/report.py`

### 验收命令
- `python3 tools/ai-team/skills/run_gates.py --help`

---

## 14.6 实现主循环驱动（V2 第 6 章状态机）

### 文件清单（新增/修改）
- 新增：`scripts/ai-team`（CLI 入口）
- 新增：`tools/ai-team/cli.mjs`
- 新增：`tools/ai-team/state-store.mjs`
- 新增：`tools/ai-team/review/deterministic-review.mjs`

### 验收命令
- `./scripts/ai-team --help`
- `./scripts/ai-team init`
- `./scripts/ai-team plan --demo`

---

## 14.7 自检：跑一条示例闭环并产出交付报告

### 文件清单（新增/修改）
- 新增：`docs/ops/delivery-report.md`
- 修改：`docs/ops/ai-team-state.json`（demo todo 状态、gates、review、commit hash）
- 生成：`docs/ops/logs/**`（运行时证据，不建议入库）

### 验收命令
- `./scripts/ai-team run --demo`
- `./scripts/check`
- `test -f docs/ops/delivery-report.md`

---

## 关键风险点与规避方案（必须具体）

1. **网络受限导致无法下载依赖（pnpm/maven 下载、spectral、openapi generator 等）**
   - 规避：所有门禁与 demo 采用“确定性本地校验”实现（schema/yaml/json/规则扫描/命名约束），不依赖外网下载。
   - 留痕：在 `docs/ops/delivery-report.md` 记录网络限制与对应的 gate 证明（日志路径、命令摘要）。

2. **Docker socket 无权限，无法通过 docker CLI 验证 MySQL/Redis 容器**
   - 规避：本项目门禁不依赖容器可达性；MySQL/Redis 仅作为业务工程运行时依赖（示例闭环不做真实连接）。
   - 留痕：在 `docs/ops/logs/system/<run>/run.log` 记录 `docker ps` 失败摘要与原因（permission denied）。

3. **Review Checklist 主观化风险（导致 PASS/FAIL 不可判定）**
   - 规避：每条规则必须包含 `CHECK_METHOD` 与 `PASS_CONDITION`，并尽量映射到 `./scripts/*` 或可重复的 `rg/python` 命令；禁止“建议/尽量/最好”等措辞。

4. **状态机与 state.json 漂移（状态跳跃、缺字段、漏写 gates）**
   - 规避：强制 `./scripts/state-validate` 与 `./scripts/config-validate` 作为 `./scripts/check` 前置步骤；CLI 每次迁移都先写 state 再落盘日志再输出摘要。

5. **日志泄露敏感信息（例如 `.env` 中 password）**
   - 规避：所有 `./scripts/*` 落盘日志前统一执行正则脱敏（按 `ai-team-config.json` 的 redactions.patterns），脱敏失败直接 FAIL。
