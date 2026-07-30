---
applyTo: "**/*.{cpp,h,hpp}"
description: Qt/C++ 编码规范 — 命名、声明顺序、文件结构
---

# Qt/C++ 编码规范

格式化由 `.clang-format` 统一管理（参考 `config/clang-format/`，Qt Creator 风格），以下为人工遵守的规则和习惯。

---

## 核心原则

- **格式交给 .clang-format**：括号位置、缩进、空格由工具统一管理
- **类声明顺序固定**：Q_OBJECT → public → signals → slots → protected → private，成员变量在各节末尾
- **实现与声明顺序一致**：.cpp 中的实现严格按照 .h 的声明顺序排列，不混杂
- **头文件暴露最少接口**：实现细节放 .cpp，前置声明代替 include
- **父对象管理优先**：能设 parent 就不手动 delete
- **信号槽新式语法**：编译期检查优于运行期字符串匹配
- **`m_` / `s_` 前缀成员变量**：实例成员用 `m_`，静态成员用 `s_`，与 Qt 源码习惯一致
- **复杂就拆分**：一个类过于臃肿时，提取为新类，职责单一比大而全更易维护

---

## 常见陷阱

以下是 Agent 最容易忽略、但后果严重的 C++ 行为细节：

- **QObject 不可拷贝**：忘记 `Q_DISABLE_COPY_MOVE` 不会编译报错，但运行时拷贝 QObject 会导致双重释放或信号槽断裂。
- **`Q_ASSERT` 在 Release 中不执行**：`Q_ASSERT(ptr != nullptr); ptr->doSomething();` — Release 下断言被跳过，空指针直接崩。用显式 `if` 判空。
- **`qDeleteAll` 只删直接子节点**：`qDeleteAll(container)` 不会递归删除孙子节点。子孙 QObject 应设 parent 靠对象树管理。
- **隐式共享容器 `operator[]` 触发深拷贝**：对 `QHash`/`QMap` 只读操作用 `.value()` 而非 `operator[]`，后者在 key 不存在时会插入默认值并触发 detach。
- **跨线程信号自动排队，但 `Qt::DirectConnection` 不会**：worker 线程 emit 信号时用 `Qt::AutoConnection`（默认），Qt 会自动将参数拷贝到接收者线程。手动指定 `Qt::DirectConnection` 会导致接收者槽在 worker 线程执行。
- **析构时忘记中断异步操作**：`QNetworkReply`/`QTimer` 在析构前必须 `abort()`/`stop()`，否则回调访问已销毁的 `this`。
- **`QString::arg` 链式调用被前值干扰**：`.arg(a).arg(b)` 中第一个 arg 的替换值如果包含 `%1`、`%2`，会被后续 `.arg()` 错误替换。用多参数重载 `QString("%1/%2").arg(dir, fileName)`。
- **范围 for 对隐式共享容器用 `auto` 而非 `const auto&`**：`for (auto x : list)` 触发不必要的深拷贝。不修改元素时始终用 `const auto&`。
- **枚举 switch 写 `default:`**：新增枚举值时编译器不会警告，新增值静默走进 `default` 分支。显式列出所有枚举值，利用 `-Wswitch` 编译期检查。

---

## Modern C++

使用 C++17 特性，摒弃 C++98/03 旧写法：

| 应使用                             | 避免                                 |
| ---------------------------------- | ------------------------------------ |
| `enum`（配合 `Q_ENUM`）            | `enum class`（无法注册到元对象系统） |
| `using` 别名（简化长类型）         | `typedef` / 手写长类型               |
| 范围 for（`for (auto &x : list)`） | 下标 for（`for (int i = 0; ...)`）   |
| 传值 + RVO/NRVO                    | 手动拷贝 / `return std::move(...)`    |
| `nullptr`                          | `NULL` / `0`                         |
| `auto`                             | 显式冗长类型                         |
| `constexpr`                        | `#define` 常量                       |
| `= default` / `= delete`           | 空实现 / 不声明                      |
| 类内初始化（`int m_count = 0`）    | 构造函数中赋值全部成员               |
| 容器 `emplace_back`                | `push_back` + 临时对象               |
```cpp
// ✅ C++17（需要 Q_ENUM 时用普通 enum，无需注册的用 enum class）
enum Status { Idle, Running, Finished };
using StringList = QVector<QString>;         // 简化长类型
using Callback = std::function<void(int)>;  // 简化复杂签名
constexpr int k_maxRetries = 3;              // 字面量类型 → constexpr
constexpr auto k_defaultTimeout = 5000ms;    // C++14 chrono 字面量
static const QString k_tag = "Toolkit";      // 非字面量类型 → static const

for (const auto &item : items) {
    item.process();
}

auto pos = data.indexOf(',');
if (pos != -1) {
    auto value = data.left(pos);
}

// ❌ 旧写法
typedef QVector<QString> StringList;
#define MAX_RETRIES 3

for (int i = 0; i < items.size(); ++i) {
    items[i].process();
}
```

