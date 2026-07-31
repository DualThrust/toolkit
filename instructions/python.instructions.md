---
applyTo: "**/*.py"
description: Python 编码规范 — PEP 8 snake_case，PySide6 适配说明
---

# Python 编码规范

> snake_case（PEP 8）与 Qt camelCase 共存 —— 风格差异是跨语言信号。

格式化由 Black（行宽 100，双引号，4 空格）+ isort 统一管理。

## 核心原则

- 可读性优先；格式交给 Black/isort
- **PEP 8 命名**：函数/变量 snake_case，类 PascalCase，常量 UPPER_SNAKE
- **类型注解全覆盖**：所有函数签名必须有参数和返回类型
- `pathlib` 代替 `os.path`；`@dataclass` 代替裸 dict
- `match` 代替长 `if-elif`（3.10+）
- 函数短小单一职责；超过 50 行考虑拆分（调度/编排函数例外）
- 所有脚本入口：`main()` + `if __name__ == "__main__"`
- 用 `uv` 管理项目，`pyproject.toml` 必须存在

## 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| 模块/文件 | snake_case | `deploy_toolkit.py` |
| 类 | PascalCase | `DeployConfig` |
| 函数/方法/变量 | snake_case | `copy_skills()` |
| 常量 | UPPER_SNAKE | `DEFAULT_TIMEOUT` |
| 私有成员 | `_` + snake_case | `_validate_path()` |

### `_` vs `__`

| 写法 | 含义 |
|------|------|
| `_name` | 内部约定，子类可访问覆盖 |
| `__name` | 名称修饰，子类不可直接访问 |
| `__name__` | 魔术方法，不要自己发明 |

常规用 `_`，双下划线 `__` 极少需要。

## PySide6 / QML 适配

Qt API 保持 camelCase（`self.setWindowTitle(...)`），自己代码 snake_case。
风格差异即信号——camelCase = Qt 交互，snake_case = 纯 Python。

暴露给 QML 的信号/属性名用 camelCase，Python 辅助函数 snake_case：

```python
class Manager(QObject):
    progressChanged = Signal(int)            # camelCase → QML

    @Slot(str)
    def start_download(self, url: str): ...  # snake_case → Python 侧

    def get_title(self) -> str: ...          # snake_case
    title = Property(str, get_title, ...)    # camelCase → Q_PROPERTY
```

## Import 排序

三段空行：标准库 → 第三方 → 本地模块。组内字母序。禁止 `from x import *`。

## 类型注解

```python
def resolve(name: str | None) -> Path: ...       # 3.10+ 联合类型
TargetMap = dict[str, Path]                       # 复杂类型别名
```

## 字符串与路径

```python
msg = f"处理 {f} 失败: {e}"                       # f-string
config_dir = Path("config") / "projects"          # Path 拼接
open(path, encoding="utf-8")                      # Windows 显式编码
```

## 常见陷阱

- 可变默认参数 → `def f(lst: list | None = None):`
- `shutil.copytree` 目标存在报错 → `dirs_exist_ok=True`
- `subprocess.run` 不检查返回码 → `check=True`
- Windows `open()` 默认 GBK → 显式 `encoding="utf-8"`
- `print` 管道缓冲 → `flush=True`
- `None` 用 `is None`，不 `==`
- for 修改迭代对象 → 遍历副本 `for x in list(my_list):`

## 错误处理

- 脚本：`sys.exit(1)`，不抛裸异常
- 库：自定义异常继承 `Exception`
- `assert` 只用于测试（`python -O` 跳过）

## 本项目约定

- 所有脚本用 `argparse`；标配 `--dry-run` / `-n`
- 返回码：成功 0，参数错误 2，运行时错误 1

> 📖 完整示例和 uv 命令见 [references/python-patterns.md](references/python-patterns.md)
