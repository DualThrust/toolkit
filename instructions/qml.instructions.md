---
applyTo: "**/*.qml"
description: QML 编码规范 — import 顺序、组件声明顺序、命名约定、最佳实践
---

# QML 编码规范

## 核心原则

- **可读性和可调试性优先**：清晰的逻辑比微小的性能差异更有价值。写给人读的代码，顺便给机器跑
- **`id` 最先**：`id: root` 必须是组件块内第一个属性
- **声明顺序**：id → enum → required → 附加属性 → 公开属性 → 信号 → 函数 → 私有属性/函数 → 信号处理器 → 生命周期 → 内嵌结构 → 子控件 → 状态/转换 → 其他对象
- **可见性分组**：按"公开接口 → 内部实现 → 行为 → 视觉"排序，从上到下从抽象到具体
- **命名**：组件 PascalCase，私有文件加 `_` 前缀，`id` 用描述性名称
- **属性**：具体类型代替 `var`，`readonly` 表示派生值，颜色用 `Qt.color()`
- **函数**：`const`/`let` 代替 `var`，`===` 代替 `==`
- **绑定**：声明式优先，不隐式引用 `id`，不写重逻辑
- **安全优先**：内嵌组件结构（`contentItem`、`delegate` 等）必须使用内联对象定义，禁止引用外部已声明的子项
- **私有约定**：私有成员统一使用 `_` 前缀命名
- **复杂即分离**：内嵌结构超过 50 行或单文件超过 300-400 行时，提取为独立文件
- **性能**：Layout 优于 anchors，ListView 设 `cacheBuffer`，惰性加载用 `Loader`

---

## 常见陷阱

以下是 Agent 最容易忽略、但后果严重的 QML 行为细节：

- **`parent` 在 delegate 中不是 ListView**：delegate 内部 `parent` 指向内部容器，而非 ListView。用 `ListView.view` 或显式 `id` 引用列表。
- **命令式 `=` 静默破坏绑定**：`item.width = 100` 会永久移除声明式绑定，不是临时覆盖。需要恢复绑定时用 `Qt.binding()`。
- **`Timer` 不会自动启动**：`Timer.running` 默认 `false`，必须显式设置 `running: true` 或调用 `.start()`。
- **`Connections` 一对一**：一个 `Connections` 块只能连接一个 target。监听多个信号源需要多个 `Connections` 块。
- **Z 轴顺序 = 声明顺序**：后声明的兄弟节点渲染在上层。仅在声明顺序无法满足需求时才用 `z` 属性。
- **动态作用域脆弱**：QML 的裸名称通过作用域链解析，嵌套时行为不可预测。始终用显式 `id` 引用（如 `root.enabled` 而非 `enabled`）。
- **`Component.onCompleted` 在 delegate 复用时不触发**：`ListView.reuseItems: true` 时，初始化逻辑应放在 `ListView.onReused` 中。
- **属性别名链不可靠**：alias → alias 的链式引用在中间组件未完成初始化时值为 `undefined`。保持别名只有一级。

## 导入规范

import 是文件级别的声明，必须放在文件最顶部、组件声明之前。

### 排序规则

1. **Qt 内置模块** — 按字母序
2. **Qt 扩展模块**（若存在）
3. **项目自有模块** — 按字母序
4. **JavaScript 文件** — `import "..." as Xxx` 放最后

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import com.myproject.components

