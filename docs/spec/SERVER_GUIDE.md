# SERVER_GUIDE（后端开发规范）

## 1. 技术栈固定（不可漂移）

- Spring Boot + Java21 + MySQL + Redis + MyBatis-Flex + Flyway + OpenAPI/Swagger

## 2. 目录结构与分层（强制）

以 `apps/server/src/main/java` 为根，强制三层：

- `.../controller`：仅处理 HTTP 输入输出与参数校验
- `.../service`：业务逻辑
- `.../mapper`：数据访问（MyBatis-Flex）

### 2.1 禁止跨层（可判定）

- controller 不得直接依赖 mapper
- service 不得依赖 controller

## 3. 统一响应与异常（强制）

- 统一响应：`ApiResponse<T>`
- 全局异常：
  - 必须输出 traceId（写入响应与日志）
  - 对外响应不得包含堆栈

## 4. Redis 规范（强制）

- key 必须带前缀：`<app>:<module>:...`
- 必须设置 TTL（除非明确定义为永久数据并在 scope.in 说明）

## 5. Flyway 迁移规范（强制）

- 目录：`apps/server/src/main/resources/db/migration`
- 命名：`VYYYYMMDDHHMMSS__kebab-name.sql`
- 规则：
  - timestamp 必须递增（默认不允许 out-of-order）
  - 禁止 repeatable（`R__`）
  - 禁止空 SQL 文件

