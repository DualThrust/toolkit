# toolkit

个人技能（Skills）与编码规范（Instructions）的单一源头仓库。

不依赖任何外部插件，所有内容从此仓库按需复制到各项目使用。

---

## 目录结构

```
toolkit/
├── skills/                     # Skill — 复制到项目 .agents/skills/ 使用
│   ├── workflows/              # 工作流技能（源自 obra/superpowers）
│   └── qt/                     # Qt 开发技能（源自 TheQtCompanyRnD/agent-skills）
│       └── references/         # 审查清单、常见错误等参考文件
│
├── instructions/               # File Instructions — 复制到 VS Code prompts/ 目录
│   ├── cpp.instructions.md     # C++ / Qt 编码规范
│   └── qml.instructions.md     # QML 编码规范
│
└── config/                     # 编辑器/工具配置参考
    └── clang-format/
        └── .clang-format       # Qt Creator 风格
```

## 使用方式

### 安装 Skill 到项目

```bash
# 将需要的技能复制到目标项目的 .agents/skills/ 目录
cp -r skills/workflows/brainstorming 目标项目/.agents/skills/
cp -r skills/qt/qt-cpp-review 目标项目/.agents/skills/
```

### 安装 Instructions（全局生效）

```bash
# 复制到 VS Code 用户级 prompts 目录
cp instructions/*.md "$env:APPDATA\Code\User\prompts\"
```

### 同步更新

```bash
cd ~/Projects/Personal/toolkit && git pull
cp -r skills/workflows/brainstorming/* 目标项目/.agents/skills/brainstorming/
cp instructions/*.md "$env:APPDATA\Code\User\prompts\"
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