---

## 设计哲学

**编程是将一组数据转化为另一组数据的过程。** 代码分为两类：

|          | 数据                   | 操作者                        |
| -------- | ---------------------- | ----------------------------- |
| 类型     | `struct`               | `class`（尽量继承 QObject）   |
| 职责     | 承载数据               | 处理/转换数据                 |
| 成员函数 | 尽可能少               | 按功能组织                    |
| 成员变量 | 公开（调用者直接读写） | 不暴露（`m_` 前缀 + private） |
| 生命周期 | 值传递 / 栈分配        | Qt 对象树 / parent 管理       |

- **数据**用 `struct`，轻量、透明、可拷贝。只带必要的构造和转换函数
- **操作者**用 `class`，管理状态、执行逻辑、跨线程通信。通过信号对外通知，不暴露内部数据

```cpp
// 数据 — struct，无行为
struct DownloadTask {
    QString url;
    QString savePath;
    qint64 fileSize = 0;
};

// 操作者 — class，带 QObject
class Downloader : public QObject
{
    Q_OBJECT

public:
    void start(DownloadTask task);

signals:
    void finished();

private:
    DownloadTask m_task;
};
```

---

## 命名约定

| 分类          | 风格                   | 示例                                        |
| ------------- | ---------------------- | ------------------------------------------- |
| **类型**      |                        |                                             |
| 类名          | PascalCase，项目前缀   | `KRDLWorker`, `KRCRThread`                  |
| 文件名        | PascalCase，与类名一致 | `KRDLWorker.h` / `.cpp`                     |
| 枚举类型 & 值 | PascalCase             | `enum State { Idle, Checking, Decrypting }` |
| `using` 别名  | PascalCase，语义化后缀 | `AnswerPageList`, `StringMap`, `Callback`   |
| **函数**      |                        |                                             |
| 函数 / 方法   | camelCase              | `setIsRunning()`, `processNextTask()`       |
| **变量**      |                        |                                             |
| 常量          | `k_` 前缀 + camelCase  | `k_maxRetryCount`, `k_tag`                  |
| 成员变量      | `m_` 前缀 + camelCase  | `m_rate`, `m_isRunning`, `m_task`           |
| 静态成员变量  | `s_` 前缀 + camelCase  | `s_instance`, `s_defaultTimeout`            |
| 局部变量      | camelCase              | `reply`, `task`, `thread`                   |
| 参数          | camelCase              | `QWidget *parent`, `qreal rate`             |
| **预处理器**  |                        |                                             |
| 宏 / 导出宏   | 大写 + 下划线          | `KEEPRIX_DOWNLOAD_API`, `Q_DECL_EXPORT`     |

> **常量定义规则**：常量必须用 `constexpr` 或 `static const` 声明，**禁止使用 `#define` 定义常量**。`k_` 前缀表示不可变，与 `m_` / `s_` 前缀系统保持一致。对于 literal type（int、double、enum 等）用 `constexpr`，对于非 literal type（QString、QColor 等）用 `static const` / `inline static const`。宏（预处理器符号）不受此规则约束，仍用大写 + 下划线。
>
> **`using` 别名规则**：以**原类型名 + 语义后缀**命名。容器别名用 `原类型 + List/Map/Hash`（`AnswerPageList`、`StringMap`），函数别名用 `原类型 + Fn` 或功能名（`Callback`、`ErrorHandler`）。不发明与原类型无关的名称。

### 成员变量前缀：`m_` / `s_`

使用 `m_`（实例成员）和 `s_`（静态成员）前缀，protected 和 private 统一风格：

```cpp
protected:
    qreal m_rate = 1.0;
    bool m_isRunning = false;

private:
    static ClassName *s_instance;
    QString m_error;
    int m_maxConcurrent = 3;
```

