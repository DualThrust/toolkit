# CMake 模式与参考示例

> 本文从 `cmake.instructions.md` 中移出的完整模板和参考用法。

---

## 完整项目模板

```cmake
cmake_minimum_required(VERSION 3.16...4.4)

project(MyApp VERSION 1.0.0 LANGUAGES CXX)

# ---- Qt 设置 ----
find_package(Qt6 6.5 REQUIRED COMPONENTS Core Quick Widgets)
qt_standard_project_setup(REQUIRES 6.5)

# ---- 选项 ----
option(MYAPP_ENABLE_TESTS "Build tests" ON)

# ---- C++ 标准 ----
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---- 输出目录 ----
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# ---- 主程序 ----
qt_add_executable(myapp
    main.cpp
)

target_link_libraries(myapp
    PRIVATE
        Qt6::Core
        Qt6::Quick
        Qt6::Widgets
)

# ---- 子目录 ----
add_subdirectory(src/core)
add_subdirectory(src/widgets)

# ---- 测试 ----
if(MYAPP_ENABLE_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

---

## 库 target 模板

```cmake
# src/core/CMakeLists.txt
qt_add_library(myapp_core STATIC
    notebook.cpp notebook.h
    notestore.cpp notestore.h
)

target_include_directories(myapp_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include     # 公开头文件
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}              # 内部实现
)

target_link_libraries(myapp_core
    PUBLIC
        Qt6::Core          # 公开头文件中有 QObject* 等
    PRIVATE
        Qt6::Sql            # 仅 .cpp 中使用
)
```

---

## 别名与命名空间

```cmake
# 库定义后添加别名
add_library(myapp_core STATIC ...)
add_library(MyApp::core ALIAS myapp_core)

# 使用者通过别名引用
target_link_libraries(myapp PRIVATE MyApp::core)
```

---

## 生成器表达式示例

```cmake
# 按配置开关
target_compile_definitions(myapp PRIVATE
    $<$<CONFIG:Debug>:DEBUG_MODE>
    $<$<CONFIG:Release>:NDEBUG>
)

# 按平台开关
target_link_libraries(myapp PRIVATE
    $<$<PLATFORM_ID:Windows>:ws2_32>
    $<$<PLATFORM_ID:Linux>:pthread>
)

# 条件链接
target_link_libraries(myapp PRIVATE
    $<$<BOOL:${USE_OPENGL}>:Qt6::OpenGLWidgets>
)
```

---

## CMakePresets.json 示例

```json
{
    "version": 3,
    "configurePresets": [
        {
            "name": "default",
            "binaryDir": "${sourceDir}/build",
            "generator": "Ninja",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Debug",
                "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
            }
        },
        {
            "name": "release",
            "inherits": "default",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Release"
            }
        }
    ]
}
```

---

## 查找包

```cmake
# Qt 6 包查找
find_package(Qt6 6.5 REQUIRED COMPONENTS
    Core
    Quick
    Widgets
    Network
)

# 第三方库 — CONFIG 模式优先
find_package(fmt CONFIG REQUIRED)

# 自定义查找路径
list(APPEND CMAKE_PREFIX_PATH "/path/to/custom/install")
find_package(MyLib REQUIRED)
```

---

## 安装规则

```cmake
include(GNUInstallDirs)

install(TARGETS myapp
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(TARGETS myapp_core
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/MyApp
)
```
