---
applyTo: "**/*.{cpp,h,hpp}"
description: Qt/C++ 编码规范 — 命名、声明顺序、文件结构
---

# Qt/C++ 编码规范

格式化由 `.clang-format` 统一管理（`config/clang-format/`，Qt Creator 风格）。

## 核心原则

- 可读性优先于微优化；格式交给 .clang-format
- 类声明顺序固定：Q_OBJECT → Q_PROPERTY → public → signals → public slots → protected → private
- .cpp 实现与 .h 声明顺序一致；头文件用前置声明代替 include
- 父对象管理优先（设 parent 不手动 delete）；释放用 `deleteLater()`
- 信号槽新式语法（编译期检查）；`m_` / `s_` 前缀成员变量
- 复杂即拆分：类臃肿时提取新类，职责单一；函数超过 60 行考虑拆分

## 常见陷阱

- QObject 不可拷贝 → 必须 `Q_DISABLE_COPY_MOVE`
- `Q_ASSERT` 在 Release 不执行 → 用显式 `if` 判空
- `qDeleteAll` 只删直接子节点 → 子孙靠 parent 管理
- 隐式共享 `operator[]` 触发深拷贝 → 只读用 `.value()`
- `Qt::DirectConnection` 跨线程不安全 → 用默认 `AutoConnection`
- 析构前中断异步操作 → `abort()` / `stop()` 再 `deleteLater()`
- `QString::arg` 链式被前值干扰 → 用多参数重载 `.arg(a, b)`
- 范围 for 用 `auto` 触发深拷贝 → 不修改用 `const auto&`
- switch 枚举写 `default` → 显式列出所有值，利用 `-Wswitch`
- connect lambda 不传 context → 对象销毁后崩溃，传 `this` 作第 3 参数
- 跨线程操作 GUI → 用 `QMetaObject::invokeMethod` 回到主线程
- Model 直接改数据不调 beginXxx → 必须 `beginInsertRows`/`endInsertRows` 包裹
- 重载信号 connect 歧义 → 用 `QOverload<T>::of(&Sender::sig)`
- Qt 智能指针过时 → `std::unique_ptr`/`std::shared_ptr` 代替 `QScopedPointer`/`QSharedPointer`
- `qMin`/`qMax`/`qBound` → `std::min`/`std::max`/`std::clamp`（注意 `qBound` 与 `std::clamp` 参数顺序相反）
- `count()`/`length()` → `size()`（与 std 库一致）

> 📖 详见 [references/cpp-pitfalls.md](references/cpp-pitfalls.md)

## 命名约定

| 分类 | 风格 | 示例 |
|------|------|------|
| 类名/文件名 | PascalCase | `KRDLWorker`, `KRDLWorker.h` |
| 函数/方法 | camelCase | `setIsRunning()`, `processNextTask()` |
| 常量 | `k_` + camelCase | `k_maxRetryCount`, `k_tag` |
| 成员变量 | `m_` + camelCase | `m_rate`, `m_isRunning` |
| 静态成员 | `s_` + camelCase | `s_instance` |
| 局部/参数 | camelCase | `reply`, `parent` |
| 宏/导出宏 | UPPER_SNAKE | `KEEPRIX_DOWNLOAD_API` |

- 常量用 `constexpr`（literal 类型）或 `static const`（QString 等），**禁止 `#define` 常量**
- `using` 别名 = 原类型名 + 语义后缀（`StringMap`, `Callback`）

```cpp
// 成员变量
protected:
    qreal m_rate = 1.0;
private:
    static ClassName *s_instance;
```

### getter / setter

遵循 `Q_PROPERTY` 风格（getter 不加 `get`）。**内部修改走 setter**：

```cpp
void reset() { setRate(1.0); }   // ✅
void reset() { m_rate = 1.0; }   // ❌ 绕过 setter，可能漏信号
```

### 信号命名

过去式或描述性动词：`rateChanged()`, `errorOccurred()`

## 文件命名