> 注意：`m_` / `s_` 前缀完全符合 C++ 标准规范，不存在 `_` 前缀在全局命名空间的保留标识符问题。

### getter / setter

遵循 `Q_PROPERTY` 风格，getter 不加 `get` 前缀。参数按值传递，不使用 const 引用。

**有 setter 就用 setter**：类内部修改属性时，优先调用 setter 而非直接赋值，确保信号通知、校验等逻辑一致性：

```cpp
// ✅ 内部修改也走 setter
void KRDLWorker::reset()
{
    setRate(1.0);
    setError({});
}

// ❌ 绕过 setter 直接赋值，可能遗漏信号
void KRDLWorker::reset()
{
    m_rate = 1.0;
    m_error.clear();
}
```

### 信号命名

过去式或事件描述性动词：

```cpp
signals:
    void rateChanged();
    void isRunningChanged();
    void errorChanged();
```

---

## 类声明顺序

严格按以下顺序排列，每个节区中**方法在前，成员变量在后**：

```
1.  Q_OBJECT
2.  Q_PROPERTY（如有）
3.  public:      构造函数 / 析构函数 / 公开方法 / 静态方法
4.  signals:     信号
5.  public slots:公开槽
6.  protected:   受保护方法 → 受保护成员变量
7.  private:     私有方法 → 私有成员变量
```

### 节区内的分组原则

每个节区内部按**功能/需求**分组，组内**只读函数在前，操作函数在后**，用 `// == xxx ==` 注释分隔：

```cpp
public:
    // == 下载 ==
    qreal rate() const;               // getter/setter 在功能组内
    void setRate(qreal rate);
    bool isRunning() const;
    void startDownload();             // 操作在后
    void stopDownload();

    // == 转换 ==
    QString format() const;           // getter/setter 在功能组内
    void setFormat(QString format);
    void convert();
    void cancelConvert();
```

- **getter / setter 属于对应功能** — 放在功能组内，不单独拆出去
- **每个功能组内**：先 getter/setter（只读在前），再操作函数
- **跨功能共享的属性**（如 `enabled`）放在所有功能组之前，作为公共属性
- **空节区省略**：某个节区没有内容直接不写
- **成员变量在各节末尾**：永远放在方法之后

---

## 头文件组织

### Include 顺序

按从最稳定到最易变的顺序排列，每组之间空行，组内按字母序：

```cpp
// 1. 对应的头文件（第一个，检测遗漏依赖）
#include "../KRDLWorker.h"

// 2. 系统级头文件
#include <Windows.h>

// 3. 标准库
#include <memory>
#include <vector>

// 4. Qt 头文件（按字母序）
#include <QDebug>
#include <QFileInfo>
#include <QNetworkReply>

// 5. 跨模块项目头文件
#include <KeeprixCore/KRCR.h>

// 6. 同模块头文件
#include "FFmpegConverter.h"
#include "FFprobeParser.h"
```

### Include Guard

```cpp
#pragma once
```

### 前置声明

头文件中能前置声明就不要 `#include`，尤其对指针类型成员：

```cpp
class QNetworkReply;
class SubtitleTranscoder;
class FFmpegConverter;

class KRDLConverter : public KRDLWorker
{
    Q_OBJECT
    FFmpegConverter *m_converter = nullptr;
};
```

---

## 注释规范

公共 API 在头文件中写简要中文注释，说明用途和注意事项：

```cpp
// 创建一个已启动的线程
static KRCRThread *create(const QString &name, QObject *parent);

// 超时，单位毫秒，-1 代表没有超时
int timeout() const;
```

实现文件中的关键逻辑写行内注释，复杂流程分段说明：

```cpp
// ★ 必须先调 onStarted（让接收方连上自己的 slot），再连队列 handler。
// 否则 finished 发射时队列 handler 先执行，递归 processQueue 启动新任务后
// 新任务的 onStarted 回调会覆盖接收方的 reply 成员，导致 done() 拿到野指针。
connect(reply, &QNetworkReply::finished, this, [this]() {
    onFinished();
});
```

> 不使用 Doxygen 风格（`/** @brief */`），用简单 `//` 注释即可。

---

## 文件结构模板

### .h 文件

