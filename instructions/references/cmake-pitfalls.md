# CMake 常见陷阱详解

> 本文是 `cmake.instructions.md` 中"常见陷阱"的详细展开。

---

## `add_executable` 代替 `qt_add_executable`

Qt 项目必须用 `qt_add_executable`，它会自动链接 `Qt::Core`、处理 target finalization，并在 Android 上创建 `MODULE` 库。

```cmake
# ❌
add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Qt6::Core)

# ✅
qt_add_executable(myapp main.cpp)
```

---

## `qt5_*` 宏在 Qt 6

Qt 6 用版本无关命令。`qt5_*` 宏使用旧的变量列表 API，不兼容 target-based 方式。

```cmake
# ❌
qt5_add_resources(myapp_RESOURCES resources.qrc)

# ✅
qt_add_resources(myapp "myapp_data" PREFIX "/" FILES ...)
```

---

## 缺少 `qt_standard_project_setup()`

这个命令启用 AUTOMOC/AUTOUIC、配置 Windows 运行时输出和 RPATH，并用 `REQUIRES` 启用现代 Qt CMake 策略。

```cmake
# ❌ 手动设置
find_package(Qt6 6.8 REQUIRED COMPONENTS Quick)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)

# ✅
find_package(Qt6 6.8 REQUIRED COMPONENTS Quick)
qt_standard_project_setup(REQUIRES 6.8)
```

---

## 手写 `.qrc` 装 QML

QML 文件应该通过 `qt_add_qml_module` 管理，它会自动处理编译和注册。

```cmake
# ❌
qt_add_resources(myapp "qml" PREFIX "/" FILES Main.qml AboutDialog.qml)

# ✅
qt_add_qml_module(myapp
    URI MyApp
    QML_FILES Main.qml AboutDialog.qml
)
```

---

## 目录级命令

`include_directories` 和 `link_libraries` 对全体 target 生效，难以追踪。始终用 `target_*` 版本：

```cmake
# ❌ 目录级 — 影响所有 target
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
link_libraries(Qt6::Core)

# ✅ target 级 — 精确控制
target_include_directories(myapp PRIVATE include)
target_link_libraries(myapp PRIVATE Qt6::Core)
```

---

## `file(GLOB)` 收集源文件

`file(GLOB)` 在新增/删除文件时 CMake 不自动重新运行，导致构建不一致。

```cmake
# ❌
file(GLOB SOURCES *.cpp *.h)
add_executable(myapp ${SOURCES})

# ✅ 显式列出
add_executable(myapp
    main.cpp
    widget.cpp widget.h
)
```

---

## 忘记 PRIVATE/PUBLIC/INTERFACE

`target_link_libraries` 必须指定可见性关键字，否则行为不确定。

```cmake
# ❌ 缺少关键字
target_link_libraries(myapp Qt6::Core)

# ✅
target_link_libraries(myapp PRIVATE Qt6::Core)
```

---

## 全局标志代替 target 属性

`add_definitions` 和 `CMAKE_CXX_FLAGS` 影响所有 target，破坏隔离性。

```cmake
# ❌ 全局污染
add_definitions(-DDEBUG_MODE)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# ✅ target 级别
target_compile_definitions(myapp PRIVATE DEBUG_MODE)
target_compile_options(myapp PRIVATE -Wall)
```
