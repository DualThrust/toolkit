---
applyTo: "**/*.py"
description: Python 编码规范 — PySide6 风格（camelCase），与 Qt C++ 命名对齐
---

# Python 编码规范

> **风格定位：PySide6 / Qt 对齐。** 命名采用 camelCase 以与 Qt C++ API 保持一致（`setWindowTitle` 而非 `set_window_title`）。
> 这是有意偏离 PEP 8 的选择，理由见下方说明。

格式化由 [Ruff](https://docs.astral.sh/ruff/) 统一管理（兼容 Black + isort + flake8），以下为人工遵守的规则和习惯。

---

## 核心原则

- **格式交给 Ruff**：行宽 100，双引号，4 空格缩进，isort 排序 import
- **类型注解全覆盖**：所有函数签名必须有参数类型和返回类型，`Any` 也要显式标注
- **`pathlib` 代替 `os.path`**：跨平台路径操作统一用 `pathlib.Path`
- **`match` 代替长 `if-elif` 链**：Python 3.10+ 的结构化匹配比字典分发更直观
- **dataclass 代替裸 dict**：结构化数据用 `@dataclass`，类型安全且 IDE 友好
- **函数短小**：单个函数不超过 50 行，超过则拆分
- **脚本入口 `main()` + `if __name__ == "__main__"`**：模块化可测试，避免全局执行
- **命名对齐 Qt**：camelCase（`copyDir`、`targetRoot`），与 PySide6 API 风格一致

### 为什么不用 PEP 8 snake_case？

本规范面向 PySide6 应用开发。PySide6 的 Qt API 全部使用 camelCase：

```python
# Qt API 风格 — 你的代码每天和这些打交道
self.setWindowTitle("工具")
self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
```

如果自己的函数用 snake_case，同一文件内会出现两种命名混搭：

```python
# ❌ 风格割裂 — Qt API 驼峰 + 自己蛇形
def load_config():
    self.setWindowTitle(config["title"])
```

统一 camelCase 消除这种不一致。注意：PySide6 也支持 `from __feature__ import snake_case` 反向操作（Qt API 变蛇形），但我们选择与 C++ 侧保持一致，减少跨语言心智负担。

---

## 项目管理 (uv)

使用 [uv](https://docs.astral.sh/uv/) 作为统一的 Python 项目管理工具，替代 pip + venv + pip-tools 的组合。

### 初始化项目

```bash
# 创建新项目
uv init my-project

# 为已有项目初始化
cd existing-project && uv init
```

### 依赖管理

```bash
# 添加运行时依赖
uv add requests rich

# 添加开发依赖
uv add --dev pytest ruff

# 移除依赖
uv remove requests

# 从 pyproject.toml 同步安装全部依赖
uv sync

# 升级所有依赖到最新兼容版本
uv lock --upgrade
```

### 运行与构建

```bash
# 在项目虚拟环境中运行脚本
uv run python deploy.py

# 运行项目入口（pyproject.toml 中 [project.scripts] 定义的命令）
uv run cli-tool --help

# 构建发布包
uv build
```

### 规范要点

- **每个 Python 项目必须有 `pyproject.toml`**：不用 `requirements.txt`、`setup.py`、`setup.cfg`
- **`uv.lock` 必须提交到 Git**：确保所有开发者/CI 环境依赖版本一致
- **用 `uv run` 而非手动激活 venv**：避免"能跑但不在正确环境"的问题
- **Python 版本用 `.python-version` 指定**：`uv init` 自动生成，CI 据此选择解释器
- **Ruff 配置写在 `pyproject.toml`**：`[tool.ruff]` 段，与 uv 统一管理

```toml
# pyproject.toml 示例
[project]
name = "my-tool"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# 允许 camelCase 命名（与 PySide6/Qt 风格对齐）
[tool.ruff.lint]
ignore = ["N802", "N803", "N806", "N813", "N815", "N816"]

[tool.ruff.lint.pep8-naming]
classmethod-decorators = ["classmethod"]
```

- **`N802`**：函数名不强制 snake_case → 允许 `copyDir()`
- **`N803`**：参数名不强制 snake_case → 允许 `targetRoot`
- **`N806`**：变量名不强制 snake_case → 允许 `deployRules`
- **`N813/N815/N816`**：类/异常/全局变量也放宽

---

## 常见陷阱

以下是 Agent 最容易忽略、但后果严重的 Python 行为细节：

- **可变默认参数**：`def f(lst=[])` — 默认值只在函数定义时求值一次，多次调用共享同一对象。用 `def f(lst: list | None = None)` + 内部判空。
- **`shutil.copytree` 目标已存在时报错**：目标目录必须不存在，或用 `dirs_exist_ok=True`（Python 3.8+）。
- **`subprocess.run` 不检查返回码**：默认不抛异常，shell 命令失败静默通过。加 `check=True`。
- **Windows 路径分隔符**：`Path("a/b")` 在 Windows 上自动转 `\`，但字符串拼接 `str(path)` 可能混用。始终用 `Path` 的 `/` 运算符拼接。
- **`os.environ` 修改不跨进程**：子进程继承的是父进程启动时的环境快照，`os.environ["X"] = "y"` 只影响当前进程及其直接 spawn 的子进程。
- **`try-except` 兜底太宽**：`except Exception` 吞掉 `KeyboardInterrupt`、`SystemExit` 以外的异常尚可接受；但 `except:` 裸捕获连 `KeyboardInterrupt` 都吞，进程无法 Ctrl+C 终止。
- **编码声明**：Windows 上 `open()` 默认用 GBK（cp936），读 UTF-8 文件乱码。始终显式 `encoding="utf-8"`。
- **`print` 输出缓冲**：管道/重定向时 `print` 默认块缓冲。脚本输出实时性要求高时 `print(..., flush=True)` 或用 `PYTHONUNBUFFERED=1`。
- **可变对象是引用**：`a = [1,2]; b = a; b.append(3)` — `a` 也变成 `[1,2,3]`。需要独立副本用 `b = a.copy()` 或 `copy.deepcopy()`。
- **`is` vs `==`**：`is` 比较对象身份（同一内存地址），`==` 比较值。`None` 比较用 `is None`/`is not None`，字符串和数字用 `==`。
- **for 循环修改迭代对象**：遍历 list 时删除元素会跳过相邻项。改为遍历副本 `for x in list(my_list):` 或用列表推导式 `[x for x in my_list if condition]`。

---

## 字符串处理

### f-string 优先（Python 3.6+）

```python
# ✅ f-string — 最简洁、最快
msg = f"处理 {filename} 失败: {e}"
path = f"{baseDir}/{subDir}/{name}.json"

# ❌ 旧式写法，不推荐
msg = "处理 %s 失败: %s" % (filename, e)
msg = "处理 {} 失败: {}".format(filename, e)
```

### 多行字符串与缩进

```python
# textwrap.dedent 去掉公共前导空白
from textwrap import dedent

help_text = dedent("""\\
    用法: deploy.py --target <项目>

    选项:
      -t, --target   目标项目路径或别名
      -n, --dry-run  预览模式
      -u, --update   强制覆盖
""")
```

### 路径拼接

```python
# ✅ Path 运算符 — 跨平台
from pathlib import Path
config = Path("skills") / "qt" / "references"

# ❌ 字符串拼接 — Windows 上 \\ 噩梦
config = "skills\\qt\\references"
```

---

## PySide6 专有约定

### 信号槽

```python
# ✅ 新式语法 — 编译期检查
button.clicked.connect(self.onButtonClicked)
lineEdit.textChanged.connect(self.validateInput)

# ❌ 旧式字符串语法 — 不推荐
# button.clicked.connect("onButtonClicked()")
```

### `__feature__` 不使用

PySide6 提供 `from __feature__ import snake_case` 可将 Qt API 转为 snake_case，但**本规范不使用**：
- 与 C++ 侧代码风格保持一致
- 避免隐式全局状态（feature import 影响整个模块）
- 查阅 Qt 官方文档时方法名直接对应

### QObject 子类

```python
from PySide6.QtCore import QObject, Signal, Slot

class DownloadManager(QObject):
    # 信号声明
    progressChanged = Signal(int)
    downloadFinished = Signal(str)

    @Slot(str)
    def startDownload(self, url: str) -> None:
        ...
```

### 属性：Qt Property 优先

```python
# ✅ 用 Qt Property 绑定到 QML/信号系统
from PySide6.QtCore import Property

class ViewModel(QObject):
    def getTitle(self) -> str:
        return self._title

    def setTitle(self, value: str) -> None:
        self._title = value

    titleChanged = Signal()
    title = Property(str, getTitle, setTitle, notify=titleChanged)
```

---

## 上下文管理器 (`with`)

Python 没有 C++ 的 RAII 析构确定性，用 `with` 语句确保资源释放：

```python
# 文件 — with 自动关闭
with open(path, encoding="utf-8") as f:
    content = f.read()

# 临时目录 — with 自动清理
import tempfile
with tempfile.TemporaryDirectory() as tmpDir:
    download(url, tmpDir)
    process(tmpDir)
# tmpDir 已自动删除

# 锁 — with 自动释放
from threading import Lock
lock = Lock()
with lock:
    sharedData["key"] = value

# 自定义上下文管理器
from contextlib import contextmanager

@contextmanager
def workingDir(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)
```

- **读写文件永远用 `with open()`**：不用手动 `.close()`
- **`contextlib.closing()` 包装不支持 `with` 的老式对象**

---

## 常用标准库速查

Python 标准库极其丰富，以下是最常用的模块（来自 C++ 背景尤其值得了解）：

| 模块 | 用途 | 典型场景 |
|------|------|----------|
| `pathlib` | 路径操作 | 替代 `os.path`，`Path` 对象 `/` 拼接 |
| `shutil` | 文件/目录复制 | `copy2()`, `copytree()`, `rmtree()` |
| `subprocess` | 执行外部命令 | `run(cmd, check=True, capture_output=True)` |
| `argparse` | CLI 参数解析 | 所有脚本的标准入口 |
| `json` | JSON 读写 | `load()`/`dump()` 操作文件, `loads()`/`dumps()` 操作字符串 |
| `tomllib` | TOML 读写 (3.11+) | 解析 `pyproject.toml` 等配置文件 |
| `dataclasses` | 数据类 | `@dataclass` 替代手写 `__init__` |
| `itertools` | 迭代器工具 | `chain()`, `groupby()`, `product()` |
| `functools` | 高阶函数工具 | `@lru_cache`, `partial()`, `reduce()` |
| `collections` | 容器扩展 | `defaultdict`, `Counter`, `deque` |
| `logging` | 日志记录 | 生产级日志代替 `print` 调试 |
| `tempfile` | 临时文件/目录 | `TemporaryDirectory()` 自行清理 |
| `textwrap` | 文本格式化 | `dedent()` 格式化多行字符串 |
| `re` | 正则表达式 | 复杂文本匹配提取 |
| `hashlib` | 哈希摘要 | `sha256()`, `md5()` 文件校验 |

---

## 测试 (pytest)

```bash
# 安装
uv add --dev pytest

# 运行
uv run pytest                           # 自动发现 test_*.py
uv run pytest -v                        # 详细输出
uv run pytest -k "test_copy"            # 按名称筛选
```

```python
# tests/test_deploy.py
import pytest
from deploy import copy_dir

@pytest.fixture
def sample_tree(tmp_path: Path) -> Path:
    \"\"\"pytest 内置 tmp_path 自动创建并清理。\"\"\"
    (tmp_path / "src" / "a.txt").write_text("hello")
    return tmp_path

def test_copy_creates_files(sample_tree: Path) -> None:
    created, skipped = copy_dir(
        sample_tree / "src",
        sample_tree / "dst",
    )
    assert created == 1
    assert (sample_tree / "dst" / "a.txt").exists()

def test_copy_skips_existing(sample_tree: Path) -> None:
    # 第一次复制
    copy_dir(sample_tree / "src", sample_tree / "dst")
    # 第二次应跳过
    _, skipped = copy_dir(sample_tree / "src", sample_tree / "dst")
    assert skipped == 1
```

- **`tmp_path` fixture 自动创建临时目录，测试结束自动清理**
- **函数名以 `test_` 开头，pytest 自动发现**
- **`assert` 在测试中是推荐用法**（pytest 会展开失败信息）

---

## 命名约定

采用 camelCase，与 PySide6/Qt C++ 风格对齐。

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块/文件名 | snake_case（文件系统惯例） | `deploy_toolkit.py` |
| 类 | PascalCase | `DeployConfig` |
| 函数/方法 | camelCase | `copySkills()`, `resolveTarget()` |
| 变量 | camelCase | `targetRoot`, `deployRules` |
| 常量 | UPPER_SNAKE（业界惯例） | `PRESET_TARGETS`, `DEFAULT_TIMEOUT` |
| 私有成员 | `_` 前缀 + camelCase | `_validatePath()`, `_pendingJobs` |
| 类型变量 | PascalCase | `PathLike` |

> **例外**：文件名保持 snake_case（文件系统跨平台兼容）。常量和模块级配置保持 UPPER_SNAKE（Python 工具链依赖此约定识别常量）。

---

## Import 排序

按 isort 规则，分三段空行分隔：

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
- `typing` 相关导入集中在文件顶部

---

## 类型注解

```python
from typing import Any, Dict, List, Optional, Tuple

# 函数签名必须有类型注解
def resolveTarget(name: str | None) -> Path:
    ...

# 复杂类型用别名
TargetMap = Dict[str, Path]

# Optional 用 | None（Python 3.10+）
def findProject(name: str) -> Path | None:
    ...

# dataclass 优于 dict
from dataclasses import dataclass, field

@dataclass
class DeployResult:
    created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
```

---

## 脚本结构

```python
#!/usr/bin/env python3
"""模块级 docstring — 一句话概括 + 详细说明。"""

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
- **库用自定义异常**：继承 `Exception`，不用字符串匹配
- **`assert` 只在测试中用**：`python -O` 会跳过 assert，业务逻辑用 `if` + `raise`

---

## 工具脚本特殊规范

本项目（toolkit）以工具脚本为主，额外约定：

- **`argparse` 统一**：所有脚本用 `argparse`，不用 `sys.argv` 裸解析
- **`--dry-run` / `-n`**：预览模式是脚本标配
- **命令返回码**：成功 0，参数错误 2，运行时错误 1
- **中文输出可接受**：面向开发者的工具，`print` 中文比英文更直观