```cpp
#pragma once

#include <QObject>
#include <QString>

class QNetworkReply;

class MODULE_API MyClass : public QObject
{
    Q_OBJECT

public:
    explicit MyClass(QObject *parent = nullptr);
    ~MyClass() override;

    // == 属性 ==
    QString name() const;
    void setName(QString name);

    // == 动作 ==
    void reset();

signals:
    void nameChanged(QString name);

private:
    QString m_name;
    int m_counter = 0;
};
```

### .cpp 文件

实现顺序严格按照头文件的声明顺序，从上到下依次实现，便于对照阅读。

```cpp
#include "../MyClass.h"
#include <memory>
#include <QDebug>

namespace {
    constexpr int k_maxRetries = 3;
    static const QString k_tag = "Toolkit";
    QString sanitize(const QString &input) { return input.trimmed().toLower(); }
}

MyClass::MyClass(QObject *parent)
    : QObject(parent)
{
}

MyClass::~MyClass() = default;

QString MyClass::name() const
{
    return m_name;
}

void MyClass::setName(QString name)
{
    if (m_name != name) {
        m_name = name;
        emit nameChanged(m_name);
    }
}
```

---

## Qt 规范

### Q_OBJECT

所有继承 `QObject` 的类必须写，紧跟 `{` 之后：

```cpp
class MyClass : public QObject
{
    Q_OBJECT
};
```

### Q_DISABLE_COPY_MOVE

所有 QObject 子类必须禁用拷贝/移动，QObject 不可拷贝：

```cpp
class MyClass : public QObject
{
    Q_OBJECT
    Q_DISABLE_COPY_MOVE(MyClass)
};
```

### explicit 构造函数

单参数构造函数必须加 `explicit`：

```cpp
explicit MyClass(QObject *parent = nullptr);
```

### QML 与 C++ 调用权限一致

从 QML 能调用的方法，C++ 也应该能调；C++ 中 `private` 的不应通过 `Q_INVOKABLE` 暴露给 QML。保持两边的访问权限一致。

### Q_INVOKABLE 与 public slots

优先使用 `public slots`，除非需要从 QML 获取返回值（`public slots` 有返回值时在 QML 中调用不太方便），才用 `Q_INVOKABLE`：

```cpp
// ✅ 默认用 public slots（C++ 和 QML 都能连信号、都能调）
public slots:
    void start();
    void stop();

// ✅ 需要返回值时用 Q_INVOKABLE，仍放在 public 区
public:
    Q_INVOKABLE QString formatStatus();

// ❌ 不要用 Q_INVOKABLE 绕过 private 向 QML 暴露内部方法
private:
    Q_INVOKABLE void secretHelper();  // C++ 不能调但 QML 能调 → 权限不一致
```

### 单例模式

QObject 单例使用 `static` 局部变量（C++11 线程安全初始化）配合 `QScopedPointerDeleteLater`，确保线程安全和安全销毁：

```cpp
// xxx.h
class MyClass : public QObject
{
    Q_OBJECT

public:
    static MyClass *instance();

private:
    static MyClass *createInstance();
    MyClass();
};
```

```cpp
// xxx.cpp
MyClass *MyClass::instance()
{
    // C++11 static 保证线程安全初始化
    using Ptr = QScopedPointer<MyClass, QScopedPointerDeleteLater>;
    static Ptr s_instance(createInstance());
    return s_instance.data();
}

MyClass *MyClass::createInstance()
{
    auto inst = new MyClass();
    auto mainThread = QCoreApplication::instance()->thread();
    if (mainThread != inst->thread()) {
        inst->moveToThread(mainThread);
    }
    return inst;
}

MyClass::MyClass()
    : QObject(nullptr)
{
}
```

### 父对象管理

优先指定 parent，利用 Qt 对象树自动释放：

```cpp
auto worker = new KRDLWorker(this);
```

### 优先使用 deleteLater

QObject 及其派生类的释放使用 `deleteLater()` 而非 `delete`，确保未处理完的信号和事件安全结束：

```cpp
// ✅ 安全，处理完当前事件循环再释放
worker->deleteLater();

// ❌ 可能在使用中直接销毁
delete worker;
```

### QSharedData 写时复制（COW）

复杂结构体多处传递时使用 `QSharedData` 实现隐式共享：

```cpp
// MyData.h
class MyData
{
public:
    MyData() : m_data(new Data) {}
    QString name() const { return m_data->name; }
    void setName(QString name) { m_data->name = name; }  // 自动 detach
private:
    struct Data : QSharedData { QString name; };
    QSharedDataPointer<Data> m_data;
};
```

