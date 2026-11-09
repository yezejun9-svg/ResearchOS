# Q2 independent Source review

Verdict: REQUEST CHANGES — SOURCE_COMPONENT_NOT_ACCEPTED.

Q2已移除RUN/PASS文本子串接受，增加官方test2json和严格JSONL状态机；但两个确定的正常路径拒绝缺陷使旧CHILD_JSONL阻断尚未有效关闭。必须新Source namespace最小修订并再次独立审查，不进入该Q2的Root实际10叶执行。本结论只基于源码和已固定工具来源，不宣称执行失败、编译失败或生产失败。

Q2：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9
HDF 9d0e393bedf1e647008cf9022081664ab7511ab6d341edeaa4831482bcd29340 /10797 bytes
MF 65cd84d5c0b440f0c70acbb808c1960102bf03107e10aca1a83f0081f7035ca4 /5997 bytes
helper b2d3b4b35bc47a24f362b615520c0ca3dd194b842ae8fb961f8f0fa63dcd1ec2 /25155 bytes

## Critical Issues

- candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:267（首次调用326，另受影响353）：Digest(raw)与expectedSHA格式不一致，固定Go的正确资源也会被必然拒绝。T5 internal/domain/contracts.go:97定义Digest为"sha256:"+hex；helper74常量和349–351环境约束均为裸64hex。实际固定Go字节的Digest是sha256:d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490，永远不等于d3cc...；所以尚未启动官方reporter即t.Fatal。最小修复：本资源pin链统一使用裸SHA256（例如明确sha256.Sum256+hex.EncodeToString或仅在此helper规范化已知前缀），同步270资源sha256字段与412调用后复查，保持Root固定裸hash合同。不要更改生产Digest或TLS/profile/model需要的领域hash语义。静态反例见checks.json，未运行Go。

## Important Issues

- candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:106–130（事件struct76–83）：decoder缺少固定官方Go1.27.1的OutputType字段，default拒绝正常事件。实际已编译依赖的cmd/internal/test2json/test2json.go:38定义OutputType string，json:",omitempty"。378先发送run，380调用writeFraming；386–391置isFraming，425–428选"frame"，503–508输出Action="output",OutputType="frame"。因此修正hash后，第一个正常测试framing输出也会被拒绝。最小修复：增加严格可选string OutputType，只允许Action=output携带，值按这个已pin版本校验为省略/""、"frame"、"error"、"error-continue"，拒绝null、错类型、未知值及重复键；保持Output与OutputType均不提供run/pass权威。仍须唯一run+terminalpass及fail/skip全拒绝，不通过忽略所有未知字段或接受Output里的PASS文本修复。

## Pinned official JSON schema notes

此处仅针对固定Go1.27.1；官方实现hash81b811cc3af1cc49da5faec1a93aabf12b769a69a5dbc60505c125edb19d288b /19217 bytes，官方main.go hash98613882be8e9dcfed687f594b253b2a0474771981099174406ad74bb377b5c7 /5993 bytes；均属于已独立接受工具编译组件的选中输入。未猜其他Go版本。

| 字段 | 官方实际类型/省略规则 | 实际生成条件 | 本scope最小处理 |
|---|---|---|---|
| OutputType | string，omitempty | Action=output；普通输出空串省略；isFraming为frame；markErrBegin为error；分段错误延续为error-continue（425–508） | 严格支持合法输出元数据；不产生pass权威；其他Action携带拒绝 |
| FailedBuild | string，omitempty | Close里最终Action=fail时赋值（411–418） | 当前scope fail本来拒绝，无需为了成功scope泛化接受 |
| Key / Value | string，omitempty | Action=attr，解析=== ATTR分支（355–358） | 当前scope不接受attr，可继续明确拒绝 |
| Path | string，omitempty | Action=artifacts（353–354） | 当前scope不接受artifacts，可继续明确拒绝 |

Time/Action/Package/Test/Elapsed/Output原有字段的类型和唯一性校验可以保留；-t负责实际Time与Elapsed。上述OutputType支持不能扩大预期case集合或改变业务断言。

## What's Done Well

- 独立复算Q2的4个原测试Source与4396逐字节相同；181原t.Fatal/Error/Skip调用、20原Test名及顺序、196 assertion_or_error if（190严格t断言+6 fmt.Errorf返回块）完整保留。
- helper的typedMuBrokerFixtureProgram到文件尾与4396逐字节相同：正常x509 TLS、公共host.configure、profile、provider/model/credential/ref/revision、qualification与same-owner attach全部继承先前已审结构，Goal mock未改。
- 新JSONL状态机显式限定包、parent和原8native叶，要求首包start、每case唯一run/terminalpass、叶先于父、所有scope先于包pass。未知case/action、fail/skip、重复run/pass、缺事件、包terminal后事件、malformed对象/字段、非UTF8/未完整LF均拒绝；Output文本不授予pass。
- 官方reporter由明确绝对path+Root裸SHA配置，same compiled binary/path与exact argv（-test.run=^parent$、-test.v=test2json、-test.count=1、-test.timeout=180s）可追踪；直接reporter满足官方工具来源要求，无须literal go tool。
- runner实际PID/exit与尚未观察到的physical child/parent exit分开。NULL/PENDING_ROOT_GO_JOB/PENDING_ROOT_RECONCILIATION正确；无需Source伪造未来parent exit。
- 已接受的official-tool编译资源结论仍只为TOOL_COMPILATION_COMPONENT，不被本Source的hash格式错误推翻。

## Verification Story

Tests reviewed: yes，先核对修订helper与保留测试，然后追T5 Digest/Object定义和固定official converter真实字段/生成顺序。独立词法函数重新核对四文件原181/20/196/190；53 refs零漂移；5个成员全部test-only；helper词法括号平衡且新函数无T5同名冲突。
Build verified: no。未运行Go AST/compiler/gofmt/native/SQL/model/provider/private/目标脚本；未发现其他明显静态符号冲突不等于编译通过。
Security checked: static only，原permission/lease/profile/TLS主体保持；Root仍须在后续可接受Source上持有固定reporter/compiled binary guards，实际Job覆盖reporter→compiled child→SDK所有后代，独立核对parent/native exit、terminal JSONL及lease关闭。
Evidence limit: child.stdout.jsonl/raw是官方reporter真实stdout，官方main.go将native child的stdout/stderr合并为Output；此包不将reporter stderr冒称独立捕获了native child stderr。真实执行证据尚未产生。

原4396 REQUEST_CHANGES、Q2封存、814/815错误记录均保留，Root FULL1261 PASS /25 FAIL /4 SKIP FAILED不变。CP356/OW168/SS/CM、6/22历史和0/42当前、GoalActive不变。两项是Source review findings，非新机械执行失败，无新ordinal、不reset。Main/T5/canonical/旧Source均未编辑。

下一步仅新namespace修正两个边界后重新独立Source审查；接受Source后才交Root fresh integration/compile/目标10叶实际执行。STOP。

