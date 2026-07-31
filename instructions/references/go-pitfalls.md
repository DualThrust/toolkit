# Go 常见陷阱详细展开

> 从 `go.instructions.md` 中移出的陷阱详细说明，每条一行的版本在指令文件中。

---

## 循环变量捕获（range 闭包）

**问题**：Go 1.21 及更早版本中，range 循环变量是复用的，闭包捕获的是同一个变量。

```go
// ❌ 所有 goroutine 都看到最后一个 v
for _, v := range items {
    go func() { fmt.Println(v) }()
}

// ✅ Go 1.22+（或显式复制）
for _, v := range items {
    v := v
    go func() { fmt.Println(v) }()
}

// ✅ 推荐：显式传参
for _, v := range items {
    go func(v string) { fmt.Println(v) }(v)
}
```

---

## goroutine 泄漏

**问题**：goroutine 阻塞在 channel 上永远等不到值。

```go
// ❌ 若 ch 永不关闭，goroutine 泄漏
go func() { data := <-ch }()

// ✅ 始终能退出：select + context / 关闭信号
go func() {
    select {
    case data := <-ch:
        use(data)
    case <-ctx.Done():
        return
    }
}()
```

**规则**：每个 goroutine 必须有明确的退出路径（channel 关闭、context 取消、或 `sync.WaitGroup` 保证）。

---

## 拷贝 sync.Mutex / sync.WaitGroup

**问题**：`sync` 类型拷贝后会复制锁状态，导致死锁或竞态。

```go
// ❌ 结构体按值拷贝时带上锁
type Cache struct {
    mu sync.Mutex
}

func (c Cache) Get() any { ... }   // 值接收者 → 拷贝锁

// ✅ 指针接收者，锁不拷贝
func (c *Cache) Get() any { ... }
```

**规则**：含 `sync.Mutex`/`sync.WaitGroup`/`sync.Once` 的结构体，方法一律用指针接收者。

---

## 接口包含 nil 指针 ≠ 接口为 nil

**问题**：接口由类型 + 值组成，放入 nil 指针后接口自身不是 nil。

```go
func ReturnsError() error {
    var p *MyErr = nil
    return p   // ❌ 接口非 nil，调用方 if err != nil 永远为真
}

// ✅ 返回 nil 接口
func ReturnsError() error {
    return nil
}
```

**规则**：返回接口前检查具体值；`nil` 检查用反射或提前 `if p == nil { return nil }`。

---

## defer 参数与执行时机

**问题**：defer 的参数在**声明时**求值，不是执行时；且 defer 在函数返回后执行（LIFO）。

```go
func f() {
    start := time.Now()
    defer log.Printf("elapsed %v", time.Since(start))  // ✅ 需要时用闭包

    file, _ := os.Open(name)
    defer file.Close()       // 打开后立即 defer，别在文件中间 defer
}
```

**规则**：
- defer 放资源获取后立即执行，不在使用中途
- 需要取"执行时"的值 → 用闭包 `defer func() { ... }()`
- 循环里 defer 会累积到函数末尾 → 循环体抽成函数

---

## 切片共享底层数组

**问题**：`append` 到共享底层数组的子切片会互相覆盖。

```go
a := []int{1, 2, 3, 4}
b := a[:2]                 // b = [1, 2]，与 a 共享底层
b = append(b, 99)          // ❌ 覆盖了 a[2]，a 变成 [1,2,99,4]

// ✅ 需要独立时显式复制
c := slices.Clone(a[:2])   // Go 1.21+
```

**规则**：子切片要独立修改/追加时，用 `slices.Clone`（Go 1.21+）或 `copy`。

---

## map / slice 并发读写

**问题**：map 并发写会 panic（`fatal error: concurrent map writes`）。

```go
// ✅ 只读并发：sync.RWMutex
var mu sync.RWMutex
mu.RLock()
v := m[key]
mu.RUnlock()

// ✅ 读写都频繁：sync.Map（键稳定、读多写少的场景）
m := &sync.Map{}
m.Store(key, val)
val, ok := m.Load(key)
```

**规则**：map 需要并发访问时，要么加锁，要么用 `sync.Map`，不要裸用。

---

## `:=` 短变量遮蔽

**问题**：`:=` 在内部作用域会**遮蔽**外层同名变量。

```go
x := 1
if v, err := f(); err != nil {
    x := v   // ❌ 新变量遮蔽外层 x
}

// ✅ 显式区分
if v, err := f(); err != nil {
    x = v    // 赋值而非声明
}
```

**规则**：`:=` 只声明新变量；复用外层变量用 `=`；go vet 的 shadow 检查可捕获。

---

## 字符串拼接性能

```go
// ❌ O(n²)，每次拼接都分配
s := ""
for _, p := range parts {
    s += p
}

// ✅ strings.Builder
var b strings.Builder
for _, p := range parts {
    b.WriteString(p)
}
s := b.String()
```

**规则**：循环内拼接字符串用 `strings.Builder`；`strings.Join` 处理切片。

---

## JSON 序列化

```go
type User struct {
    Name  string `json:"name"`
    Email string `json:"email,omitempty"`   // 空值省略
    ID    int64  `json:"id"`
}

// 字段不想导出但参与序列化 → 保持首字母大写 + tag
// 忽略某字段 → json:"-"
```

**规则**：
- 每个字段显式 `json:"..."` tag，不依赖默认（默认用字段名）
- 未导出字段不参与 JSON；需要时用小写 tag + 大写字段名

---

## 整数溢出

```go
// ❌ 加法溢出，结果变负数
total := a + b

// ✅ 检查溢出
if b > math.MaxInt-a {
    return fmt.Errorf("overflow")
}
total := a + b
```

**规则**：涉及外部输入或大数的算术，先做边界检查；时间/字节数尤其注意。

---

## recover 只在 defer 中有效

```go
// ❌ 无效
func f() {
    defer recover()   // recover 返回值丢弃，panic 继续传播
}

// ✅
func f() (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic: %v", r)
        }
    }()
    return g()
}
```

**规则**：`recover` 必须直接（或经一层）在 defer 函数内调用，且要处理返回值。

---

## init() 的陷阱

**问题**：`init()` 在包加载时执行，顺序隐式（依赖导入顺序），难测试、难覆盖。

```go
// ❌ 副作用藏在 init
func init() { config.Load() }

// ✅ 显式初始化，可测试
var cfg = mustLoad()          // 包级变量初始化
// 或
func NewApp() *App {
    return &App{cfg: config.Load()}
}
```

**规则**：用包级变量初始化或显式 `New*`，尽量不用 `init()`。

---

## 全局可变状态

```go
// ❌ 全局 map，测试间相互污染
var cache = map[string]int{}

// ✅ 显式注入
type Service struct{ cache map[string]int }
func NewService() *Service { return &Service{cache: map[string]int{}} }
```

**规则**：状态通过构造函数注入，不用全局变量；全局只放只读配置。

---

## time 与 Duration

```go
// ❌ 把 Duration 当 int 用
timeout := 5000          // 微妙错误：5000 纳秒

// ✅ 显式单位
timeout := 5 * time.Second
```

**规则**：时间一律用 `time.Duration`/`time.Time`；乘单位（`time.Second`）显式表达。
