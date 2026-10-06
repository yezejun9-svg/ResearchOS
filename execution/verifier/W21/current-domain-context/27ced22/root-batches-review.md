# W21 R05 / R08 / R09 独立证据核查

结论：现有定向测试证据通过；R05 的 Go 进程退出码仍未知。没有重跑测试，没有改变正式 case 验收状态。

| 批次 | 实际测试 | 完整断言 | Go 进程退出码 | 原始包结果 |
|---|---:|---:|---|---|
| R05 | 11 | 18 | 未保存；Python wrapper 实际退出 1 | PASS |
| R08 | 9 | 54 | command.json 已保存 0 | PASS |
| R09 | 2 | 19 | command.json 已保存 0 | PASS |

独立按 Package/Test 拼接 Go Output 后解析完整行，逐条比对 report.json 的所有 assertion 对象；验证非空精确 selector、每个 run/pass、无 fail/skip、原始 stdout/stderr 哈希、before/report/current 源清单一致。逐断言原始行号与完整文件哈希见 root-batches-review.json。

R05 的初始解析错误与原始日志均保留，未把 package PASS 当作实际进程退出 0。其限制来自命令回执缺失，不能通过本次只读审查补造。

范围仅限 public synthetic SQLite/HTTP 与真实 Windows 存储。R09 是通用旧夹具数据恢复，不是 current-control 授权。未签发完整 C11–C16、A02/A03、A12、新 native child、provider、私有评测或生产激活验收；源清单也不是已证明的传递依赖闭包。


补充依赖核查：新增 dependency-supplement.json 的 53 个 evaluation/qualification/core `.go`/`.json` 文件，逐项确认当前字节、SHA-256、大小与运行版本 `27ced22` 的 Git blob 一致；原始 raw/report/before 哈希保持不变。此证据明确为 `SUPPLEMENTAL_POST_RUN_GIT_COMPARISON_NOT_ORIGINAL_BEFORE_CAPTURE`。53 项都未出现在原始 before 清单中，因此属于运行后 Git 比对，不能追认运行开始时已捕获这些文件，也不能由此声称完整依赖闭包、扩大 case 验收或消除 R05 退出码未知限制。没有重跑测试。
