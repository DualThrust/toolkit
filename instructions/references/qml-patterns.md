# QML 模式与参考示例

> 本文从 `qml.instructions.md` 中移出的完整代码示例和参考用法。

---

## 内嵌组件结构示例

```qml
// Control 内容区域
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

---

## 状态与转换

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

---

## 动画：Behavior 声明式过渡

```qml
// ✅ 声明式，属性变化时自动触发
Behavior on opacity { NumberAnimation { duration: 200 } }
Behavior on scale { NumberAnimation { duration: 150 } }

// ❌ 手动管理 Animation 对象
NumberAnimation { id: anim; target: root; property: "opacity"; to: 0 }
```

---

## 国际化 (i18n)

所有用户可见字符串必须使用 `qsTrId()`：

```qml
text: qsTrId("button_ok")
title: qsTrId("dialog_title")

// 需要参数的文本用 %1 占位符
text: qsTrId("items_count").arg(count)
```

---

## 日志级别

```qml
console.debug("Current value:", value);   // 调试
console.log("Component initialized");       // 一般信息
console.warn("Value out of range:", val);  // 警告
console.error("Failed to load:", src);     // 错误
```

---

## 文本换行

```qml
Text {
    text: longString
    wrapMode: Text.WordWrap
}
```

---

## Repeater vs ListView

元素少（< 50）且固定时用 `Repeater`，多或动态时用 `ListView`：

```qml
// 少量固定项
Column {
    Repeater {
        model: 3
        delegate: Button { text: "Item " + (index + 1) }
    }
}

// 大量数据 — ListView 回收项
ListView {
    model: largeModel
    delegate: MyDelegate {}
    cacheBuffer: 200
}
```

---

## ListView 性能优化

```qml
ListView {
    cacheBuffer: 200              // 预缓存行数
    delegate: MyDelegate {}
    model: myArrayModel           // plain 模型比 ListModel 快
}
```

---

## Loader 惰性加载

```qml
// ✅ 惰性加载
Loader {
    active: isDetailsVisible
    sourceComponent: DetailsPanel {}
}

// ❌ 总是实例化
DetailsPanel { visible: isDetailsVisible }
```

---

## clip 使用

```qml
// ✅ 子控件确实超出时裁剪
Rectangle {
    clip: true
    radius: 8
    Text { text: "可能超出的文字" }
}

// ❌ 不需要时不要开
Item { clip: true }  // 无背景，裁剪无意义
```

---

## id 命名示例

```qml
id: root              // 根组件统一用 root
id: saveButton        // 描述性名称
id: userNameInput     // 语义化
```

---

## 布局：Layout 优于 anchors

```qml
// ✅ Layout — 自动管理间距和尺寸
RowLayout {
    spacing: 10
    Button { text: "OK"; Layout.fillWidth: true }
    Button { text: "Cancel" }
}

// ❌ 手动 anchors
Row {
    spacing: 10
    Button { text: "OK"; anchors.fill: parent }
    Button { text: "Cancel" }
}
```

---

## 属性分组语法

```qml
// ✅ 分组
font { pixelSize: 14; bold: true }
anchors { left: parent.left; right: parent.right; topMargin: 10 }

// ❌ 分散
font.pixelSize: 14
font.bold: true
```

---

## Binding 条件绑定

```qml
Binding {
    target: rect
    property: "color"
    value: condition ? "red" : "blue"
    when: root.active
}
```
