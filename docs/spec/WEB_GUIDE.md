# WEB_GUIDE（前端开发规范）

## 1. 技术栈固定（不可漂移）

- Vue3 + Vite + TailwindCSS + Naive UI + Pinia + Axios 封装 + qs + dayjs + **纯 JS**

## 2. 目录结构（强制）

以 `apps/web` 为根：

- `src/main.js`：应用入口
- `src/App.vue`：根组件
- `src/pages/`：页面（路由页面）
- `src/components/`：可复用组件
- `src/stores/`：Pinia stores
- `src/api/`：API 封装
  - `src/api/http.js`：唯一 Axios 封装入口（强制）
  - `src/api/generated/`：由 openapi 生成的客户端（如启用）
- `src/utils/`：工具函数

## 3. API 调用（强制）

### 3.1 唯一入口

- 任何请求不得直接 import `axios`
- 必须通过：`apps/web/src/api/http.js`

### 3.2 统一错误处理

- 业务错误码来源：`packages/api-contract/error-codes.json`
- UI 提示必须可判定：同一错误码返回同一提示文案（不可“看情况”）

## 4. 约束性 lint 规则（确定性，可判定）

以下规则必须可通过脚本判定（详见 REVIEW_CHECKLIST）：

- 禁止：`apps/web` 中除 `src/api/http.js` 外出现 `from 'axios'` / `require('axios')`
- 禁止：未使用的 import/变量（可通过脚本扫描或最小规则集判定）
- 禁止：尾随空格、无换行结尾（统一由 lint gate 检查）

