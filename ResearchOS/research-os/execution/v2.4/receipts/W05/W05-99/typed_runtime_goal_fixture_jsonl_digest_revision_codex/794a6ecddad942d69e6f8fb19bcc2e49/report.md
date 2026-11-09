# Q3 minimal helper Source revision

结论：仅两个已确认Source阻断的最小修订候选；authority=NONE、formal_acceptance=false，等待Root独立复核及新组合实际执行。
旧Q2 REQUEST_CHANGES与两finding保持历史事实；finding不是机械执行失败，不改/归零任何失败计数。
Q3 Source namespace：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49

1. Digest资源比较只将裸expectedSHA加一次明确sha256:前缀；固定Go裸常量与test2json裸SHA环境约束不变。
保存pin仍是Digest(raw)合法sha256:<64hex>格式，调用后比较也是Digest对Digest，不改生产Digest或TLS/profile领域hash。
依据T5 contracts.go97实际Digest定义，公开Source指纹已绑定base-refs；禁止通过更改固定Root Go hash使比较通过。
2. DecodeEvent增加可选nonnull string OutputType并跟踪字段presence；只允许Action=output和省略/空串/frame/error/error-continue。
非output携带OutputType即使空串也拒绝；null、错类型、未知值、重复字段、未知字段或额外JSONvalue仍拒绝。
Output/OutputType都不提供run/pass权威；FailedBuild/Key/Value/Path及fail/attr/artifacts scope没有泛化接受。

固定官方来源：D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go
官方Source SHA/bytes：81b811cc3af1cc49da5faec1a93aabf12b769a69a5dbc60505c125edb19d288b /19217；selected inventory SHA/bytes：4f7c76bea3116f31806ef15f655e692f7507e34585fc10e9a0be5e9507e77287 /190768（build_inputs748）。
实际Source38是OutputType string/omitempty；run378→framing380/386，writeOutputEvent425–508只发output及上述值；官方writeEvent515–531负责package/time/LF。

四个原测试Source逐字节保持Q2/4396；完整VerifyJSONL状态机、child到TLS/configure/profile/provider/attach文件尾逐字节保持Q2。
181原t.Fatal/Error/Skip调用、20原顶层Test名、196 assertion_or_error_if（190严格t断言+6fmt.Errorf返回块）由字节相同继承，scope仍8native+2Goal原leaf。
Root required resource/env与Q2完全相同：固定Go/GOROOT、explicit官方test2json及裸SHA、Node/Mu bundle/fresh absolute evidence directory。
Root仍须real parent JSONL/exit、test2json→compiled child→SDK所有descendant Go Job、physicalchild PID/exit及lease关闭对账。
child.stdout.jsonl/raw是官方reporter stdout；官方reporter把native stdout/stderr合并为Output，child.stderr.raw仅reporter stderr，不冒称native stderr独立分流。

本轮仅固定Python短script构造/指纹和Go文本/词法分隔符检查；Go AST/compiler/gofmt/native/SQL/model/provider/private/sign/canonical均0。
新机械失败0；全部公开工具IO见tool-io.json，封存运行IO单独列MF排除。没有运行、独立Source接受或formal产品接受结论。
精确diff：runtime_typed_client_fixture_windows_test.patch；完整五文件pins：source-refs.json；官方字段合同：official-outputtype-contract.json。
实际helper修订行：{"57": "func typedRuntimeFixtureWrite(t *testing.T, path string, raw []byte) {", "88": "func typedRuntimeFixtureDecodeEvent(raw []byte) (typedRuntimeFixtureEvent, error) {", "123": "case \"OutputType\":", "153": "if event.OutputType != nil && (event.Action != \"output\" || (*event.OutputType != \"\" && *event.OutputType != \"frame\" && *event.OutputType != \"error\" && *event.OutputType != \"error-continue\")) {", "165": "func typedRuntimeFixtureVerifyJSONL(raw []byte, parent string, expected []string) (Object, error) {", "256": "func typedRuntimeFixturePin(t *testing.T, path, expectedSHA string) Object {", "277": "if expectedSHA != \"\" && Digest(raw) != \"sha256:\"+expectedSHA {", "288": "func typedRuntimeFixtureChild(t *testing.T) bool {"}
作者封存后STOP。由Root独立review→fresh integration→actual，不能把static或resource compilation当10leaf/正式接受。
