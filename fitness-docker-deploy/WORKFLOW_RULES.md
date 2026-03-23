# Fitness Pose Validator - Git 工作流程规范

> ⚠️ **AI 操作前必读** - 每次进行 Git 操作前必须遵守此规范

---

## 一、分支保护规则

`main` 分支已启用保护，以下操作被 **禁止**：

| 操作 | 状态 |
|------|------|
| 直接 push 到 main | ❌ 禁止 |
| force push 到 main | ❌ 禁止 |
| 删除 main 分支 | ❌ 禁止 |
| 绕过 PR 审批 | ❌ 禁止（管理员也不例外） |

**必须通过 Pull Request 流程才能合并到 main。**

---

## 二、服务器端代码更新流程

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1: 创建功能分支                                             │
│  ─────────────────────                                           │
│  git checkout main && git pull                                   │
│  git checkout -b server/功能名称                                  │
├──────────────────────────────────────────────────────────────────┤
│  Step 2: 修改代码并提交                                           │
│  ─────────────────────                                           │
│  git add .                                                       │
│  git commit -m "type(server): 描述"                              │
├──────────────────────────────────────────────────────────────────┤
│  Step 3: 推送到远程并创建 PR                                       │
│  ─────────────────────                                           │
│  git push origin server/功能名称                                 │
│  gh pr create --title "type(server): 描述" --body "..."          │
├──────────────────────────────────────────────────────────────────┤
│  Step 4: 审核通过后合并                                           │
│  ─────────────────────                                           │
│  gh pr merge --squash --delete-branch                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 三、分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `server/` | 服务器端功能 | `server/add-llm-cache` |
| `client/` | 客户端功能 | `client/add-dark-mode` |
| `fix/` | Bug 修复 | `fix/api-timeout` |
| `docs/` | 文档更新 | `docs/update-readme` |
| `refactor/` | 代码重构 | `refactor/simplify-auth` |
| `test/` | 测试相关 | `test/add-api-tests` |

---

## 四、Commit 消息规范

```
<type>(<scope>): <subject>

type 类型：
  feat      新功能
  fix       Bug 修复
  docs      文档更新
  refactor  重构（不增加功能、不修复 Bug）
  test      测试相关
  chore     构建/工具变动
  perf      性能优化

scope 范围：
  server    服务器端
  client    客户端 GUI
  dashboard Web 前端
  api       API 相关
```

**示例：**
```bash
git commit -m "feat(server): 添加 LLM 分析缓存功能"
git commit -m "fix(client): 修复深蹲计数错误"
git commit -m "docs: 更新部署文档"
```

---

## 五、禁止操作清单

| 操作 | 后果 | 正确做法 |
|------|------|----------|
| `git push --force origin main` | ❌ 会被拒绝 | 创建 PR 合并 |
| `git push origin main`（直接） | ❌ 会被拒绝 | 创建 PR 合并 |
| `git reset --hard origin/main` | ⚠️ 丢失本地更改 | 先备份，再操作 |
| `git merge --no-ff` 到 main | ⚠️ 可能产生混乱历史 | 使用 PR + Squash |

---

## 六、项目结构

```
fitness-pose-validator/
├── gui/                    # PyQt6 桌面客户端
├── src/                    # 核心检测模块（姿态检测、计数等）
├── main.py                 # 客户端入口
├── run_gui.py              # GUI 启动脚本
├── fitness-docker-deploy/  # Docker 部署
│   ├── server/             # 服务器端（Python + LLM 分析）
│   │   ├── analysis/       # LLM 分析模块
│   │   ├── api/            # API 端点
│   │   └── run_server.py   # 服务器入口
│   ├── dashboard/          # Web 前端（HTML/JS/CSS）
│   └── docker-compose.yml  # Docker 编排
├── docs/                   # 文档
├── test/                   # 测试
└── models/                 # MediaPipe 模型文件
```

---

## 七、快速命令参考

### 新功能开发
```bash
git checkout main && git pull
git checkout -b server/feature-name
git add . && git commit -m "feat(server): 功能描述"
git push origin server/feature-name
gh pr create --title "feat(server): 功能描述" --body "## 变更内容\n- xxx"
gh pr merge --squash --delete-branch
```

### Bug 修复
```bash
git checkout main && git pull
git checkout -b fix/bug-name
git add . && git commit -m "fix(server): 修复描述"
git push origin fix/bug-name
gh pr create --title "fix(server): 修复描述" --body "## 问题\n- xxx\n\n## 修复\n- xxx"
gh pr merge --squash --delete-branch
```

### 查看当前状态
```bash
git status                    # 查看工作区状态
git branch -a                 # 查看所有分支
gh pr list                    # 查看当前 PR
gh pr view <number>           # 查看 PR 详情
```

---

## 八、紧急情况处理

### 如果需要撤销本地错误的 commit（尚未 push）
```bash
git reset --soft HEAD~1       # 撤销最近一次 commit，保留更改
git reset --hard HEAD~1       # 撤销最近一次 commit，丢弃更改（危险）
```

### 如果已经 push 到错误分支
```bash
# 不要 force push！创建修复 commit
git revert <commit-hash>      # 创建一个新 commit 来撤销指定 commit
git push origin branch-name
```

### 如果 main 分支有冲突需要解决
```bash
git checkout main
git pull origin main
git checkout feature-branch
git merge main                # 将 main 合并到 feature 分支解决冲突
# 解决冲突后
git add .
git commit -m "chore: 解决合并冲突"
git push origin feature-branch
```

---

## 九、检查清单

每次提交 PR 前确认：

- [ ] 分支命名符合规范（`server/`、`client/`、`fix/` 等）
- [ ] Commit 消息符合规范（`type(scope): 描述`）
- [ ] 代码已在本地测试
- [ ] PR 描述清晰说明了变更内容
- [ ] 没有包含敏感信息（API Key、密码等）

---

**最后更新**: 2024-03-23
**维护者**: kooibox