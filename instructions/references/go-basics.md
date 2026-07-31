# Go 基础语法速查（初学者）

> 从 C++ 迁移时的 Go 语言速查（C++ 对照为重点）。硬性规则见 `go.instructions.md`。

**目录**：C++ 快速对照 · 程序入口 · 变量声明 · 基础类型 · 容器 · 控制流 · 函数 · 结构体与方法 · 接口 · 错误处理 · defer · 指针 · goroutine/channel · 自检清单

---

## C++ → Go 快速对照（重点）

### 关键字与语法

| C++ | Go | 说明 |
|------|------|------|
| `class` / `struct` | `type X struct{}` | 统一为 struct |
| `public` / `private` / `protected` | 首字母大小写 | 导出 = 首字母大写 |
| `virtual` / 继承 | 嵌入字段 + interface | 无 virtual |
| `template` | 泛型 `[T any]` | 1.18+ |
| `const` | `const` | 无 const 引用 |
| `static` | 包级变量 / 函数 | 无 static 成员 |
| `new` / `delete` | `new`（少用）/ GC | 无手动释放 |
| `this` | 接收者 `d` | `func (d *X)` |
| `nullptr` | `nil` | 空值 / 空接口 |
| `auto` | `:=` / 类型推断 | 类似 |
| `decltype` | 无 | 显式写类型 |
| `for` / `while` / `do-while` | `for` | 只有 for |
| `switch` | `switch` | 不穿透 |
| `try` / `catch` / `throw` | error 返回值 | 无异常 |
| `namespace` | package | 包名小写 |
| `#include` | `import` | 无头文件 |
| `typedef` / `using` | `type X = Y` | 别名 |
| `enum class` | `const` + `iota` | 类型化枚举 |
| `operator 重载` | 方法 | `a.Add(b)` |
| `? :` 三元 | 无 | 用 if |
| `->` | `.` | 自动解引用 |
| `::` | `.` | `pkg.Func` |
| `sizeof` | `len()` / `unsafe.Sizeof` | 语义不同 |
| `volatile` | `sync/atomic` | 并发场景 |

### 命名速查

| 对象 | 风格 | 示例 |
|------|------|------|
| 文件名 | snake_case | `http_server.go`, `main.go` |
| 导出标识符 | PascalCase | `DeployConfig` |
| 未导出标识符 | camelCase | `maxRetries` |
| 包名 | 小写单数，无下划线 | `toolkit`, `config` |
| 常量 | 同变量规则（导出才大写） | `DefaultTimeout` |
| 缩写词 | 保持全大写 | `URL`, `ID`, `API` |

- **文件用 snake_case，标识符用驼峰**（正好相反，新手易混）
- 导出与否只看首字母：`CamelCase` 导出，`camelCase` 私有
- 文件名与内部类型名无关（不像 Java 类名 = 文件名）
- 保留后缀别撞名：`xxx_test.go`（测试）、`xxx_windows.go` / `xxx_linux.go`（平台）

### 常用容器

| C++ | Go | 差异 |
|------|------|------|
| `std::vector<T>` | `[]T`（slice） | 日常主力 |
| `std::array<T,N>` | `[N]T` | 定长，极少用 |
| `std::map` | `map[K]V` | 无序，需排序 |
| `std::unordered_map` | `map[K]V` | Go map 即哈希表 |
| `std::set` | `map[T]struct{}` | 无内置 set |
| `std::string` | `string` | 不可变 |
| `std::pair` | 多返回值 / struct | |
| `std::tuple` | 多返回值 / struct | |
| `std::optional` | 零值 + `, ok` | |
| `std::variant` | `any` + 断言 | |
| `std::stack` | slice | |
| `std::queue` | slice / `container/list` | |
| `std::priority_queue` | `container/heap` | |
| `std::bitset` | `math/bits` | |

### 常用类型

| C++ | Go | 说明 |
|------|------|------|
| `int` | `int` | 平台相关 |
| `int64_t` | `int64` | 定宽 |
| `unsigned int` | `uint32` / `uint64` | 显式宽度 |
| `float` | `float32` | 少用 |
| `double` | `float64` | 默认浮点 |
| `char` | `byte` | ASCII 字节 |
| `wchar_t` / Unicode | `rune` | Unicode 码点 |
| `std::string` | `string` | 值类型，不可变 |
| `bool` | `bool` | 相同 |
| `void*` | `any` | 需类型断言 |
| `const char*` | `string` | |
| `size_t` | `int` | `len()` 返回 int |

