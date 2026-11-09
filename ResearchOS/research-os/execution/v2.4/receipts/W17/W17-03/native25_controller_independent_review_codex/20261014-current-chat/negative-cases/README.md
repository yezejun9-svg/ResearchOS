# Native25 八个负例的只读独立审查入口

`review_negative.py` 只处理已列入 `../negative-review-preparation/expected-cases.json` 的八个负例。所有真实 case 必须由 Root 提供确切配置与快照 SHA256 后逐次调用。本入口不调用 `serve`、`poll`、`snapshot`、`sign_reviewed`、`publish_signed`、`release_fixture` 或 `stop`，不创建 Root 批准，不读取 `fixture.key`、DPAPI 或 runtime issuer 私有资源。

Python：`C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe -B -X utf8`。

公共参数：

```text
review_negative.py --stage STAGE --config CONFIG --config-sha256 SHA256 --snapshot SNAPSHOT --snapshot-sha256 SHA256 --attempt UNIQUE
```

- `release`：完整配置与 4375 frozen pins、accepted controller/test binary 身份、新 namespace、648 release source pins、原 fixture schema24 全部 typed rows、schema、真实旧24 producer 与新25 rehearsal闭合。`release-pin-mismatch` 只允许第一个 source pin 的指定 synthetic digest，不改变真实源文件。
- `grant`：额外要求 `--baseline-report RELEASE_REPORT`。核验 76 个精确 pin（缺 pin 例为75）、source/target 完整 inventory、options 原始 JSON 字节、binding、时限；wrong-purpose、mismatched identity、missing pin、expired 各例仅放开其指定变更。mismatched identity 必须对应当前 temp 中真实 `other-native-file-*` 的文件身份。已存在的公开签名用 Ed25519 实际校验。
- `terminal`：额外要求 `--baseline-report RELEASE_REPORT`。fresh `mode=ro&immutable=1` 查询原 fixture，whole typed rows/schema 必须等于原 schema24；检查真实 native 非零退出、各例指定 stderr、owned Job 与 private stdin 清理；lease 例检查真实 Win32 code32与持有至闭合，expired 例检查实际进程创建时间晚于grant expiry。必须已有两个签名收据。
- `closure`：`--snapshot` 指向 `controller.closed.json`，额外要求 `--terminal-report TERMINAL_REPORT`。核验实际 outer exit0、`PASS`、4376 guards、held Job closure，以及5个临时公开raw的逐hash归档映射。

`--expected-pins` 默认4375；只有 Root 提供实际新配置合同并单独审查变化后才能显式调整。每次输出到本目录下 `<CaseID>/<stage>-<attempt>/report.json`，同名目录拒绝覆盖。检查失败记录 `REVIEW_FAILED_NOT_ACCEPTED` 和 `traceback.raw.txt`；用新的attempt重试，保留所有原始失败。公共输入在检查期间改变也属于失败，不能转成通过。

本脚本的语法、帮助入口及已知公共artifact字段接口检查，不代表任何新负例已执行或接受。每例最终manifest由独立审查员在具体完成后另行封存。`inner_native_job_id_independently_observed`始终保留false；每例通过均不增加formal接受，不关闭22父任务，也不替代剩余case。
