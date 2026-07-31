---
applyTo: "**/*.qml"
description: QML 编码规范 — import 顺序、组件声明顺序、命名约定、最佳实践
---

# QML 编码规范

## 核心原则

- 可读性优先于微优化
- `id: root` 必须是组件块内第一个属性
- 声明顺序：id → enum → required → 附加属性 → 公开属性 → 信号 → 函数 → 私有 → 信号处理器 → 生命周期 → 内嵌结构 → 子控件 → 状态/转换
- 公开接口在上，内部实现在下，视觉在最后
- 组件 PascalCase，私有文件 `_` 前缀
- 具体类型代替 `var`，`readonly` 表示派生值
- `const`/`let` 代替 `var`，`===` 代替 `==`
- 声明式绑定优先，不隐式引用 `id`
- 内嵌结构（contentItem/delegate 等）用内联对象定义，不引用外部 id
- 私有成员 `_` 前缀；单文件 ≤300 行，复杂即分离
- 重业务逻辑用 C++ 单例（数据处理/网络/文件 I/O）；禁止创建 `.js` 文件，UI 辅助函数内联即可

## 常见陷阱

- `parent` 在 delegate 中不是 ListView → 用 `ListView.view` 或显式 id
- 命令式 `=` 破坏绑定 → 需要恢复用 `Qt.binding()`
- `Timer` 不自动启动 → 显设 `running: true` 或 `.start()`
- `Connections` 一对一 → 多个信号源需多个 `Connections` 块
- Z 轴 = 声明顺序 → 先声明在下，仅必要时用 `z`
- 动态作用域脆弱 → 始终用 `root.xxx` 显式引用
- `Component.onCompleted` 在 delegate 复用时不触发 → 用 `ListView.onReused`
- 属性别名链不可靠 → 别名只有一级

> 📖 详见 [references/qml-pitfalls.md](references/qml-pitfalls.md)

## 导入规范

文件最顶部，按序排列：
1. Qt 内置模块（字母序）
2. 项目自有模块（字母序）
3. JavaScript 文件

```qml
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
```

- **不加版本号**：`import QtQuick` 而非 `import QtQuick 2.15`
- **控件定制须导入风格**：用 `QtQuick.Controls.Basic` 而非裸 `import QtQuick.Controls`

## 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 公开组件 | PascalCase | `MyButton.qml` |
| 私有组件 | `_` + PascalCase | `_MyContent.qml` |

## 声明顺序

```
id → enum → required → 附加属性 → 公开属性 → 信号 → 公开函数
  → 私有属性 → 私有函数 → 信号处理器 → 生命周期
  → 内嵌组件结构 → 子控件 → 状态/转换 → 其他对象
```

> 📖 视觉总览图见 [references/qml-pitfalls.md](references/qml-pitfalls.md)

## 属性

- **`readonly` 表示派生值**：`readonly property bool isValid: value > 0`
- **具体类型代替 `var`**：`property color c` / `property int size`
- **颜色用 `Qt.color()`**：`color: Qt.color("#ffcc00")` 而非裸字符串
- **日期用 `Date` 对象**：`property date d: new Date(2026, 6, 29)`
- **别名只有一级**：`property alias text: label.text`
- **属性分组**：`font { pixelSize: 14; bold: true }`
- **绑定不写重逻辑**：复杂计算放函数

## 函数

```qml
function calculate() {
    const MAX = 3;          // const — 常量
    let count = items.len;  // let — 块级作用域
    if (value === 0) {}     // === — 严格比较
}
```

- `const`/`let` 不用 `var`；`===`/`!==` 不用 `==`/`!=`
- 函数超过 30 行考虑提取；业务逻辑优先 C++ 单例，UI 辅助可留 QML

## 绑定

- **不破坏绑定**：`Component.onCompleted: width = 100` 会移除声明式绑定
- **显式 id 引用**：`color: root.enabled ? "black" : "gray"` 而非 `color: enabled ? ...`
- **条件绑定用 `Binding`**：`Binding { target: r; property: "color"; value: ...; when: cond }`
- **避免绑定循环**：至少一个值是独立计算的

## 信号与连接

```qml
Connections {
    target: someObject           // 必须显式指定
    function onValueChanged(v) {} // function 语法，不用 onFoo:
}
```

## 组件结构

- **内嵌结构内联**：`contentItem: Item { ... }` 不引用外部 id
- **单文件 ≤300 行**：超过则提取独立文件
- contentItem 不用 `anchors.fill: parent`，尺寸由 Control 管理

## 性能

- **Layout > anchors**：`RowLayout`/`ColumnLayout` 自动管理间距和伸缩
- **ListView 设 `cacheBuffer`**：`cacheBuffer: 200`
- **惰性加载用 `Loader`**：`active: visible`
- **delegate 复用**：`reuseItems: true` 时初始化逻辑放 `onReused`

> 📖 完整示例见 [references/qml-patterns.md](references/qml-patterns.md)

