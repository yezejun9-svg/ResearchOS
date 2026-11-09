# Q3 independent Source review

Verdict: APPROVE — SOURCE_COMPONENT_ONLY_FOR_ROOT_FRESH_INTEGRATION.

Q2的Digest格式与OutputType两个阻断已在Q3源码层关闭，4396的child JSONL源码缺口也具备有效修复路径。建议Root将此精确Q3五文件组合至全新T6，进行真实编译及原10叶验证。此结论由独立reviewer给出源级判断，Root仍负责采纳与实际执行决定；没有Source作者自接受，没有编译/测试/产品PASS。

Q3：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49
HDF d6ab61e0522ae7f4cae0621e73a648e046ccfe9a4372c2f3848a93f5fc279658 /9879 bytes
MF d6d631ceac02968a7884a278e21358ee6d3c59d55fa158acd5801a10caf81138 /6435 bytes
helper 3a976a38a53ec0e9a4a884c43c52a32e7396bbcab37eef7be1dd47949aab7654 /25741 bytes

## Critical / Important Issues

本次最小修订范围未发现仍然阻断的Source问题。未运行Go类型检查，不能把此判断称为编译通过。

## Closed findings

- Q2-DIGEST-FORMAT：helper277将Root裸expectedSHA显式加一次sha256:前缀后与领域Digest比较；固定Go正确资源的实际hash关系现一致。返回的资源sha256字段仍为领域sha256:<hex>，child调用后复核也使用同一Digest格式。Root裸Go常量与裸reporter hash环境约束未更改，生产Digest及TLS/profile领域hash未改。最小修订采用保留内部prefixed格式这一等价方案，不要求把所有领域hash改成裸值。
- Q2-OFFICIAL-OUTPUTTYPE：helper82为*string，123–126严格解析字符串且保留presence；153–155仅允许Action=output携带并限制为省略/""/frame/error/error-continue。通用decoder仍拒绝null、重复键、错类型、未知字段与trailing JSON；非output即使携带空OutputType也拒绝。固定官方Go1.27.1普通framing所需frame现可通过字段校验，OutputType和Output均不提供run/pass权威。未泛化接受FailedBuild/Key/Value/Path或fail/attr/artifacts。
- 4396-CHILD-JSONL：现走固定官方test2json与same compiled child、精确argv，真实JSONL通过有限状态机判定。源码缺口关闭；child JSONL实际产物、10叶实际通过与Root关闭证据尚未产生，运行验收仍PENDING。

## What's Done Well

独立反向还原helper的四处差分可精确得到Q2原字节；四处为OutputType字段、解码case、action/value约束、Digest比较。整个typedRuntimeFixtureVerifyJSONL函数与整个typedRuntimeFixtureChild到文件尾均与Q2逐字节相同，没有顺带改动控制流或执行范围。

四原测试Source与Q2/4396逐字节相同，重新词法核对T5原181个t.Fatal/Error/Skip调用、20个顶层Test名及顺序、196 assertion_or_error_if（190严格含t断言+6 fmt.Errorf返回块）全部保留。五个Source均为test-only，无production成员。权限、lease、Goal真实创建回执约束、public host.configure、provider/model/同credential ref/revision、profile、正常x509 TLS、same-owner attach结构继承已审代码。

JSONL状态机仍要求唯一包start，精确package、parent与原8native叶各一次run和terminalpass，叶完成后父才能pass，全scope完成后包才能pass；拒绝fail/skip、unknown/out-of-scope、duplicate/missing、malformed、不完整LF、非UTF8及包终态后的事件。不信任Output里的RUN/PASS文本。原2 Goal叶由Root执行与对账，Source不合成接受。

## Verification Story

- Tests reviewed: yes，限定最小diff与先前finding的依赖，54 refs重新指纹零漂移，完整关键函数字节比较及181/20/196/190保留检查通过。helper词法分隔符平衡；新增*string字段和json.Unmarshal使用在现有import范围内，未发现明显静态编译冲突。
- Build verified: no。Go AST/compiler/test/gofmt/native/SQL/provider/model/private/目标脚本均未执行；检查脚本只固定Python读文件、哈希及纯词法函数。
- Security checked: static in scope。caller still requires absolute pinned resources、original scoped exact child args、新鲜独占evidence；test2json实际runner PID/exit与unknown physical child/parent exit保持明确区分。Root全部Job后代与lease闭合尚待实际。
- 固定reporter实际binary仍是D:/作品集/ResearchOS/research-os/.local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe，dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c /4932608 bytes。本次重新核hash，先前独立接受限TOOL_COMPILATION_COMPONENT；此处不调用工具，也不要求不存在的GOROOT/pkg/tool/test2json.exe。

## Root handoff conditions

可用于Root全新T6集成与实际验证。Root应使用已审官方reporter精确path/hash并重新guard；保留新compiled parent/child pins、exact argv、原始reporter stdout JSONL/raw/stderr、严格event-verdict、实际runner结果。运行回执资源sha256字段是带sha256:前缀的领域格式，与外部裸pin比较应显式规范化一次，不能忽略hash。

Root外层须补真实parent JSONL、terminal event及exit，核对original8native+2Goal实际结果，并证明test2json→compiled child→SDK所有descendants都在owned Go Job内且关闭、lease完整对账。Source actual_parent_exit=null/PENDING_ROOT_RECONCILIATION与actual_native_child_pid/exit=null/PENDING_ROOT_GO_JOB正确，不伪造未来事实。reporter将native stdout/stderr合并为Output，reporter stderr不是独立native stderr流。

以上是已有执行合同的待实际事项，不是本Source的新阻断。未执行/缺资源/skip不得PASS，父exit0不能代替后代关闭。源级APPROVE不提升旧FULL1261 PASS /25 FAIL /4 SKIP FAILED、不改CP356/OW168/SS/CM、6/22历史与0/42当前、GoalActive。

Q2两finding、4396旧审查、814/815历史记录原样保留，无新机械失败、不分配ordinal、不reset。Main/T5/canonical/旧receipts无修改。本review独占namespace封存后STOP。

