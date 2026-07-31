# C++ 常见陷阱详解

> 本文是 `cpp.instructions.md` 中"常见陷阱"的详细展开，供人类开发者参考。

---

## QObject 不可拷贝

忘记 `Q_DISABLE_COPY_MOVE` 不会编译报错，但运行时拷贝 QObject 会导致双重释放或信号槽断裂。所有 QObject 子类必须禁用拷贝/移动：

```cpp
class MyClass : public QObject
{
    Q_OBJECT
    Q_DISABLE_COPY_MOVE(MyClass)
};
```

---

## `Q_ASSERT` 在 Release 中不执行

```cpp
// ❌ Release 下断言被跳过，空指针直接崩
Q_ASSERT(ptr != nullptr);
ptr->doSomething();

// ✅ 用显式 if 判空
if (ptr == nullptr) return;
ptr->doSomething();
```

---

## `qDeleteAll` 只删直接子节点

`qDeleteAll(container)` 不会递归删除孙子节点。子孙 QObject 应设 parent 靠对象树管理。

---

## 隐式共享容器 `operator[]` 触发深拷贝

对 `QHash`/`QMap` 只读操作用 `.value()` 而非 `operator[]`，后者在 key 不存在时会插入默认值并触发 detach。

```cpp
// ✅ 只读
auto val = map.value(key);

// ❌ 触发深拷贝 + 插入默认值
auto val = map[key];
```

---

## 跨线程信号自动排队，但 `Qt::DirectConnection` 不会

worker 线程 emit 信号时用 `Qt::AutoConnection`（默认），Qt 会自动将参数拷贝到接收者线程。手动指定 `Qt::DirectConnection` 会导致接收者槽在 worker 线程执行。

---

## 析构时忘记中断异步操作

`QNetworkReply`/`QTimer` 在析构前必须 `abort()`/`stop()`，否则回调访问已销毁的 `this`。

```cpp
~Downloader() override
{
    if (m_reply) { m_reply->abort(); m_reply->deleteLater(); }
    if (m_timer) { m_timer->stop(); }
}
```

---

## `QString::arg` 链式调用被前值干扰

`.arg(a).arg(b)` 中第一个 arg 的替换值如果包含 `%1`、`%2`，会被后续 `.arg()` 错误替换。

```cpp
// ✅ 多参数重载
auto path = QString("%1/%2").arg(dir, fileName);

// ❌ 链式调用
auto path = QString("%1/%2").arg(dir).arg(fileName);
```

---

## 范围 for 对隐式共享容器用 `auto` 而非 `const auto&`

`for (auto x : list)` 触发不必要的深拷贝。不修改元素时始终用 `const auto&`。

```cpp
// ✅
for (const auto &item : items) { item.process(); }

// ❌ 触发深拷贝
for (auto item : items) { item.process(); }
```

---

## 枚举 switch 写 `default:`

新增枚举值时编译器不会警告，新增值静默走进 `default` 分支。

```cpp
// ✅ 显式列出所有枚举值
switch (status) {
case Idle:     return "空闲";
case Running:  return "运行中";
case Finished: return "已完成";
}

// ❌ 有 default — 新增值静默走错分支
switch (status) {
case Idle:     return "空闲";
default:       return "未知";
}
```

---

## connect lambda 不传 context

`connect(obj, &Obj::sig, [this] { ... })` — 不传 context，对象 `deleteLater()` 后 lambda 仍在事件队列中，访问已销毁的 `this` 直接崩溃。

```cpp
// ❌ 无 context — this 销毁后崩溃
connect(obj, &Obj::sig, [this] { m_data = ...; });

// ✅ 传 this 作 context — sender/receiver 任一销毁自动断开
connect(obj, &Obj::sig, this, [this] { m_data = ...; });
```

> `connect` 的第 3 个参数是 context object，当 sender 或 context 被销毁时连接自动断开。永远不要省略它。

---

## 跨线程直接操作 GUI 对象

Qt 规定 GUI 对象只能在主线程操作。Worker 线程直接调 `widget->setText()` 会崩溃或未定义行为。

```cpp
// ❌ worker 线程中
label->setText("done");

// ✅ 排队到主线程（AutoConnection 默认行为）
QMetaObject::invokeMethod(label, [label] {
    label->setText("done");
});

// ✅ 或通过信号槽（跨线程自动排队）
emit resultReady("done");  // 主线程接收
```

---

## Model 修改不调 beginXxx / endXxx

`QAbstractItemModel` 的数据变更必须用 `beginXxx`/`endXxx` 包裹，View 才能正确刷新。直接修改内部数据会导致 View 不更新或崩溃。

```cpp
// ❌ View 不知道数据变了
m_items.append(item);

// ✅ 通知 View
beginInsertRows(QModelIndex(), m_items.size(), m_items.size());
m_items.append(item);
endInsertRows();
```

常用配对：`beginInsertRows`/`endInsertRows`、`beginRemoveRows`/`endRemoveRows`、`beginResetModel`/`endResetModel`。

---

## 重载信号 connect 编译失败

`QSpinBox::valueChanged` 有两个重载（`int` 和 `QString`），新式语法下编译器不知选哪个。

```cpp
// ❌ 编译错误：ambiguous
connect(spinBox, &QSpinBox::valueChanged, this, &MyClass::onValueChanged);

// ✅ 用 QOverload 消歧
connect(spinBox, QOverload<int>::of(&QSpinBox::valueChanged),
        this, &MyClass::onValueChanged);

// ✅ C++14 更简洁写法
connect(spinBox, qOverload<int>(&QSpinBox::valueChanged),
        this, &MyClass::onValueChanged);
```

---

## Qt 智能指针过时

`QScopedPointer` 不可移动，`QSharedPointer` 复制需要 2× 原子操作，Qt 7 计划移除。用标准库替代：

```cpp
// ❌ Qt 智能指针
QScopedPointer<Data> m_data;
QSharedPointer<Data> m_shared;

// ✅ 标准库
std::unique_ptr<Data> m_data;
std::shared_ptr<Data> m_shared;
```

> 例外：`QScopedPointerDeleteLater` 用于 QObject 单例模式，但普通场景一律用 `std::unique_ptr`。

---

## `qMin`/`qMax`/`qBound` 用标准库替代

Qt 宏的参数顺序与 `std::min`/`std::max` 不同，混用容易出错。统一用标准库：

```cpp
// ❌ Qt 宏
auto m = qMin(a, b);
auto M = qMax(a, b);
auto c = qBound(lo, x, hi);

// ✅ 标准库（注意用括号保护宏展开）
auto m = (std::min)(a, b);
auto M = (std::max)(a, b);
auto c = std::clamp(x, lo, hi);
```

> Windows 的 `windows.h` 会 `#define min`/`#define max`，用 `(std::min)(...)` 括号语法防止宏展开。

---

## `count()`/`length()` 统一用 `size()`

与标准库保持一致，减少 Qt/STL 混用时的认知负担：

```cpp
// ❌ 不统一
auto n = list.count();
auto n = str.length();

// ✅ 统一 size()
auto n = list.size();
auto n = str.size();
```
