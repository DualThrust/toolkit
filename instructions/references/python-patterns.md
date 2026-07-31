# Python 模式与参考示例

> 本文从 `python.instructions.md` 中移出的完整代码示例和工具链参考。

---

## uv 命令参考

```bash
uv init my-project          # 创建新项目
uv add requests             # 添加依赖
uv add --dev pytest        # 添加开发依赖
uv sync                     # 同步安装
uv run python script.py     # 在虚拟环境中运行
```

- 每个项目必须有 `pyproject.toml`，不用 `requirements.txt` / `setup.py`
- `uv.lock` 必须提交到 Git
- Python 版本用 `.python-version` 指定

---

## pyproject.toml 示例

```toml
[project]
name = "my-tool"
version = "0.1.0"
requires-python = ">=3.11"

[tool.black]
line-length = 100
target-version = "py311"
```

---

## `_` vs `__` 前缀

| 写法 | 含义 | 继承行为 |
|------|------|---------|
| `_name` | 内部使用（约定） | 子类可访问、可覆盖 |
| `__name` | 名称修饰 | 子类不可直接访问 |
| `__name__` | 魔术方法 | 不要自己发明 |

```python
class Base:
    def _internal(self) -> None:     # 子类可以覆盖
        ...

    def __private(self) -> None:     # 子类无法直接覆盖
        ...

class Child(Base):
    def _internal(self) -> None:     # ✅ 正确覆盖
        ...

    def __private(self) -> None:     # ❌ 这是新方法，不是覆盖
        ...
```

常规私有成员用单下划线 `_`。双下划线 `__` 只在需要避免子类意外重名时使用。

---

## PySide6 适配

Qt API 是 camelCase，与 PEP 8 snake_case 共存。两种风格形成视觉区分——看到 snake_case 是纯 Python，看到 camelCase 是在和 Qt 交互。

```python
def load_config() -> None:
    self.setWindowTitle(config["title"])      # Qt API 不变
    header = self.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
```

---

## QML 对接

暴露给 QML 的信号/属性名用 camelCase，Python 辅助函数用 snake_case：

```python
class DownloadManager(QObject):
    progressChanged = Signal(int)
    downloadFinished = Signal(str)

    @Slot(str)
    def start_download(self, url: str) -> None:
        ...
```

```python
class ViewModel(QObject):
    def get_title(self) -> str:
        return self._title

    def set_title(self, value: str) -> None:
        self._title = value

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

---

## 类型注解

```python
# Python 3.10+ 联合类型语法
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

# Path 拼接代替 os.path
from pathlib import Path
config_dir = Path("config") / "projects"
```

---

## 脚本结构模板

```python
#!/usr/bin/env python3
"""模块级 docstring — 一句话概括。"""

import argparse
import sys
from pathlib import Path

DEFAULT_TIMEOUT = 30

def main() -> None:
    ...

if __name__ == "__main__":
    main()
```