### 常用类（std → Go 包）

| C++ std | Go | 用途 |
|------|------|------|
| `std::stringstream` | `strings.Builder` | 字符串拼接 |
| `std::ifstream` / `ofstream` | `os.ReadFile` / `os.WriteFile` | 文件读写 |
| `std::chrono` | `time` | 时间 |
| `std::regex` | `regexp` | 正则 |
| `<random>` | `math/rand/v2` | 随机 |
| `std::mutex` | `sync.Mutex` | 互斥 |
| `std::thread` | goroutine | 并发 |
| `std::atomic<T>` | `sync/atomic` | 原子 |
| `std::exception` | `error` | 错误值 |
| `std::filesystem::path` | `path/filepath` | 路径 |
| `std::unique_ptr` / `shared_ptr` | 无（GC 管理） | 不需要 |
| `std::function` / lambda | `func` 类型 / 闭包 | 一等公民 |

### 核心概念

| C++ 习惯 | Go 的做法 | 注意 |
|------|------|------|
| 类 + 继承 | struct + 组合 + interface | 无继承，用嵌入字段 |
| 构造函数 / 析构函数 | `NewXxx()` / 无析构 | 资源释放用 defer |
| 异常 throw/catch | 返回 `(T, error)` | 不抛异常，显式检查 |
| RAII 作用域释放 | `defer` | **函数级**，不是块级 |
| 引用 `T&` / 常量引用 | 值传递 / 指针 `*T` | 参数默认值传递 |
| 函数重载 | 不支持 | 用不同函数名 |
| 默认参数 | 不支持 | 用可变参数 / Options 模式 |
| `const` 成员函数 | 无 | 值接收者近似只读 |
| `condition_variable` | channel | 阻塞 / 唤醒 |
| 异常类型层级 | `errors.Is` / `errors.As` | 错误即值 |

### 标准库核心

| 功能 | C++ | Go |
|------|------|------|
| 打印/格式化 | `std::cout` / `printf` | `fmt.Println` / `fmt.Printf` |
| 字符串处理 | `std::string` | `strings` 包 |
| 字符串↔数字 | `stoi` / `to_string` | `strconv.Atoi` / `strconv.Itoa` |
| 容器 | `vector` / `map` / `set` | slice / map（内置） |
| 算法 | `<algorithm>` | `slices`（1.21+）/ `sort` / `cmp` |
| 时间 | `<chrono>` | `time` |
| 文件系统 | `<filesystem>` | `os` / `path/filepath` |
| 正则 | `std::regex` | `regexp` |
| 随机 | `<random>` | `math/rand/v2` |
| JSON | nlohmann / rapidjson | `encoding/json` |
| 日志 | spdlog | `log` / `slog` |
| HTTP | libcurl | `net/http`（内置） |

### 标准库并发

| 功能 | C++ | Go |
|------|------|------|
| 线程 | `std::thread` | goroutine：`go f()` |
| 互斥 | `std::mutex` | `sync.Mutex` / `sync.RWMutex` |
| 条件变量 | `std::condition_variable` | channel（`<-ch` 阻塞/唤醒） |
| 原子 | `std::atomic` | `sync/atomic` |
| 异步结果 | `std::future` / `promise` | channel / `errgroup.Group` |

### 标准库代码示例