import "utils.js" as Utils
```

### Qt 6 关键规则

- **不加版本号**：Qt 6 已废弃版本号，`import QtQuick 2.15` 会限制 API 表面并阻止 `qmlsc` 编译。始终写 `import QtQuick`。
- **控件定制须导入具体风格**：使用 `contentItem`、`background`、`indicator` 等定制属性时，导入 `QtQuick.Controls.Basic`（或项目约定的其他风格），而非裸 `import QtQuick.Controls`。
- **不需要 `QtQuick.Window`**：Qt 6 中 Window 类型已合并到 `QtQuick` 模块，单独导入是冗余的。

```qml
// ✅ Qt 6 正确
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// ❌ 错误
import QtQuick 2.15              // Qt 6 不加版本号
import QtQuick.Controls          // 定制控件时缺少风格
import QtQuick.Window            // 与 QtQuick 冗余
```

## 文件命名约定

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 公开组件 | PascalCase | `MyButton.qml`, `UserProfile.qml` |
| 私有/内部组件 | `_` 前缀 + PascalCase | `_MyButtonContent.qml`, `_PrivateDialog.qml` |
| 单例 | PascalCase + `Singleton` 后缀（可选） | `Theme.qml`, `Constants.qml` |

## 组件内部元素推荐声明顺序

按**可见性**分组，从公开接口到内部实现，让读者从上到下依次了解"这个组件能做什么"→"它内部怎么运作"。

### 总览

```
组件块开始
│
├─ id                              ← 身份标识
│
├─ 📦 公开接口                     ← 外部使用者关心的
│  ├─ enum
│  ├─ required 属性
│  ├─ 附加属性
│  ├─ 公开属性
│  ├─ 信号
│  └─ 公开函数
│
├─ 🔒 内部实现                     ← 外部不需要知道的
│  ├─ 私有属性
│  └─ 私有函数
│
├─ ⚡ 行为                         ← 响应逻辑
│  ├─ 信号处理器
│  └─ 生命周期
│
├─ 🎨 视觉与状态                   ← 渲染和布局
│  ├─ 内嵌组件结构
│  ├─ 其他子控件
│  ├─ 状态和转换
│  └─ 其他对象
│
组件块结束
```

### 详细顺序

#### 0. `id`

必须是组件块内的**第一个属性**。推荐用 `root`。

```qml
MyButton {
    id: root
}
```

---

### 📦 公开接口 (Public API)

外部使用者通过这里了解"这个组件能干什么"。

#### 1. `enum`（Qt 6）

```qml
enum Status { Active, Inactive, Pending }
enum Size { Small, Medium, Large }
```

#### 2. `required` 属性（Qt 6）

调用方必须传入的属性，按字母序排列。

```qml
required property string userName
required property int userId
required property Model userModel
```

#### 3. 附加属性 (Attached Properties)

布局、可访问性等附加行为。

```qml
anchors.fill: parent
// Layout.fillWidth: true
// Accessible.name: "My Control"
```

#### 4. 公开属性 (Public Properties)

组件公共接口，包括 `property alias`。按字母序排列。

```qml
property bool enabled: true
property int value: 0
property string title: "Default Title"
property alias displayText: textLabel.text
```

#### 5. 信号 (Signals)

参数使用有意义的名称。

```qml
signal clicked()
signal valueChanged(int newValue)
signal errorOccurred(string message, int code)
```

#### 6. 公开函数 (Public Functions)

```qml
function reset() {
    value = 0;
}

function apply() {
    valueChanged(value);
}
```

---

### 🔒 内部实现 (Internal Implementation)

外部不需要关心的内部细节。

#### 7. 私有属性 (Private Properties)

以 `_` 开头的内部状态，通过命名约定避免外部误用。

```qml
property bool _isPressed: false
property real _animationProgress: 0
property var _internalState: ({})
```

#### 8. 私有函数 (Private Functions)

以 `_` 开头的内部方法，封装实现逻辑。

```qml
function _updateVisuals() { /* ... */ }
function _validateInput(input) { return input >= 0; }
```

---

### ⚡ 行为定义 (Behavior)

组件如何响应事件和生命周期。

#### 9. 信号处理器 (Signal Handlers)

`on<SignalName>` 响应逻辑。子组件的信号处理器在子组件内部定义。

```qml
onClicked: {
    clicked();
}

onValueChanged: {
    _updateVisuals();
}
```

#### 10. 生命周期处理器

`Component.onCompleted` 和 `Component.onDestruction`，用于初始化和清理。

```qml
Component.onCompleted: {
    console.log("Component ready");
    _updateVisuals();
}

Component.onDestruction: {
    console.log("Component destroyed");
}
```

---

### 🎨 视觉与状态 (Visual & State)

组件长什么样、如何布局和变化。

#### 11. 内嵌组件结构 (Embedded Component Structures)

属性值本身是一个完整 QML 组件树的场景，包括 `contentItem`、`background`、`delegate`、`header`、`footer`、内联 `ListModel` 等。这些结构往往体量较大，放在后面可以避免打断属性的线性阅读。

**通用规则：**
- ✅ 属性值使用**内联对象定义**（`contentItem: Item { ... }`）
- ❌ 禁止引用外部已声明的子项（如 `contentItem: myItem`）
- 若结构过于复杂，提取为私有 `.qml` 文件（如 `_MyContent.qml`）并通过 `contentItem: _MyContent { control: root }` 引用

**各场景示例：**

```qml
// Control 内容区域 — 不使用 anchors.fill: parent，尺寸由 Control 管理
contentItem: Item {
    width: childrenRect.width
    height: childrenRect.height

    RowLayout {
        anchors.fill: parent
        spacing: 10
        Text { text: root.title }
    }
}

