---
applyTo: "**/*.go"
description: Go 编码规范 — gofmt 官方风格、错误处理、并发
---

# Go 编码规范

> 遵循 Go 官方约定（Effective Go / gofmt）。命名由导出与否决定，不用前缀体系。

格式化由 gofmt + goimports 统一管理；静态检查用 `go vet` + `staticcheck`。

## 核心原则

- 格式交给 gofmt/goimports；命名服从语言规则（导出与否），不用 `m_`/`s_`/`k_` 前缀
- 错误用 `error` 值显式处理，不用异常；`panic` 仅限程序不可恢复状态
- 组合优于继承；小接口优于大接口；接受 `interface`，返回具体类型
- 并发优先 goroutine + channel，慎用锁；`go.mod` 必须存在
- 函数短小单一职责；超过 60 行考虑拆分
- 显式优于隐式：返回 `(T, error)`，不用零值/哨兵值当错误
- 不写全局可变状态；依赖显式注入
- 每个 package 一个职责；包名与导入路径末段一致

## 心智模型（与 Qt/C++/Python 的差异）

| 你熟悉的语言 | Go 的做法 |
|------|------|
| 类 + 继承 | struct + 组合 + interface |
| 异常 throw/catch | 函数返回 `error`，调用方检查 |
| 构造函数 | `NewXxx()` 函数，或让零值可用 |
| 头文件 / 声明分离 | 不需要，定义即用 |
| this / self | 显式接收者 `func (d *Downloader)` |
| 重载 | 不支持；用类型断言或泛型（1.18+） |

## 编译强制规则（编译器说了算）

- **未使用的变量/导入 = 编译错误** → 定义即用，多余即删
- `:=` 只声明新变量（限函数内）；`=` 赋值；包级变量用 `var`
- 类型不隐式转换：`int64(5)` 显式转换
- 日常用 slice 不用数组；`make` 建 slice/map/channel，`new` 极少用
- switch 默认不穿透（C++ 需要显式 `fallthrough`）
- 多返回值是原生特性：`(T, error)`

> 基础语法速查见 [references/go-basics.md](references/go-basics.md)

## 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 包 | 小写单数，无下划线 | `toolkit`, `config` |
| 导出标识符 | PascalCase | `DeployConfig` |
| 未导出标识符 | camelCase | `maxRetries` |
| 常量 | 同变量规则（导出才大写） | `DefaultTimeout` |
| 接收者 | 单字母/短名 | `func (d *Downloader)` |
| 缩写词 | 保持全大写 | `URL`, `ID`, `API` |

- **不使用** snake_case、前缀体系 —— 那是 Qt/C++、Python 的专属
- 导出与否只看首字母：`CamelCase` 导出，`camelCase` 私有
- 缩写词保持原样：`httpClient`、`ParseURL`，不拆成下划线
- 命名要描述性，避免 `temp`/`data`/`item`/`tmp`

## 文件与结构

- 一个文件一个职责；单文件超 500 行考虑拆分
- 声明顺序：常量/变量 → 类型 → `New*` 构造 → 方法 → 接口实现
- 错误处理就近：检查错误立即返回，不嵌套 else
- `init()` 尽量不用；构造逻辑放显式 `NewXxx` 函数
- 结构体名词命名；接口用 `er` 结尾动词或行为名（`Reader`, `Storer`）
- 导出标识符必须有文档注释，以标识符名开头（`// DeployConfig 描述...`）

## 错误处理

```go
val, err := Load(path)
if err != nil {
    return fmt.Errorf("load %s: %w", path, err)   // %w 保留错误链
}
```

- 错误信息小写开头、不带结尾标点；加上下文用 `%w`
- `errors.Is`/`errors.As` 判断错误，不比较错误字符串
- 不确定函数是否返回错误 → 假设返回并检查
- 忽略错误必须显式 `_ = f()` 或注释说明原因

## 并发

- goroutine 优先 channel 通信，不用共享变量 + 锁
- 取消/超时用 `context.Context`，作第一个参数传递
- 防 goroutine 泄漏：用 `errgroup.Group`/`sync.WaitGroup` 保证退出
- 通道只由发送方关闭；接收方用 `v, ok := <-ch`
- 单例用 `sync.Once`；互斥锁保护临界区保持最短
- `select` + 默认分支做非阻塞，注意避免忙等

## 接口

- 接口保持小：1-2 个方法（`io.Reader` 模式）
- 在消费方定义接口，不在实现方
- 空接口 `any` 谨慎用，取出后立即类型断言
- 值/指针接收者保持一致：同类型方法不要混用

## 常见陷阱

- 拷贝 `sync.Mutex`/`sync.WaitGroup` → 始终指针传递
- range 闭包捕获循环变量 → Go 1.22 前需 `v := v` 或显式传参
- `defer` 在循环内累积 → 把循环体包成函数，defer 放其内
- 接口含 nil 指针 ≠ nil → 返回接口前检查具体值
- map/slice 并发读写 → `sync.RWMutex` 或 `sync.Map`
- 切片共享底层数组 → 修改前 `slices.Clone`/显式 copy
- 字符串循环拼接 → `strings.Builder`
- JSON 字段 → 显式 `json:"name,omitempty"` tag
- 整数溢出 → 检查边界或使用 `math.MaxInt` 等

> 📖 完整示例见 [references/go-patterns.md](references/go-patterns.md)；陷阱详细展开见 [references/go-pitfalls.md](references/go-pitfalls.md)