```go
// 格式化（类似 printf / snprintf）
fmt.Printf("name=%s n=%d\n", name, n)
s := fmt.Sprintf("sum=%d", a+b)

// 字符串（类似 std::string 操作）
parts := strings.Split(s, ",")       // 类似 split
joined := strings.Join(parts, ";")   // 类似 join
if strings.HasPrefix(s, "http") { ... }  // 类似前缀检查
var b strings.Builder                 // 类似 stringstream
b.WriteString("a")
b.WriteString("b")

// 数字转换（注意：返回 error！类似 stoi 但必须处理错误）
n, err := strconv.Atoi(s)
if err != nil { /* 转换失败 */ }
s2 := strconv.Itoa(42)

// map 查找（类似 find，ok 表示是否存在）
v, ok := m[key]
if !ok { /* 不存在 */ }

// 排序（类似 std::sort）
slices.Sort(nums)      // 1.21+ 泛型版
sort.Ints(nums)        // 旧版
slices.SortFunc(users, func(a, b User) int {
    return cmp.Compare(a.Age, b.Age)
})

// 时间（类似 sleep_for / steady_clock）
time.Sleep(5 * time.Second)
deadline := time.Now().Add(30 * time.Second)

// 文件（类似 ifstream 读全部 / ofstream 写）
data, err := os.ReadFile("a.txt")
if err != nil { /* 不存在或读失败 */ }
os.WriteFile("b.txt", data, 0o644)

// JSON（类似 nlohmann dump / parse）
type User struct { Name string `json:"name"` }
data, _ := json.Marshal(u)
var u2 User
json.Unmarshal(data, &u2)

// 正则（Must 前缀 = 编译期失败会 panic，适合常量模式）
re := regexp.MustCompile(`^\d+$`)
if re.MatchString(s) { ... }

// 随机（math/rand/v2，Go 1.22+；旧版用 rand.Intn）
n := rand.IntN(100)   // 0~99
```

### C++ 习惯的常见误区

- **没有 `const 引用`**：`func f(s string)` 就够，Go string/slice 传引用头，拷贝便宜
- **不要手动 delete**：GC 管理；`defer file.Close()` 代替析构函数
- **`defer` 是函数级**：不是块级，循环里 defer 会累积到函数末尾
- **结构体默认按值拷贝**：C++ 怕拷贝才用引用；Go 默认拷贝，大结构体才传指针
- **`&` 取地址是安全的**：Go 无悬垂指针，返回局部变量地址没问题
- **没有 `const` 语义**：想表达“只读”用值接收者，语言不强制的
- **map 迭代无序**：需要有序时手动收集 key 再 `sort`
- **`new` 很少用**：C++ 的 `new` 对应 Go 的 `make`（slice/map/channel），不是 `new`

### 关键差异示例

```go
// ① enum class → iota（自动递增，类似无值枚举）
type Color int
const (
    Red Color = iota   // 0
    Green              // 1
    Blue               // 2
)

// ② RAII/析构 → defer（函数级，不是块级！）
func process() error {
    f, err := os.Open("a.txt")
    if err != nil {
        return err
    }
    defer f.Close()     // 函数返回时执行，类似析构
    // ... 使用 f
}

// ③ 继承 → 嵌入字段（组合）
type Base struct{ Name string }
func (b *Base) Hello() string { return "hi " + b.Name }

type User struct {
    Base        // 嵌入，User 自动提升获得 Hello()
    Age int
}

// ④ 运算符重载 → 方法
// C++: v1 + v2   →   Go: v1.Add(v2)
func (a Vec) Add(b Vec) Vec { return Vec{a.X + b.X, a.Y + b.Y} }

// ⑤ lambda → 闭包（Go 自动捕获外层变量，无需 C++ 的 [&] 捕获列表）
add := func(a, b int) int { return a + b }
result := add(1, 2)
```

---

## 程序入口

```go
package main            // 可执行程序包名必须是 main

import "fmt"           // 导入标准库包

func main() {           // 入口函数，无参数无返回值
    fmt.Println("hi")
}
```

- 库代码放非 main 包，用 `package 包名` 声明
- `main` 包下的 `func main` 是唯一入口
- 导入未使用 = 编译错误；先 `go mod init 模块名` 初始化模块才能运行

---

## 变量声明

```go
var name string = "go"      // 完整声明
var n = 42                  // 类型推断
msg := "hi"                 // 函数内简写（最常用）
const maxRetries = 3        // 常量（小写 = 包内私有，不导出）
```

| 写法 | 位置 | 作用 |
|------|------|------|
| `:=` | 仅函数内 | 声明新变量（同时推断类型） |
| `var` | 任意位置 | 声明（包级变量必须用它） |
| `=` | 任意位置 | 给已存在变量赋值 |

- **未使用的变量/导入 = 编译错误** —— 定义即用，多余即删
- 包级变量和常量用 `var`/`const`，不能 `:=`

---

## 基础类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `int`/`int64` | 整型（平台相关/定宽） | `42` |
| `float64` | 浮点 | `3.14` |
| `string` | 字符串（不可变） | `"hi"` |
| `bool` | 布尔 | `true` |
| `error` | 错误值接口 | `errors.New("...")` |
| `byte`/`rune` | 字节 / Unicode 码点 | `'a'`, `'中'` |