// Control 背景
background: Rectangle {
    color: root.enabled ? "white" : "lightgray"
    border.color: "gray"
}

// 列表代理
delegate: ItemDelegate {
    text: model.display
    icon.source: model.decoration
}

// 内联数据模型
model: ListModel {
    ListElement { name: "Item 1"; color: "red" }
    ListElement { name: "Item 2"; color: "blue" }
}

// 视图头部
header: Label {
    text: "Header"
    font.bold: true
}
```

#### 12. 其他子控件声明

非 `contentItem` 或 `background` 的额外视觉元素，如装饰、浮动层、Overlay 等。

```qml
MouseArea {
    id: overlay
    anchors.fill: parent
    visible: false
}
```

#### 13. 状态 (States) 和 转换 (Transitions)

因其常引用子控件的 `id`，需确保目标已声明。

```qml
states: [
    State {
        name: "pressed"
        when: _isPressed
        PropertyChanges { textLabel.color: "blue" }
    }
]

transitions: [
    Transition {
        from: "*"; to: "pressed"
        ColorAnimation { duration: 100 }
    }
]
```

#### 14. 其他对象声明

`Timer`, `ShaderEffectSource`, `ParticleSystem`, `Animation` 等非直接视觉子项的对象。

```qml
Timer {
    id: autoSaveTimer
    interval: 5000
    repeat: false
    onTriggered: console.log("Auto-saving...")
}
```

## 其他最佳实践

### 属性类

#### 优先使用 `readonly property` 表示派生值

```qml
// ✅ Qt 6 readonly — 语义明确，不可外部修改
readonly property bool isValid: value > 0
readonly property real halfWidth: width / 2

// ❌ 普通 property 表示派生值，外部可能误写
property bool isValid: value > 0
```

#### 类型安全：用具体类型代替 `var`

```qml
// ✅ 尽量用具体类型
property color highlightColor: "#ff0"
property int fontSize: 14

// ❌ var 太宽泛，失去类型自描述
property var highlightColor: "#ff0"    // 是 color 还是 string？
property var fontSize: 14              // 是 int 还是 real？
```

#### 使用 `Qt.color()`、`Qt.rgba()` 等工厂函数创建颜色

直接写颜色字符串 VS Code 会警告类型不匹配。使用 `Qt` 工厂函数类型安全且语义清晰。

```qml
// ✅ Qt 工厂函数 — 类型安全，VS Code 无警告
color: Qt.color("#ffcc00")
color: Qt.rgba(1.0, 0.8, 0.0, 1.0)
color: Qt.darker(baseColor, 1.3)

// ❌ 裸字符串 — VS Code 可能警告类型不匹配
color: "#ffcc00"        // string → color 隐式转换
color: "red"            // 同上
```

#### 日期时间使用 `Date` 对象而非字符串

日期字符串在不同 locale 下行为不一致，使用 `Date` 对象更可控。

```qml
// ✅ Date 对象 — 精确可控
property date startDate: new Date(2026, 6, 29)
property date currentTime: new Date()

// ❌ 日期字符串 — 解析依赖 locale，容易出问题
property string startDate: "2026-07-29"
```

#### 别名引用链不要太深

```qml
// ✅ 一级 alias
property alias text: label.text

// ❌ 链式 alias — 难以追踪
property alias data: innerItem.data
// 内部 innerItem 又 alias 了别的...
```

#### 属性分组语法

同类属性使用分组语法，比逐行 `前缀.属性` 更整洁。

```qml
// ✅ 分组
font { pixelSize: 14; bold: true }
anchors { left: parent.left; right: parent.right; topMargin: 10 }

// ❌ 分散
font.pixelSize: 14
font.bold: true
```

#### 绑定中避免重逻辑

属性绑定在依赖变化时重新求值，绑定中的复杂计算会在每次求值时执行，影响性能。

```qml
// ✅ 简单表达式写在绑定中，复杂逻辑放到函数
readonly property bool isReady: _loaded && _validated
function _calculateDisplay() { /* 复杂计算 */ }