> 写入时自动 detach，多个实例共享同一份数据直到有人修改。

### Content 结构体隐藏实现细节

成员变量过多时用 `Content` 结构体藏到 .cpp，头文件只留指针：

```cpp
// xxx.h
class MyClass : public QObject
{
    Q_OBJECT
public:
    MyClass(QObject *parent = nullptr);
    ~MyClass() override;
    void doSomething();
private:
    struct Content;
    QScopedPointer<Content> m_content;
};

// xxx.cpp
struct MyClass::Content {
    QString name;
    QNetworkReply *reply = nullptr;
};
MyClass::MyClass(QObject *p)
    : QObject(p), m_content(new Content)
{
}

MyClass::~MyClass() = default;

void MyClass::doSomething()
{
    if (m_content->reply != nullptr) {
        m_content->reply->abort();
    }
}
```

> 成员变量 >5 个时考虑使用，与 Qt d-pointer 模式一致。

### 线程设计原则

**兄弟对象（非调用者创建的）必须在同一线程**，直接调用。**子对象（调用者创建的）可以跨线程**，跨线程通信统一用 `QMetaObject::invokeMethod` 传 lambda：

```cpp
// Worker.h — Worker 不感知线程
class Worker : public QObject
{
    Q_OBJECT
public:
    explicit Worker(QObject *host);          // host 用于回调，不设 QObject parent
public slots:
    void process(QByteArray data);
signals:
    void finished();
private:
    QObject *m_host = nullptr;
};

// Worker.cpp
Worker::Worker(QObject *host)
    : QObject(nullptr), m_host(host)
{
}

void Worker::process(QByteArray data)
{
    // 在 Worker 线程执行
    emit finished();
    QMetaObject::invokeMethod(m_host, [this] { /* 主线程回调 */ });
}

// 主线程中
auto thread = new QThread(this);
auto worker = new Worker(this);
worker->moveToThread(thread);
thread->start();

QMetaObject::invokeMethod(worker, [worker] { worker->process(data); });

// 停止
thread->quit(); thread->wait(3000); worker->deleteLater();
```

### 析构时中断异步操作

异步操作必须在析构前中断，避免回调访问已销毁对象：

```cpp
class Downloader : public QObject
{
    Q_OBJECT
public:
    ~Downloader() override
    {
        cancelAll();
    }

    void cancelAll()
    {
        if (m_reply) {
            m_reply->abort();
            m_reply->deleteLater();
            m_reply = nullptr;
        }
        if (m_timer) {
            m_timer->stop();
        }
    }
private:
    QNetworkReply *m_reply = nullptr;
    QTimer *m_timer = nullptr;
};
```

### QML 类型注册

暴露给 QML 的 C++ 类使用 `QML_ELEMENT` 系列宏声明，让 Qt 自动生成类型注册文件，避免手动 `qmlRegisterType()`：

```cpp
class MyClass : public QObject
{
    Q_OBJECT
    QML_ELEMENT                          // 以类名注册到 QML
    // QML_NAMED_ELEMENT("CustomName")   // 或自定义 QML 名称
    // QML_SINGLETON                      // 单例
};
```

配合 `CMakeLists.txt` 中的 `qt_add_qml_module()` 使用，自动生成 `qmldir`。

### 信号设计原则

**信号中尽量不要带参数。** 信号只做通知（"something happened"），不传递数据。跨线程数据传递在类内部处理。

```cpp
signals:
    // ✅ 信号只做通知
    void downloadFinished();
    void statusChanged();

    // ❌ 信号带参数 → 跨线程时参数序列化有开销，且暴露内部数据细节
    void downloadFinished(const QByteArray &data);
    void statusChanged(QString status, int code);
```

### 信号槽连接

使用新式 PMF 语法，编译期类型检查。

**优先使用成员函数而非 lambda**：能用命名成员函数的地方就不用 lambda，便于调试和阅读：

```cpp
// ✅ 成员函数，名称自描述
connect(button, &QPushButton::clicked, this, &MyClass::onClicked);
connect(m_timer, &QTimer::timeout, this, &MyClass::onTimeout);

// ❌ lambda，逻辑内嵌无法独立调试
connect(button, &QPushButton::clicked, this, [this]() {
    submit();
    reset();
    updateUI();
});
```

---

## 通用编码规范

### 参数传递

参数按值传递，不使用 const 引用：

