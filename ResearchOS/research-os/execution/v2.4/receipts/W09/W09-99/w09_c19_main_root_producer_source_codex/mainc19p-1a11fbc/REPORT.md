# W09 C19 Main-root producer Source

本包实现新的两阶段 caller。固定 cwd/source_root 为 Main；prepare 仅创建专属 receipt、profile、TEMP 和 GOCACHE，run 依次调用一次 owned go list -export 和一次 owned Python producer。producer 保留原六份审查 Source 与两项 Go 父测试，产生固定新 run 的五项 C19 assertion，Source21、owned/raw 绝对路径均必须属于 Main。本轮没有执行这些实际阶段。

launcher 只给加载的 retrieval runner 注入局部 UUID 对象，恰好允许一次 uuid4，既不改 stdlib uuid 全局状态，也不修改 Main 文件。launcher、permit/started/closed、环境、argv 和 run/output 绑定都是后续 mode 独审的强制输入。不能借用旧候选 packet 或旧 mode review。

实际 prepare 的前置条件为：Main 七目标实际 adoption 及非作者实际独审、当前21项源码与commands精确匹配、本包新的独立 Source 接受、Root 新 scope、CP>367/OW>171 的 owner/worker 登记和四文档 vector。scope 不包含 vector 引用；登记后 request 绑定二者，避免循环 hash。prepare/run 必须使用同一 request/vector。

固定 toolchain；351包 roster 和3905稳定 compiler refs 只从旧 metadata 建立有限清单，不把历史 Native 结果当作新结果。19项 Module GoMod、稳定 Main/GOROOT/module Source 在 go list 前持锁；实际新生成 export/cache/compiler 输入在 Go test 前持锁。使用全新私有 GOCACHE，禁网络模块下载。超时为 list240 / producer420 / innerGo180。

任一步失败停止，不自动重跑。每个 Job 保留原始 stdout/stderr 和原始结果对象；FILETIME 同时保留 Python 整数与十进制字符串，未观察到的各子进程数值退出码为 null。ordinary failure 尽力逐个关闭所有 guard，只在 Job 已确认 idle 后保存部分 packet；进程丢失保留 intent 和现有证据供 Root 明确核对。prepare-ready 和 producer-closed 只在必要 guard/Job/archive 完整闭合后发布。

最终107项新纯 Source 控制通过，4000项既有输入 pin 不变，准备、初轮控制、最终控制、封存四次 Source guard 均 closed、retained=0。内存 fake helper 的 nonzero/timeout/unknown/unclosed 行是控制输入，不是真实 Native 执行。初轮104控制为此前未封存版本结果，未与最终107累加。完整字节逆操作及未封存绑定修订全文均保留。

本任务未读/持锁 Root 七目标与 Canon，未写 Main/Canon，未执行 Git/Go/SQL/API/model/dispatcher/worktree/实际 producer。Source21 的当前 Main 资格由未来实际 gate 验证。一次只读工具错误已独立保存完整原始 pair：ordinal952，outer1，Python/Go/Native/Model均null；当前Root下一序号953。后续正确Source调用0没有覆盖原失败。

状态为 SOURCE_READY_PENDING_INDEPENDENT_REVIEW。本包不授权执行，不接受 formal C19，不改变 W09 parent；formal_case_accepted_delta=0。后续依次需要本包独立 Source 审查、Root新登记与actual授权、实际Main producer及模式独审、两条真实router/dispatcher消费与正式资格审查。