// ❌ 绑定里写重逻辑
readonly property string display: {
    let result = "";
    // 每次依赖变化都执行...
    return result;
}
```

### 函数类

#### `const` / `let` 代替 `var`

JavaScript 的 `var` 存在函数级作用域和变量提升问题。值不变的用 `const`，会变的用 `let`，不再使用 `var`。

```qml
function calculate() {
    // ✅ const — 常量，不会意外修改
    const MAX_RETRIES = 3;
    const BASE_URL = "/api/v1";

    // ✅ let — 块级作用域
    let count = items.length;
    if (count > 0) {
        let first = items[0];    // 仅在此块内有效
    }

    // ❌ var — 函数级作用域，可能意外覆盖
    var count = items.length;
    if (count > 0) {
        var first = items[0];    // 整个函数内都有效
    }
}
```

#### 严格比较 `===` 代替 `==`

JavaScript 的 `==` 会做类型强制转换（type coercion），可能导致隐晦的 bug。QML 中常出现字符串与数字混用（如从 `TextField.text` 取值），尤其需要注意。

```qml
function validate() {
    // ✅ 严格比较 — 类型不同直接返回 false
    if (value === 0) { /* ... */ }
    if (textValue === "0") { /* ... */ }

    // ❌ 宽松比较 — 隐式类型转换，结果可能出乎意料
    if (value == 0) { /* ... */ }        // "0" == 0 → true
    if (value == "") { /* ... */ }       // 0 == "" → true
    if (value == false) { /* ... */ }    // 0 == false → true
}
```

> QML 中 `==` 的常见陷阱：`0 == ""` → `true`, `0 == "0"` → `true`, `"" == false` → `true`。一律使用 `===` 和 `!==` 可避免这些问题。

### 绑定与赋值

#### 属性绑定 vs 命令式赋值

```qml
// ✅ 绑定（声明式，自动更新）
width: parent.width * 0.5

// ❌ 不要无意识破坏绑定
Component.onCompleted: width = 100  // 这行会覆盖上面的绑定！
```

如果确实需要在初始化后修改，使用 `Qt.binding()` 重新建立绑定：

```qml
Component.onCompleted: {
    width = Qt.binding(() => parent.width * 0.3);
}
```

#### 避免隐式 `id` 引用（作用域歧义）

```qml
// ✅ 通过 root 显式引用
color: root.enabled ? "black" : "gray"

// ❌ 隐式引用 — 嵌套时作用域规则不直观
color: enabled ? "black" : "gray"  // 是 root.enabled 还是 parent.enabled？
```

#### `Binding` 用于条件绑定

当需要根据条件切换不同绑定时，用 `Binding` 比命令式赋值更优雅。

```qml
// ✅ Binding 声明式 — 根据条件自动切换
Binding {
    target: rect
    property: "color"
    value: condition ? "red" : "blue"
    when: root.active
}

// ❌ 命令式 — 需要在多处手动管理
if (condition) {
    rect.color = "red";
} else {
    rect.color = "blue";
}
```

#### 避免绑定循环

属性之间相互依赖会导致绑定循环，QML 引擎会检测并报 Warning。

```qml
// ❌ 相互依赖 → 绑定循环
Rectangle {
    width: height * 2       // width 依赖 height
    height: width * 0.5     // height 又依赖 width → 循环！
}

// ✅ 打破循环，至少一个值是独立计算的
Rectangle {
    height: parent.height * 0.5   // height 由父容器决定
    width: height * 2
}
```

### 动画

#### 使用 `Behavior` 声明过渡动画

```qml
// ✅ 声明式，当属性变化时自动触发
Behavior on opacity { NumberAnimation { duration: 200 } }
Behavior on scale { NumberAnimation { duration: 150 } }

// ❌ 手动管理 Animation 对象
NumberAnimation { id: anim; target: root; property: "opacity"; to: 0 }
// 还需要手动启动/停止
```

### 布局

#### 优先使用 Layout 系列组件

`RowLayout`、`ColumnLayout`、`GridLayout` 比手动设置 `anchors` 更简洁、响应式更好。

```qml
// ✅ Layout — 自动管理间距和尺寸
RowLayout {
    spacing: 10
    Button { text: "OK"; Layout.fillWidth: true }
    Button { text: "Cancel" }
}

// ❌ 手动 anchors — 需要逐个设置，伸缩时容易漏
Row {
    spacing: 10
    Button { text: "OK"; anchors.fill: parent }
    Button { text: "Cancel" }
}
```

> 当需要精确控制边距时 `Layout.margins` / `Layout.topMargin` 比 `anchors.margins` 更推荐。

### 日志

#### 按严重级别使用 `console` 方法

QML 提供多个日志级别，合理区分便于快速过滤。

```qml
// ✅ 按场景使用不同级别
console.debug("Current value:", value);        // 调试信息
console.log("Component initialized");            // 一般信息
console.warn("Value out of range:", value);     // 警告
console.error("Failed to load:", source);       // 错误

