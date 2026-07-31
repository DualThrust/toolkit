# C++ 设计模式与高级用法参考

> 本文从 `cpp.instructions.md` 中移出的设计模式、模板和高级用法，供需要时查阅。

---

## Modern C++ 对照表

| 应使用 | 避免 |
|--------|------|
| `using` 别名 | `typedef` |
| 范围 for (`const auto&`) | 下标 for |
| 传值 + RVO/NRVO | 手动拷贝 |
| `nullptr` | `NULL` / `0` |
| `constexpr` | `#define` 常量 |
| `= default` / `= delete` | 空实现 |
| 类内初始化 | 构造函数赋值全部成员 |
| `emplace_back` | `push_back` + 临时对象 |

```cpp
// ✅ C++17
using StringList = QVector<QString>;
constexpr int k_maxRetries = 3;

for (const auto &item : items) {
    item.process();
}
```

---

## 设计哲学：struct vs class

| | 数据 | 操作者 |
|---|---|---|
| 类型 | `struct` | `class`（继承 QObject） |
| 职责 | 承载数据 | 处理/转换数据 |
| 成员函数 | 尽可能少 | 按功能组织 |
| 成员变量 | 公开 | 不暴露（`m_` + private） |
| 生命周期 | 值传递/栈 | Qt 对象树 |

```cpp
// 数据
struct DownloadTask {
    QString url;
    QString savePath;
    qint64 fileSize = 0;
};

// 操作者
class Downloader : public QObject {
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

## 文件结构模板

### .h 文件

```cpp
#pragma once

#include <QObject>

class QNetworkReply;

class MODULE_API MyClass : public QObject
{
    Q_OBJECT

public:
    explicit MyClass(QObject *parent = nullptr);
    ~MyClass() override;

    QString name() const;
    void setName(QString name);
    void reset();

signals:
    void nameChanged(QString name);

private:
    QString m_name;
    int m_counter = 0;
};
```

### .cpp 文件

```cpp
#include "../MyClass.h"
#include <QDebug>

namespace {
    constexpr int k_maxRetries = 3;
}

MyClass::MyClass(QObject *parent) : QObject(parent) {}

MyClass::~MyClass() = default;

QString MyClass::name() const { return m_name; }

void MyClass::setName(QString name) {
    if (m_name != name) {
        m_name = name;
        emit nameChanged(m_name);
    }
}
```

---

## QSharedData 写时复制（COW）

```cpp
class MyData {
public:
    MyData() : m_data(new Data) {}
    QString name() const { return m_data->name; }
    void setName(QString name) { m_data->name = name; }
private:
    struct Data : QSharedData { QString name; };
    QSharedDataPointer<Data> m_data;
};
```

---

## Content 结构体隐藏实现

成员变量 >5 个时，用 Content 结构体藏到 .cpp：

```cpp
// xxx.h
class MyClass : public QObject {
    Q_OBJECT
public:
    MyClass(QObject *parent = nullptr);
    ~MyClass() override;
private:
    struct Content;
    QScopedPointer<Content> m_content;
};

// xxx.cpp
struct MyClass::Content {
    QString name;
    QNetworkReply *reply = nullptr;
};

MyClass::MyClass(QObject *p) : QObject(p), m_content(new Content) {}
MyClass::~MyClass() = default;
```

---

## 单例模式

```cpp
// xxx.h
class MyClass : public QObject {
    Q_OBJECT
public:
    static MyClass *instance();
private:
    static MyClass *createInstance();
    MyClass();
};

// xxx.cpp
MyClass *MyClass::instance() {
    using Ptr = QScopedPointer<MyClass, QScopedPointerDeleteLater>;
    static Ptr s_instance(createInstance());
    return s_instance.data();
}

MyClass *MyClass::createInstance() {
    auto inst = new MyClass();
    auto mainThread = QCoreApplication::instance()->thread();
    if (mainThread != inst->thread()) {
        inst->moveToThread(mainThread);
    }
    return inst;
}
```

---

## 线程设计原则

兄弟对象（非调用者创建的）在同一线程，直接调用。子对象（调用者创建的）可跨线程，通信用 `QMetaObject::invokeMethod`：

```cpp
// Worker 不感知线程
class Worker : public QObject {
    Q_OBJECT
public:
    explicit Worker(QObject *host);
public slots:
    void process(QByteArray data);
signals:
    void finished();
private:
    QObject *m_host = nullptr;
};

// 使用
auto thread = new QThread(this);
auto worker = new Worker(this);
worker->moveToThread(thread);
thread->start();

QMetaObject::invokeMethod(worker, [worker] { worker->process(data); });

// 停止
thread->quit(); thread->wait(3000); worker->deleteLater();
```

---

## QML 类型注册

```cpp
class MyClass : public QObject {
    Q_OBJECT
    QML_ELEMENT
    // QML_NAMED_ELEMENT("CustomName")
    // QML_SINGLETON
};
```

配合 `CMakeLists.txt` 中的 `qt_add_qml_module()`。

---

## std::move 使用原则

只在需要**明确转移所有权**时使用（如传入 `std::unique_ptr`、存入容器后不再使用原变量）。编译器 RVO/NRVO 已能处理绝大多数场景：

```cpp
// ✅ 让编译器自己处理
Widget createWidget() {
    Widget w;
    return w;  // NRVO 自动优化
}

// ✅ 明确转移所有权
container.push_back(std::move(w));

// ❌ 阻止 NRVO
Widget createWidget() {
    Widget w;
    return std::move(w);  // 强制走移动构造
}
```