- `.h`/`.cpp` 同名配对，类名 = 文件名（PascalCase）：`KRDLWorker.h` / `KRDLWorker.cpp`
- 私有实现头文件用 `_p.h`：`KRDLWorker_p.h`（d-pointer 惯例）
- 测试文件 `tst_<类名>.cpp`（Qt Test 惯例）：`tst_krdlworker.cpp`
- 单类一文件；小工具类可合并；公共工具函数放 `utils.h` / `utils.cpp`

## 类声明顺序

```
Q_OBJECT → Q_PROPERTY → public → signals → public slots → protected → private
```

每节内先按功能分组（`// == 下载 ==`），组内固定顺序：**静态函数 → 只读函数 → 操作函数**（`static` 工厂 / `const` 只读 / 修改状态的 setter 与动作）。

成员变量集中在各访问控制节末尾，按功能分组（与函数分组对应），同组内 `k_` 常量 → `s_` 静态 → `m_` 实例。

> 📖 完整示例见 [references/cpp-patterns.md](references/cpp-patterns.md)

## 头文件组织

- `""` 引号：项目内头文件，先查本文件所在目录（`"Helper.h"`、相对路径 `"../MyClass.h"`）
- `<>` 尖括号：标准库 / 系统 / Qt 头文件，只在 include 搜索路径查找（`<QObject>`、`<vector>`）

```cpp
#pragma once

// include 顺序：自身 → 系统 → 标准库 → Qt → 跨模块 → 同模块
#include "../MyClass.h"   // "" 项目内
#include <QObject>        // <> 标准库 / 系统 / Qt
#include "Helper.h"       // "" 项目内

// 前置声明代替 include
class QNetworkReply;
```

## Qt 必备

```cpp
class MyClass : public QObject {
    Q_OBJECT
    Q_DISABLE_COPY_MOVE(MyClass)
public:
    explicit MyClass(QObject *parent = nullptr);
};
```

- `public slots` 优先于 `Q_INVOKABLE`（除非需要返回值）
- QML 暴露用 `QML_ELEMENT` + `qt_add_qml_module()`

## 信号槽

- 新式 PMF：`connect(sender, &Sender::sig, this, &MyClass::slot)`
- **优先成员函数而非 lambda**：便于调试和阅读
- **信号尽量不带参数**：信号只通知，不传数据

## 参数传递

- **按值传递**，不用 const 引用：`void setName(QString name);`
- 不滥用 `std::move` — 只在转移所有权时用（RVO 已覆盖多数场景）
- 指针判空显式比较：`if (ptr != nullptr)`

## 编码铁律

- **const**：不修改成员的函数标记 `const`
- **override**：所有重写虚函数必须加
- **nullptr**：不用 `NULL` 或 `0`
- **auto**：非基本类型用 `auto`，基本类型（int/bool/qreal）显式写
- **大括号**：`if` / `for` / `while` 必须 `{}`，即使一行
- **禁止嵌套调用**：`auto r = f(x); g(r);` 而非 `g(f(x))`
- **非单行函数**：函数体必须多行，不用 `void f() { ... }`
- **扁平化**：if 嵌套 ≤2 层；条件拆为多个简单 if；重复调用提取变量
- **单出口**：`do { ... } while(false)` + `break`，禁止中途 `return`
- **属性守卫**：setter 先 `if (m_x == x) return;` 再赋值
- **Q_ENUM**：暴露给元对象的枚举须注册
- **switch 枚举不写 default**：显式列出所有值
- **static_cast**：类型转换用 `static_cast`，不用 C 风格 `(int)x`
- **.h 禁止 using namespace**：污染所有包含此头文件的翻译单元
- **构造函数不调虚函数**：派生类尚未构造，虚函数表指向基类
- **禁止 unsigned → signed 比较**：隐式转换导致负数变巨大正数
- **时间用 chrono**：`QDeadlineTimer` / `std::chrono`，不用裸 int/qint64
- **错误检查**：I/O、JSON 解析、网络请求必须检查返回值

```cpp
if (!file.open(QIODevice::ReadOnly)) {
    emit errorOccurred(file.errorString());
    return;
}
```

> 📖 设计模式、模板等参见 [references/cpp-patterns.md](references/cpp-patterns.md)