// ❌ 一律用 console.log，难以区分严重程度
console.log("Error:", errorMessage);
```

### 国际化

#### 所有用户可见字符串必须使用 `qsTrId()`

使用文本 ID 而非直接字符串，便于翻译管理和提取。

```qml
// ✅ qsTrId — 使用翻译 ID
text: qsTrId("button_ok")
title: qsTrId("dialog_title")
placeholderText: qsTrId("search_placeholder")

// ❌ 裸字符串 — 无法国际化
// ❌ qsTr() — 本项目统一使用 qsTrId
```

#### 需要参数的文本使用 `%1` 占位符

```qml
// ✅ 占位符 — 支持翻译时调整语序
text: qsTrId("items_count").arg(count)

// ❌ 字符串拼接 — 翻译时无法调整语序
text: qsTrId("items_prefix") + count + qsTrId("items_suffix")
```

### 文本

#### 超长文本换行

需要显示完整内容时使用 `wrapMode` 自动换行，避免布局溢出。

```qml
// ✅ 自动换行
Text {
    text: longString
    wrapMode: Text.WordWrap
}
```

> 一般场景要求显示完整文本，不推荐截断省略。除非空间严格受限（如列表项摘要），才考虑 `elide` + `maximumLineCount`。

### 列表与重复

#### `Repeater` vs `ListView` 的选择

元素少（< 50）且固定时用 `Repeater`，多或动态时用 `ListView`。

```qml
// ✅ 少量固定项 → Repeater 够用
Column {
    Repeater {
        model: 3
        delegate: Button { text: "Item " + (index + 1) }
    }
}

// ✅ 大量或动态数据 → ListView 回收项
ListView {
    model: largeModel
    delegate: MyDelegate {}
    cacheBuffer: 200
}
```

### 结构与组织

#### `id` 命名规范

```qml
// ✅ 推荐
id: root              // 根组件统一用 root
saveButton            // 描述性名称
userNameInput

// ❌ 不推荐
id: item1             // 无意义
id: rect              // 冗余（类型已知）
```

#### 单文件行数建议

单文件超过 300-400 行应考虑拆分：
- `contentItem` 复杂 → 提取 `_MyContent.qml`
- `delegate` 复杂 → 提取 `MyDelegate.qml`
- 公共函数过多 → 提取 `utils.js`

#### ListView 性能优化

大数据列表使用 `ListView` 时注意性能。

```qml
// ✅ 性能优化
ListView {
    // 可见范围外预缓存的行数，减少滚动时的瞬时卡顿
    cacheBuffer: 200

    // 使用合理的委托，避免在 delegate 中做复杂计算
    delegate: MyDelegate { /* ... */ }

    // 如果不需要动态变异，使用 plain 模型比 ListModel 更快
    model: myArrayModel
}

// ❌ 未优化
ListView {
    delegate: Item {
        // 每次滚动都重新创建复杂内容
    }
}
```

#### `Loader` 惰性加载

不需要立即显示的内容用 `Loader`，减少启动开销。

```qml
// ✅ 惰性加载 — active 为 true 时才实例化
Loader {
    active: isDetailsVisible
    sourceComponent: DetailsPanel { /* ... */ }
}

// ❌ 总是实例化，即使不可见
DetailsPanel { visible: isDetailsVisible }
```

#### 正确使用 `clip`

子控件可能超出父边界时裁剪，但不要滥用（影响渲染性能）。

```qml
// ✅ 子控件确实会超出时裁剪
Rectangle {
    clip: true
    radius: 8
    Text { text: "可能超出的文字" }
}

// ❌ 不需要时不要开，增加渲染开销
Item { clip: true }  // Item 无背景，裁剪无意义
```

### 信号与连接

#### `Connections` 必须显式指定 `target`

默认 target 是 `parent`，类型变化时行为不可预测。

```qml
// ✅ 显式 target
Connections {
    target: rootControl
    function onClicked() { /* ... */ }
}

// ❌ 缺少 target — 默认指向 parent，不可靠
Connections {
    function onClicked() { /* ... */ }
}
```

#### 使用 `function onFoo()` 语法，不用废弃的 `onFoo:`

Qt 5.15 起 `onFoo:` 已废弃。混用两种语法会导致函数式处理器被静默忽略。

```qml
// ✅ 函数式语法
Connections {
    target: someObject
    function onValueChanged(newVal) { /* ... */ }
}

// ❌ 废弃的 onFoo: 语法
Connections {
    target: someObject
    onValueChanged: { /* ... */ }
}
```

