# toolkit

个人技能（Skills）与编码规范（Instructions）的单一源头仓库。

不依赖任何外部插件，所有内容从此仓库按需复制到各项目使用。

---

## 目录结构

```
toolkit/
├── deploy.py                   # 自动部署脚本
├── deploy-state.json           # 已部署项目的记录（自动生成，不入库）
├── .gitignore
│
├── skills/                     # Skill — 复制到项目 .agents/skills/ 使用
│   ├── workflows/              # 工作流技能（源自 obra/superpowers）
│   └── qt/                     # Qt 开发技能（源自 TheQtCompanyRnD/agent-skills）
│       └── references/         # 审查清单、常见错误等参考文件
│
├── instructions/               # File Instructions — 复制到 .github/instructions/
│   ├── cpp.instructions.md     # C++ / Qt 编码规范
│   ├── qml.instructions.md     # QML 编码规范
│   └── python.instructions.md  # Python 编码规范
│
└── config/                     # 编辑器/工具配置参考
    └── clang-format/
        └── .clang-format       # Qt Creator 风格
```

## 使用方式

### 一键部署（推荐）

使用 `deploy.py` 脚本自动将 toolkit 内容部署到目标项目：

```bash
# 交互模式 — 选择已部署过的项目，或输入新路径
python deploy.py

# 按已记录的名称部署（首次部署后自动记录）
python deploy.py --target keeprix_dev

# 按路径部署
python deploy.py --target /path/to/your/project

# 预览（不实际复制）
python deploy.py --target keeprix_dev --dry-run

# 更新模式：覆盖目标已有文件
python deploy.py --target keeprix_dev --update

# 强制刷新：先删旧目录再重新复制（解决文件残留）
python deploy.py --target keeprix_dev --force

# 列出所有已部署项目
python deploy.py --list-deployed
```

脚本自动处理以下映射：

| 源 (toolkit) | 目标项目 |
|---|---|
| `skills/workflows/*` | `.agents/skills/*` |
| `skills/qt/*` (除 references) | `.agents/skills/*` |
| `skills/qt/references/*` | `.agents/references/*` |
| `instructions/*.md` | `.github/instructions/*` |

> **部署模式说明：**
> - **安装（默认）**：新增文件，跳过已有文件
> - **更新（`--update`）**：新增文件，覆盖已有文件（残留文件不清除）
> - **强制刷新（`--force`）**：先删除 `.agents/` 和 `.github/instructions/`，再全量复制（无残留）
>
> 交互模式下选择项目后会提示选择部署模式，也可通过命令行参数直接指定。

### 部署状态管理

每次部署后路径自动记录在 `deploy-state.json` 中，下次交互模式自动列出。  
路径已不存在的项目会自动清理，无需手动维护。

### 手动部署（备用）

```bash
# Skills — 复制到目标项目的 .agents/skills/
cp -r skills/workflows/* 目标项目/.agents/skills/
cp -r skills/qt/* 目标项目/.agents/skills/   # 按需选择 Qt 技能

# Instructions — 复制到项目的 .github/instructions/
cp instructions/*.md 目标项目/.github/instructions/
```

### 同步上游更新后重新部署

```bash
cd ~/Projects/Personal/toolkit && git pull
python deploy.py --target keeprix_dev --update   # 增量更新
python deploy.py --target keeprix_dev --force    # 完整刷新
```

## 上游来源

| 仓库 | 说明 | 许可 |
|------|------|------|
| [obra/superpowers](https://github.com/obra/superpowers) | 工作流技能框架 | MIT |
| [TheQtCompanyRnD/agent-skills](https://github.com/TheQtCompanyRnD/agent-skills) | Qt 官方 AI 开发技能 | BSD-3-Clause |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | Copilot 社区技能合集 | MIT |

## 同步上游更新

### Superpowers（工作流技能）

```bash
git clone --depth 1 https://github.com/obra/superpowers /tmp/superpowers

# 对比差异
diff -r skills/workflows /tmp/superpowers/skills

# 按需复制更新
cp -r /tmp/superpowers/skills/brainstorming skills/workflows/
# ... 其他有变动的技能
```

### Qt 官方技能

```bash
git clone --depth 1 https://github.com/TheQtCompanyRnD/agent-skills /tmp/qt-skills

# 对比差异
diff -r skills/qt /tmp/qt-skills/skills

# 按需复制更新
cp -r /tmp/qt-skills/skills/qt-cpp-review skills/qt/
# ... 其他有变动的技能
```
