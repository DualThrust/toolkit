# Go 模式与参考示例

> 从 `go.instructions.md` 中移出的完整模板、项目结构和高级用法，供需要时查阅。

---

## 工具链命令

```bash
go mod init github.com/you/your-tool   # 初始化模块
go mod tidy                            # 整理依赖
go build ./...                         # 构建
go test ./...                          # 测试
go vet ./...                           # 静态检查
go run ./cmd/your-tool                 # 运行
gofmt -l .                             # 检查未格式化文件
```

- 每个模块必须有 `go.mod`，`go.sum` 必须提交到 Git
- 代码提交前跑 `gofmt -w .` + `go vet ./...`
- 建议用 `staticcheck`（`go run honnef.co/go/tools/cmd/staticcheck@latest ./...`）

---

## 标准项目结构

```
project/
├── go.mod
├── cmd/
│   └── app/            # main.go — 每个可执行文件一个目录
│       └── main.go
├── internal/           # 私有包（外部不可导入）
│   └── config/
│       └── config.go
├── pkg/                # 可复用公开包
│   └── toolkit/
└── tests/              # 集成测试
```

- `cmd/` 下 main 保持薄：只做组装，业务逻辑放包内
- `internal/` 放私有实现；`pkg/` 放对外公开库
- 包名 = 目录名（小写单数）

---

## 构造函数模式

```go
type Config struct {
    Timeout time.Duration
    Retries int
}

func NewConfig(timeout time.Duration) *Config {
    return &Config{Timeout: timeout, Retries: 3}   // 默认值集中在此
}
```

- 零值不可用时才需要 `New*`；优先让类型零值可用
- `New` 返回指针；必要时返回 `(*T, error)`

---

## Functional Options 模式

```go
type Option func(*Server)

func WithPort(port int) Option { return func(s *Server) { s.port = port } }

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, port: 8080}
    for _, o := range opts {
        o(s)
    }
    return s
}
```

- 参数多且有可选值时用；避免一堆布尔/空参数
- 保持向后兼容：新增选项不影响已有调用

---

## 错误包装与判断

```go
// 包装：%w 保留原始错误链
return fmt.Errorf("connect %s: %w", addr, err)

// 判断：errors.Is / errors.As
if errors.Is(err, sql.ErrNoRows) { ... }

var netErr *net.OpError
if errors.As(err, &netErr) { ... }
```

- 只有一层时用 `errors.New`；带上下文用 `fmt.Errorf`
- 不要 `fmt.Errorf("...: %s", err)`（丢失错误链）

---

## 并发模式：Worker Pool

```go
func Run(ctx context.Context, jobs <-chan Job, workers int) error {
    g, ctx := errgroup.WithContext(ctx)
    for i := 0; i < workers; i++ {
        g.Go(func() error {
            for {
                select {
                case <-ctx.Done():
                    return ctx.Err()
                case job, ok := <-jobs:
                    if !ok {
                        return nil
                    }
                    if err := job.Process(ctx); err != nil {
                        return err
                    }
                }
            }
        })
    }
    return g.Wait()
}
```

- `errgroup.WithContext` 传播取消与首个错误
- goroutine 必须响应 `ctx.Done()`，否则无法优雅退出

---

## 接口定义位置

```go
// 消费方定义接口（调用方）
type Store interface {
    Save(ctx context.Context, v any) error
}

// 实现方返回具体类型，不声明自己实现
type dbStore struct{ ... }
func NewDBStore(dsn string) *dbStore { ... }
```

- 接口在**使用处**定义，不在实现处
- 实现方返回具体类型，让编译器隐式检查实现

---

## Table-Driven 测试

```go
func TestParse(t *testing.T) {
    tests := []struct {
        name string
        in   string
        want int
        err  bool
    }{
        {"valid", "42", 42, false},
        {"invalid", "abc", 0, true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Parse(tt.in)
            if (err != nil) != tt.err {
                t.Fatalf("err = %v, want %v", err, tt.err)
            }
            if got != tt.want {
                t.Errorf("got %d, want %d", got, tt.want)
            }
        })
    }
}
```

- 表驱动测试是 Go 惯用风格；用 `t.Run` 子测试隔离
- 断言失败用 `t.Errorf`（继续）/ `t.Fatalf`（终止本子测试）

---

## 零值可用性

```go
type Buffer struct {
    mu   sync.Mutex
    data []byte
}

func (b *Buffer) Write(p []byte) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.data = append(b.data, p...)
}
```

- 设计类型时尽量让零值直接可用（`sync.Mutex`、`bytes.Buffer` 模式）
- 零值可用则无需 `New*` 构造