- 类型**不隐式转换**：`int64(5)` 显式转
- 拼接数字到字符串：`fmt.Sprintf("%d", n)` 或 `strconv.Itoa(n)`

### fmt 常用动词

| 动词 | 作用 | 示例 |
|------|------|------|
| `%v` | 默认格式 | `fmt.Printf("%v", u)` |
| `%d` | 十进制整数 | `%d` → 42 |
| `%s` | 字符串 | `%s` → "hi" |
| `%q` | 带引号的字符串 | `%q` → `"hi"` |
| `%f` | 浮点（`.2f` 两位小数） | `%.2f` → 3.14 |
| `%T` | 类型名（调试） | `%T` → int |
| `%#v` | Go 源码形式（调试） | `%#v` → 完整结构体 |

---

## 数组 vs 切片（slice）

```go
var arr [3]int           // 数组：定长，值语义，极少用
nums := []int{1, 2, 3}   // 切片：动态长度，日常主力
nums = append(nums, 4)   // 追加（可能重新分配底层）
```

| | 数组 `[3]int` | 切片 `[]int` |
|---|---|---|
| 长度 | 固定 | 动态 |
| 语义 | 值拷贝 | 引用头（共享底层） |
| 传递 | 整体拷贝 | 传引用头，底层共享 |
| 用途 | 几乎不用 | 日常主力 |

- `make([]int, 5, 10)` 建切片（长度 5，容量 10）
- `make(map[string]int)` 建 map；`make(chan int)` 建 channel
- `new(T)` 极少用（返回零值指针）

### map 基础操作

```go
m := make(map[string]int)   // 创建（类似 std::map）
m["a"] = 1                 // 插入/更新
v := m["a"]                // 读取（键不存在返回零值 0）
v, ok := m["a"]            // 读取 + 存在检查（类似 find）
delete(m, "a")             // 删除
len(m)                      // 键值对数
```

- **读取不存在的键返回零值**（不是报错）——需要区分时用 `, ok`
- map 迭代无序；`for k, v := range m`

---

## 控制流

### for（Go 只有 for，没有 while）

```go
for i := 0; i < 10; i++ { ... }   // 经典 C 风格
for x < 10 { ... }                // 当 while 用
for { ... }                       // 无限循环（配合 break）
```

### range（遍历）

```go
for i, v := range nums { ... }        // 切片：下标 + 值
for k, v := range m { ... }           // map：键 + 值
for _, ch := range s { ... }          // 字符串：码点
```

### switch（默认不穿透）

```go
switch n {
case 1:
    // 自动 break，C++ 需显式 fallthrough
case 2, 3:
    // 多个值
default:
}
switch {                 // 当 if-else 链用（无表达式）
case n > 0: ...
case n < 0: ...
}
```

---

## 函数

### 多返回值

```go
func Parse(s string) (int, error) {
    n, err := strconv.Atoi(s)
    return n, err
}
```

- Go 原生支持多返回值，`(T, error)` 是最常见模式
- 命名返回值（`func f() (n int)`）少用，保持简单

### 空白标识符 `_`

```go
count, _ := countWords(s)   // 忽略不需要的返回值
_ = doSomething()           // 显式忽略错误
```

### 值传递 vs 引用

```go
func inc(v int) { v++ }        // 值拷贝，外部不变
func incp(p *int) { *p++ }     // 指针，外部改变
func add(s []int) { ... }      // slice 传引用头，底层共享
```

- 参数默认**值传递**；slice/map/channel 传的是引用头
- 结构体大或需修改 → 传指针 `*T`

---

## 结构体与方法

```go
type User struct {
    Name string
    Age  int
}

u := User{Name: "a", Age: 1}    // 键值初始化
u2 := User{}                     // 零值（字段全为默认值）

func (u User) Hello() string {      // 值接收者
    return "hi " + u.Name
}

func (u *User) Birthday() {         // 指针接收者（可修改）
    u.Age++
}
```

- 方法 = 带接收者的函数，没有类的概念
- 值接收者只读；指针接收者可修改；同一类型两种接收者不混用

---

## 接口 interface

```go
// 定义接口 = 一组方法签名（类似抽象基类）
type Storer interface {
    Save(key string, value []byte) error
}

// 任何类型实现了这些方法，就自动满足接口——无需声明 implements
type FileStore struct{ dir string }

func (f *FileStore) Save(key string, value []byte) error {
    return os.WriteFile(f.dir+"/"+key, value, 0o644)
}

var s Storer = &FileStore{}   // ✅ 编译通过，结构实现方法即满足
```

