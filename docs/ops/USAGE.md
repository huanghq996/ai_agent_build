# AI 开发团队使用指南

## 1. 快速开始

### 1.1 前置条件
- 安装 Claude Code CLI
- 安装 ralph-wiggum 插件：`/plugin install ralph-wiggum@anthropics`

### 1.2 启动 AI 团队
```bash
/ralph-loop "执行 AI 团队主循环" --max-iterations 100
```

## 2. 添加新需求

### 2.1 使用 state_manager.py 添加 Todo
```bash
python3 tools/state_manager.py add-todo TODO-1001 "实现用户登录" \
  --scope-in "添加登录接口" \
  --scope-in "添加登录页面" \
  --scope-out "不做注册功能" \
  --scope-out "不做第三方登录" \
  --ac "登录成功返回 token" \
  --ac "登录失败返回错误信息" \
  --ac "前端显示登录表单"
```

## 3. 查看状态

### 3.1 查看当前动作
```bash
python3 tools/state_manager.py get-current-action
```

### 3.2 查看下一个待处理 Todo
```bash
python3 tools/state_manager.py read-next
```

## 4. 处理 BLOCKED 状态

当 Todo 达到修复上限时会进入 BLOCKED 状态。

### 4.1 查看阻断报告
```bash
cat docs/ops/reports/blocked-TODO-xxx-*.md
```

### 4.2 手动修复后重置状态
```bash
python3 tools/state_manager.py update-status TODO-xxx DOING
```

## 5. 配置说明

配置文件：`docs/ops/ai-team-config.json`

关键配置项：
- `workflow.maxAutoFixCyclesPerTodo`: 最大修复次数（默认 5）
- `workflow.execution.parallelTodos`: 是否并行执行
- `gates.required`: 必须通过的门禁列表
