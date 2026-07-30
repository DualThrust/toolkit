---
applyTo: "**/*.py"
description: Python 编码规范 — PEP 8 snake_case，PySide6 适配说明
---

# Python 编码规范

> **风格定位：PEP 8 优先。** 命名遵循 snake_case（PEP 8），PySide6/Qt API 调用保持原始 camelCase。
> 蛇形 vs 驼峰的风格差异在本项目中是**有用信息**——看到 snake_case 即知来自 Python 侧。

格式化由 [Black](https://black.readthedocs.io/)（VS Code 扩展 `ms-python.black-formatter`）统一管理，以下为人工遵守的规则。

---

## 核心原则

- **格式交给 Black**：行宽 100，双引号，4 空格缩进，isort 排序 import
- **PEP 8 命名**：函数/变量 snake_case，类 PascalCase，常量 UPPER_SNAKE
- **类型注解全覆盖**：所有函数签名必须有参数类型和返回类型
- **`pathlib` 代替 `os.path`**：跨平台路径操作统一用 `Path`
- **`@dataclass` 代替裸 dict**：结构化数据类型安全
- **`match` 代替长 `if-elif` 链**：Python 3.10+
- **函数短小**：不超过 50 行，超过则拆分
- **脚本入口 `main()` + `if __name__ == "__main__"`**

---

## 工具链

### 项目管理 (uv)

```bash
uv init my-project          # 创建新项目
uv add requests             # 添加依赖
uv add --dev pytest        # 添加开发依赖
uv sync                     # 同步安装
uv run python script.py     # 在虚拟环境中运行
```

- 每个项目必须有 `pyproject.toml`，不用 `requirements.txt` / `setup.py`
- `uv.lock` 必须提交到 Git，确保依赖版本一致
- Python 版本用 `.python-version` 指定

### pyproject.toml 示例

```toml
[project]
name = "my-tool"
version = "0.1.0"
requires-python = ">=3.11"

[tool.black]
line-length = 100
target-version = "py311"
```

Black 默认强制统一风格，无需额外配置。Qt API 的 camelCase 不会被 Black 影响（Black 只格式化自己的代码）。

---

## 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块/文件名 | snake_case | `deploy_toolkit.py` |
| 类 | PascalCase | `DeployConfig` |
| 函数/方法 | snake_case | `copy_skills()`, `resolve_target()` |
| 变量 | snake_case | `target_root`, `deploy_rules` |
| 常量 | UPPER_SNAKE | `PRESET_TARGETS`, `DEFAULT_TIMEOUT` |
| 私有成员 | `_` + snake_case | `_validate_path()`, `_pending_jobs` |
| 类型变量 | PascalCase | `PathLike` |

### `_` vs `__` 前缀

| 写法 | 含义 | 继承行为 |
|------|------|---------|
| `_name` | 内部使用（约定） | **子类可访问、可覆盖** |
| `__name` | 名称修饰（name mangling） | 子类不可直接访问，Python 改写为 `_ClassName__name` |
| `__name__` | 魔术方法 | 不要自己发明这种名字 |

**使用场景：**

```python
class Base:
    def _internal(self) -> None:     # 子类可以覆盖
        ...

    def __private(self) -> None:     # 子类无法直接覆盖
        ...

class Child(Base):
    def _internal(self) -> None:     # ✅ 正确覆盖
        ...

    def __private(self) -> None:     # ❌ 这定义的是新方法，不是覆盖
        ...
```

> 常规私有成员用单下划线 `_`。双下划线 `__` 只在需要避免子类意外重名时使用（如框架基类），日常开发几乎用不到。

### PySide6 适配

Qt API 是 camelCase，与 PEP 8 snake_case 共存于同一文件：

```python
# 自己代码 snake_case + Qt API camelCase — 风格自然区分
def load_config() -> None:
    self.setWindowTitle(config["title"])      # Qt API 不变
    header = self.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
```

两种风格形成视觉区分——看到 snake_case 知道是纯 Python 代码，看到 camelCase 知道是在和 Qt 交互。不推荐 `from __feature__ import snake_case`，那会抹掉这个信号。

### QML 对接说明

暴露给 QML 的信号/属性名用 camelCase（与 QML 侧一致），Python 侧的辅助函数用 snake_case：

```python
class DownloadManager(QObject):
    # 信号 — camelCase（与 QML 对接）
    progressChanged = Signal(int)
    downloadFinished = Signal(str)

    @Slot(str)
    def start_download(self, url: str) -> None:   # Python 侧 snake_case
        ...
```

```python
class ViewModel(QObject):
    def get_title(self) -> str:                   # Python 侧 snake_case
        return self._title

    def set_title(self, value: str) -> None:
        self._title = value

    # Q_PROPERTY — camelCase（暴露给 QML）
    titleChanged = Signal()
    title = Property(str, get_title, set_title, notify=titleChanged)
```

---

## Import 排序

三段空行分隔，组内按字母序：

```python
# 1. 标准库
import argparse
import shutil
from pathlib import Path

# 2. 第三方库
import requests
from rich.console import Console

# 3. 本地模块
from .config import PRESET_TARGETS
```

- 禁止 `from module import *`
- 禁止在函数内部 import（除非处理循环导入）

---

## 类型注解

```python
# 函数签名必须有类型注解（Python 3.10+ 联合类型语法）
def resolve_target(name: str | None) -> Path:
    ...

# 复杂类型用别名
TargetMap = dict[str, Path]

# dataclass 优于 dict
from dataclasses import dataclass, field

@dataclass
class DeployResult:
    created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
```

---

## 字符串与路径

```python
# f-string 优先
msg = f"处理 {filename} 失败: {e}"
path = f"{base_dir}/{sub_dir}/{name}.json"

# Path 拼接代替 os.path
from pathlib import Path
config_dir = Path("config") / "projects"
```

---

## 脚本结构

```python
#!/usr/bin/env python3
"""模块级 docstring — 一句话概括。"""

import argparse
import sys
from pathlib import Path

# --- 常量 ---
DEFAULT_TIMEOUT = 30

# --- 核心逻辑 ---
def main() -> None:
    ...

# --- 入口 ---
if __name__ == "__main__":
    main()
```

---

## 错误处理

- **脚本用 `sys.exit(1)`**：不抛异常到 stderr 裸堆栈
- **库用自定义异常**：继承 `Exception`
- **`assert` 只在测试中用**：`python -O` 会跳过

---

## 常见陷阱

- **可变默认参数**：`def f(lst=[])` 多次调用共享同一对象。用 `def f(lst: list | None = None)`
- **`shutil.copytree` 目标已存在时报错**：用 `dirs_exist_ok=True`（3.8+）
- **`subprocess.run` 不检查返回码**：加 `check=True`
- **Windows 编码**：`open()` 默认 GBK，始终显式 `encoding="utf-8"`
- **`print` 输出缓冲**：管道重定向时加 `flush=True`
- **`is` vs `==`**：`None` 用 `is None`，字符串/数字用 `==`
- **for 循环修改迭代对象**：遍历副本 `for x in list(my_list):`

---

## 本项目 (toolkit) 额外约定

- **`argparse` 统一**：所有脚本用 `argparse`，不用 `sys.argv` 裸解析
- **`--dry-run` / `-n`**：预览模式是脚本标配
- **命令返回码**：成功 0，参数错误 2，运行时错误 1
- **中文输出可接受**：面向开发者的工具，`print` 中文比英文更直观