- 接口是**鸭子类型**：结构只要实现方法就满足接口，不写继承关系
- 空接口 `any` 表示任何类型；取出后要**类型断言**

```go
var v any = "hello"
s, ok := v.(string)   // 安全断言：类型不符时 ok=false，不会 panic
```

- 小接口优于大接口（`io.Reader` 就一个方法）；在消费方定义接口

---

## 错误处理

```go
err := errors.New("timeout")                      // 简单错误
err := fmt.Errorf("connect %s: %w", host, cause)  // 包装 + 保留原因（%w）

if errors.Is(err, context.DeadlineExceeded) { ... }  // 类似按类型 catch
var nf *NotFoundError
if errors.As(err, &nf) { ... }                       // 类似取具体异常对象
```

- 约定：返回 `(T, error)`，`err != nil` 时忽略 T，立即 return
- 错误信息**小写开头、无结尾标点**；判断错误用 `errors.Is/As`，不比较字符串
- 类比 C++：`error` ≈ 异常对象，`errors.Is` ≈ 类型匹配，`errors.As` ≈ 拿到具体实例
- 不确定是否返回错误 → 假设返回并检查

---

## defer（类似 RAII，但粒度是函数）

```go
f, err := os.Open("a.txt")
if err != nil {
    return err
}
defer f.Close()      // 注册到函数返回时执行（类似析构）

defer func() {       // 需要"执行时"的值 → 用闭包
    fmt.Println(time.Since(start))
}()
```

- **参数在 defer 声明时就求值**，不是执行时 → 需要当前值用闭包
- 多个 defer **逆序执行**（LIFO）
- **函数级**：循环内 defer 会累积到函数末尾 → 循环体抽成函数
- 类比 C++ RAII，但作用域是函数而不是块

---

## 指针

```go
p := &u        // 取地址
name := (*p).Name  // 解引用（很少直接写，通常自动）
```

- Go 有 GC，没有悬垂指针；指针不能做算术运算（安全）
- 日常代码 `&`/`*` 大多被语法糖隐藏，不用过度担心

---

## goroutine 与 channel

```go
go worker()                // 启动 goroutine（类似 std::thread，但极轻量）

ch := make(chan int)       // 无缓冲通道：发送/接收互相阻塞等待
go func() { ch <- 42 }()   // 发送（阻塞直到有人接收）
v := <-ch                  // 接收（阻塞直到有人发送）

buffered := make(chan int, 10)  // 带缓冲：能存 10 个，不阻塞发送
close(ch)                       // 发送方关闭；接收方用 v, ok := <-ch
```

- goroutine 极轻量，可开上万个；`go 关键字` 即可启动
- channel 是线程安全的通信管道——"不要通过共享内存通信"
- 类比：`std::thread` → `go f()`；`std::future` → channel；`condition_variable` → channel

---

## 入门自检清单

- [ ] 知道 `:=` 和 `=` 的区别，包级变量用 `var`
- [ ] 知道未使用的变量/导入会编译报错
- [ ] 日常用 slice（`[]T`）不用数组
- [ ] 用 `make` 建 map/channel，不用 `new`
- [ ] 会写 `(T, error)` 模式并检查 err
- [ ] 会用 `for range` 遍历切片/map
- [ ] 知道 switch 不穿透
- [ ] 会定义 struct 和带接收者的方法
- [ ] 不手动 delete，用 `defer` 释放资源
- [ ] 知道 map 查找用 `v, ok := m[k]`（对应 C++ `find`）
- [ ] 知道 `defer` 是函数级，不在循环里累积
- [ ] 会用 `strings.Builder` 代替 `stringstream`
- [ ] 知道嵌入字段代替继承
- [ ] 知道 `iota` 代替 `enum class`
- [ ] 知道接口是鸭子类型（无需 implements）
- [ ] 会用 `errors.Is/As` 判断错误
- [ ] 知道 `defer` 参数在声明时求值
- [ ] 会用 `go f()` 和 channel 通信
- [ ] 会用 `v, ok := m[k]` 区分"键不存在"
- [ ] 会用 `fmt` 动词（`%v`/`%d`/`%s`）