```cpp
// ✅ 按值传递
void setRate(qreal rate);
void setName(QString name);
void setError(QString error);

// ❌ 禁止 const 引用
void setRate(const qreal &rate);
void setName(const QString &name);
```

> 对现代 C++ 和 Qt 的隐式共享类型，按值传递在大多数场景下性能与 const 引用相当，且语义更简洁、避免生命周期问题。对于 `std::unique_ptr` 等移动-only 类型，显式按值传递即可。

### 不要滥用 std::move

编译器（C++17 起）的 RVO / NRVO 和隐式移动已能处理绝大多数场景，显式 `std::move` 反而可能阻止编译器优化（如 RVO）或引入不必要的移动构造：

```cpp
// ✅ 让编译器自己处理
Widget createWidget() {
    Widget w;
    return w;           // NRVO 自动优化，不需要 std::move
}

void process() {
    auto w = createWidget();  // 隐式移动或 RVO
    container.push_back(std::move(w));  // ✅ 这里是有意转移所有权
}

// ❌ 多余的 std::move
Widget createWidget() {
    Widget w;
    return std::move(w);  // 阻止 NRVO，强制走移动构造
}
```

> `std::move` 只在需要**明确转移所有权**时使用（如传入 `std::unique_ptr`、存入容器后不再使用原变量）。作为通用返回值或局部变量传递时不需要。

### 对 Qt 类型的特别说明

Qt 的隐式共享类型（`QString`、`QByteArray`、`QVector` 等）按值传递本身已是 COW 引用计数，`std::move` 对它们的收益极低，反而增加代码噪声。保持一致即可。

### const 正确性

不修改成员变量的函数标记 `const`：

```cpp
QString displayName() const;
```

### 非单行函数

所有函数体必须使用多行写法，即使只有一行：

```cpp
// ✅ 多行
void setName(QString name)
{
    m_name = name;
}

// ❌ 单行
void setName(QString name) { m_name = name; }
```

### 避免隐式转换

数值类型转换使用 `static_cast`，不使用 C 风格括号转换：

```cpp
auto value = static_cast<int>(rate);     // ✅ static_cast
int value = (int)rate;                   // ❌ C 风格
int value = int(rate);                   // ❌ 函数风格
```

### 指针判空显式比较

指针判空写 `!= nullptr` 和 `== nullptr`，不隐式依赖布尔转换：

```cpp
// ✅ 显式比较
if (ptr != nullptr) { /* ... */ }
if (ptr == nullptr) { return; }

// ❌ 隐式布尔转换
if (ptr) { /* ... */ }
if (!ptr) { return; }
```

### 强制大括号

`if` / `for` / `while` 必须使用大括号，即使只有一行：

```cpp
// ✅
if (condition) {
    doSomething();
}

// ❌
if (condition) doSomething();
```

### 代码扁平化

`if` 嵌套不超过 2 层。达到 3 层时提取局部 lambda 或成员函数。

**条件拆分为多个 if**：一个判断条件不要太复杂，拆成多个简单 `if` 更清晰：

```cpp
// ✅ 多个简单 if
if (!task.isValid()) { return; }
if (!task.isReady()) { return; }
if (task.isCancelled()) { return; }

// ❌ 一个 if 塞太多条件
if (!task.isValid() || !task.isReady() || task.isCancelled()) { return; }
```

**重复调用提取变量**：同一对象或函数多次使用时，先提取到本地变量：

```cpp
// ✅ 提取后复用
auto instance = Manager::instance();
auto config = instance->config();
auto status = instance->status();

// ❌ 重复调用
auto config = Manager::instance()->config();
auto status = Manager::instance()->status();
```

**避免多层链式调用**：`a.b().c().d()` 难以调试和阅读，用临时变量拆解：

```cpp
// ✅ 临时变量拆解
auto config = manager->config();
auto timeout = config.timeout();
auto policy = timeout.retryPolicy();

// ❌ 多层链式调用
auto policy = manager->config().timeout().retryPolicy();
```

```cpp
// ✅ 2 层以内 OK
for (auto &item : items) {
    if (item.isValid() && item.isReady()) {
        doProcess(item);
    }
}

// ✅ 3 层 → 提取局部 lambda
auto processItem = [this](const Item &item) {
    if (!item.isValid()) { return; }
    if (!item.isReady()) { return; }
    doProcess(item);
};

for (auto &item : items) {
    processItem(item);
}
```

