---
applyTo: "**/CMakeLists.txt,**/*.cmake"
description: CMake 编码规范 — 现代 CMake、target-based、Qt 适配
---

# CMake 编码规范

## 核心原则

- **Target-based**：一切围绕 target 组织，不用目录级命令
- **PRIVATE/PUBLIC/INTERFACE** 必写：明确依赖传递范围
- **现代 CMake**：最低 3.16，推荐 3.24+
- **cmake_minimum_required 同时设 max**：`VERSION 3.16...4.4`
- **qt_ 系列命令**：Qt 项目用 `qt_add_executable`/`qt_add_library`/`qt_add_qml_module`
- **每个子目录声明自己的 target**：父目录不替子目录设源文件

## 常见陷阱

- `add_executable` 代替 `qt_add_executable` → Qt 项目必须用 `qt_add_executable`
- `qt5_*` 宏在 Qt 6 → 用版本无关的 `qt_*` 命令
- 缺少 `qt_standard_project_setup(REQUIRES 6.x)` → 自动启用 AUTOMOC/AUTOUIC 和策略
- 手写 `.qrc` 装 QML → 用 `qt_add_qml_module` + `QML_FILES`
- 目录级命令 → 用 `target_*` 版本：`target_include_directories` / `target_link_libraries`
- `file(GLOB)` 收集源文件 → 显式列出，新增/删除文件时 CMake 不感知
- `link_libraries` / `include_directories` → 它们对全体 target 生效，用 `target_*` 精确控制
- 忘记 `PUBLIC` / `PRIVATE` / `INTERFACE` → `target_link_libraries` 必须指定
- `add_definitions` / `CMAKE_CXX_FLAGS` → 用 `target_compile_definitions` / `target_compile_options`

> 📖 详见 [references/cmake-pitfalls.md](references/cmake-pitfalls.md)

## 项目结构模板

```cmake
cmake_minimum_required(VERSION 3.16...4.4)

project(MyApp VERSION 1.0.0 LANGUAGES CXX)

# Qt 项目必须在 find_package 之后立即调用
find_package(Qt6 6.5 REQUIRED COMPONENTS Core Quick Widgets)
qt_standard_project_setup(REQUIRES 6.5)

qt_add_executable(myapp main.cpp)

target_link_libraries(myapp
    PRIVATE
        Qt6::Core
        Qt6::Quick
        Qt6::Widgets
)
```

### 子目录模式

```cmake
# 顶层 CMakeLists.txt
add_subdirectory(src/core)
add_subdirectory(src/app)

# src/core/CMakeLists.txt — 只声明自己的 target
qt_add_library(myapp_core STATIC
    notebook.cpp notebook.h
)

target_include_directories(myapp_core PUBLIC include)
target_link_libraries(myapp_core PUBLIC Qt6::Core PRIVATE Qt6::Sql)
```

## Target 可见性规则

| 关键字 | 含义 | 何时用 |
|--------|------|--------|
| `PRIVATE` | 仅当前 target 使用 | .cpp 中用到，.h 未暴露 |
| `PUBLIC` | 当前 target + 所有依赖者 | 公开头文件中暴露了类型 |
| `INTERFACE` | 仅依赖者使用 | header-only 库 |

```cmake
target_link_libraries(myapp
    PRIVATE Qt6::Sql          # .cpp 内部用，外界不需要知道
    PUBLIC  Qt6::Widgets       # 公开头文件中有 QWidget* 参数
)
```

## 命名约定

| 分类 | 风格 | 示例 |
|------|------|------|
| target 名 | snake_case | `myapp`, `myapp_core`, `csv_plugin` |
| 变量（项目内） | snake_case | `myapp_version`, `enable_tests` |
| 缓存变量/option | UPPER_SNAKE | `MYAPP_ENABLE_TESTS` |
| 函数/宏 | snake_case | `add_myapp_test` |

- target 别名用 `Namespace::target`：`MyApp::core`、`MyApp::widgets`

## 文件命名

| 文件 | 命名 | 示例 |
|------|------|------|
| 构建脚本 | `CMakeLists.txt`（固定名） | 各级目录同名 |
| 查找模块 | `Find<库名>.cmake` | `FindZlib.cmake` |
| 工具模块 | snake_case `.cmake` | `add_myapp_test.cmake` |

- `CMakeLists.txt` 是保留名，各级目录都用它，不自定义
- `.cmake` 模块集中放 `cmake/` 目录，用 `include()` 加载
- 工具模块名与其中函数/宏同名（snake_case）

## Qt 专用规则

- 必须用 `qt_*` 命令：`qt_add_executable` / `qt_add_library` / `qt_add_qml_module`
- QML 文件放 `qt_add_qml_module`，不手写 `.qrc`
- 资源用 `qt_add_resources`，不用手写 `.qrc` 文件
- C++ 暴露给 QML 的类加 `QML_ELEMENT` 宏，自动注册
- 源文件显式列出，不用 `file(GLOB)`

```cmake
qt_add_qml_module(myapp
    URI MyApp
    QML_FILES Main.qml AboutDialog.qml
    SOURCES backend.cpp backend.h
)
```

## 通用规则

- `option()` 用于可配置开关，不用 `set()` 硬编码
- 输出目录统一：`set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)`
- 不要手动设 `CMAKE_CXX_FLAGS`，用 `target_compile_options` / `target_compile_features`
- C++ 标准用 `target_compile_features` 或 `CMAKE_CXX_STANDARD`，不手写 `-std=c++17`
- 路径用 `CMAKE_CURRENT_SOURCE_DIR` / `CMAKE_CURRENT_BINARY_DIR`，不硬编码

## 生成器表达式

条件逻辑用生成器表达式，不写 if/else 分支：

```cmake
target_compile_definitions(myapp PRIVATE
    $<$<CONFIG:Debug>:DEBUG_MODE>
    $<$<PLATFORM_ID:Windows>:PLATFORM_WINDOWS>
)
```

> 不要在 `if()` 中根据 `CMAKE_BUILD_TYPE` 分支设置 target 属性——多配置生成器（Xcode/VS）下会出错。

> 📖 完整模式见 [references/cmake-patterns.md](references/cmake-patterns.md)
