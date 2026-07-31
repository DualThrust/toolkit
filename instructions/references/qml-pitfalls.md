# QML 常见陷阱详解

> 本文是 `qml.instructions.md` 中"常见陷阱"的详细展开，供人类开发者参考。

---

## `parent` 在 delegate 中不是 ListView

delegate 内部 `parent` 指向内部容器，而非 ListView。用 `ListView.view` 或显式 `id` 引用列表。

---

## 命令式 `=` 静默破坏绑定

`item.width = 100` 会永久移除声明式绑定，不是临时覆盖。需要恢复绑定时用 `Qt.binding()`：

```qml
Component.onCompleted: {
    width = Qt.binding(() => parent.width * 0.3);
}
```

---

## `Timer` 不会自动启动

`Timer.running` 默认 `false`，必须显式设置 `running: true` 或调用 `.start()`。

```qml
Timer {
    interval: 1000
    running: true  // 必须显式设置
    onTriggered: console.log("tick")
}
```

---

## `Connections` 一对一

一个 `Connections` 块只能连接一个 target。监听多个信号源需要多个 `Connections` 块。

---

## Z 轴顺序 = 声明顺序

后声明的兄弟节点渲染在上层。仅在声明顺序无法满足需求时才用 `z` 属性。

---

## 动态作用域脆弱

QML 的裸名称通过作用域链解析，嵌套时行为不可预测。始终用显式 `id` 引用：

```qml
// ✅
color: root.enabled ? "black" : "gray"

// ❌
color: enabled ? "black" : "gray"  // 是 root.enabled 还是 parent.enabled？
```

---

## `Component.onCompleted` 在 delegate 复用时不触发

`ListView.reuseItems: true` 时，初始化逻辑应放在 `ListView.onReused` 中。

---

## 属性别名链不可靠

alias → alias 的链式引用在中间组件未完成初始化时值为 `undefined`。保持别名只有一级：

```qml
// ✅ 一级
property alias text: label.text

// ❌ 链式
property alias data: innerItem.data  // innerItem 又 alias 了别的...
```

---

## 组件声明顺序总览（ASCII 图）

```
组件块开始
│
├─ id                              ← 身份标识
│
├─ 📦 公开接口
│  ├─ enum
│  ├─ required 属性
│  ├─ 附加属性
│  ├─ 公开属性
│  ├─ 信号
│  └─ 公开函数
│
├─ 🔒 内部实现
│  ├─ 私有属性
│  └─ 私有函数
│
├─ ⚡ 行为
│  ├─ 信号处理器
│  └─ 生命周期
│
├─ 🎨 视觉与状态
│  ├─ 内嵌组件结构
│  ├─ 其他子控件
│  ├─ 状态和转换
│  └─ 其他对象
│
组件块结束
```