### 统一入口和出口

函数使用单一出口原则。需要提前退出流程控制时，使用 `do {} while (false)` 配合 `break`，所有结果汇集到最终 `return`：

```cpp
QString formatData(const QByteArray &raw)
{
    auto result = QString();

    do {
        if (raw.isEmpty()) break;

        auto parsed = parse(raw);
        if (!parsed.isValid()) break;

        result = format(parsed);
    } while (false);

    return result;                          // 唯一的 return
}
```

> 通过 `break` 跳出 `do {} while (false)` 块，自然落到统一的返回值处。不要在块内提前 `return`，否则就失去统一出口的意义了。

### override

所有重写的虚函数必须加 `override`，编译器检查签名匹配：

```cpp
~MyClass() override;
void run() override;
void paint(QPainter *painter) override;
```

### QString::arg 多参数

避免链式调用 `.arg().arg()`，后续 `.arg()` 可能错误替换前一个参数值中 `%N` 格式的内容。使用多参数重载一次传入：

```cpp
// ✅ 一次传入，顺序明确
auto path = QString("%1/%2").arg(dir, fileName);

// ❌ 链式调用，容易被前一个值中的 %N 干扰
auto path = QString("%1/%2").arg(dir).arg(fileName);
```

### auto

非基本类型统一用 `auto` 声明（`auto` 已包含指针语义，不需 `auto *`）。仅内置基本类型（`int`、`bool`、`qreal` 等）显式写出：

```cpp
auto worker = new Worker(this);          // ✅ 指针
auto list = QStringList();               // ✅ Qt 类型
auto cacheKey = QString("%1_%2").arg(id, type);    // ✅ 一次传入多参数

int count = items.size();                // ✅ 基本类型显式
bool isValid = false;
qreal rate = 1.0;
```

### 属性变更守卫

setter 中先比较再赋值，避免不必要的信号发射：

```cpp
void MyClass::setName(QString name)
{
    if (m_name == name) { return; }        // ✅ 无变化，跳过
    m_name = name;
    emit nameChanged(m_name);
}
```

### Q_ENUM 注册

需要将枚举暴露给信号、QML 或元对象系统时，使用 `Q_ENUM` 宏：

```cpp
class MyClass : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Status status READ status NOTIFY statusChanged)

public:
    enum Status { Idle, Running, Finished, };
    Q_ENUM(Status)

    Status status() const;
};
```

### switch 枚举不写 default

`switch` 枚举时**不写 `default:` 标签**，显式列出所有枚举值。编译器会在新增枚举值时产生 `-Wswitch` 警告，防止遗漏：

```cpp
// ✅ 列出所有枚举值，无 default
switch (status) {
case Idle:      return "空闲";
case Running:   return "运行中";
case Finished:  return "已完成";
}

// ❌ 有 default — 新增枚举值时编译器不会警告，可能静默走错分支
switch (status) {
case Idle:      return "空闲";
default:        return "未知";
}
```


### nullptr

统一使用 `nullptr`，不用 `NULL` 或 `0`：

```cpp
QNetworkReply *m_reply = nullptr;
```

### C++ 标准

使用 C++17（`.clang-format` 已配置 `Standard: c++17`），可用 `std::optional`、结构化绑定、`if constexpr` 等特性：

```cpp
std::optional<QString> parseTitle(const QByteArray &data);
auto [code, message] = parseResponse(raw);
```

### 错误处理

I/O 操作必须检查返回值，不假定成功：

```cpp
// ✅ 检查 QFile::open()
QFile file(path);
if (!file.open(QIODevice::ReadOnly)) {
    emit errorOccurred(file.errorString());
    return;
}

// ✅ 检查 QJsonDocument
QJsonParseError error;
auto doc = QJsonDocument::fromJson(data, &error);
if (error.error != QJsonParseError::NoError || !doc.isObject()) {
    return;
}

// ✅ 检查 QNetworkReply
connect(reply, &QNetworkReply::finished, this, [reply]() {
    if (reply->error() != QNetworkReply::NoError) {
        handleError(reply->errorString());
        reply->deleteLater();
        return;
    }
    auto data = reply->readAll();
    reply->deleteLater();
});

// ❌ 不检查返回值 — 静默失败
QFile file(path);
file.open(QIODevice::ReadOnly);     // 可能打开失败！
auto data = reply->readAll();       // 没检查 error()！
```
