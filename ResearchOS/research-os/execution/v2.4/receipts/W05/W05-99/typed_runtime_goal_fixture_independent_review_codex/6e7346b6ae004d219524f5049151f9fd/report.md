# Independent Source review — REQUEST CHANGES

结论：SOURCE_COMPONENT_NOT_ACCEPTED。五个 test-only 文件的 fixture 方向符合窄合同，但 compiled child 证据链尚不满足逐叶 JSONL 要求，修订前不接受本 Source 组件；无 Go 编译或运行结论，无产品接受权限。

输入 Source：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931。
HDF sha256 21452223845c767f89fb1660b21f751b906a9a6d2a6f9d2adefd0787b4e94f53 / 8255 bytes。
MF sha256 dcb1812c7b5d44a8db70fe0bb98ba93c9013ae016487f952a392565ec7715299 / 6789 bytes。
审查者 /root/typed_fixture_source_review，与 Source 作者独立；读取指定 T5，不编辑 Q、T5、Main、canonical。

## Critical Issues

无已证实生产 Critical。未运行不代表没有运行缺陷。

## Important Issues

- candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:133、172–178：exact compiled child 使用 -test.v 输出普通文本，父包装器以 bytes.Contains 的 RUN/PASS 子串判定全部叶通过，仅保存 raw stdout/stderr，无 child JSONL、无严格事件解析。外层 Go JSONL只能记录父 case 与其日志，不能恢复未产生的 child run/terminal 事件；子串不能证明精确叶、单一终态和无重复。须在新 Source namespace 以 Root 冻结 RESEARCHOS_GO 的 tool test2json 执行精确 compiled binary/case，使用 -test.v=test2json，保存原始 child JSONL/stdout/stderr、工具和编译二进制 pins/argv/exit，并严格验证每个 expected leaf 的真实 run 与唯一 terminal pass，拒绝 fail/skip、重复或缺失事件及非预期 case。不得合成事件、重跑原失败输入或改原断言。Root 必须对 Go/test2json/child/SDK descendants 全部 Job 成员与 lease 收尾核对；父 exit0不能代替。属于运行证据生成代码的阻断问题，非声称现有业务断言失败。

parent-result.json 无法预知所在父进程的未来退出，不要求其伪造 exit；应明确 parent_exit=null / PENDING_ROOT_ACTUAL，并由 Root 外层真实 parent exit 与 terminal event 关联补齐。现有 REQUIRES_ROOT_GO_JOB_RECEIPT 保持正确边界。

## Suggestions

- Source static-checks.json / construct.py:121：196 是包含 Fatal/Fatalf/Error/Errorf 标识符的词法 if 数，严格含 t 断言的 if 数是190。额外6个是 fmt.Errorf 返回块，全部保留。建议将名称改为 assertion_or_error_if_nodes，避免把196当成196个独立断言。此口径差异没有形成断言删除。

## What's Done Well

- 五个候选都是 *_test.go，生产成员0；四个最小diff保留181个原 t.Fatal/Error/Skip 调用、20个原顶层 Test 名及其顺序，196个作者口径 if 节点全部保留。独立算法、精确计数及额外6节点见 checks.json/if-node-supplement.json。
- typed helper 通过真实公共 host.configure 返回 model_config_ref 后封存 profile；provider=openai、model=fixture-model、endpoint、CredentialRef/Revision 同 synthetic ref，model_config hash 与 profile/qualification route一致；原callback及 Model/Tool目的保留。ClientService 与 RuntimeCoordinator 共用受限主体/provider/ref metadata fixture。
- localhost TLS 保留 x509.Verify、空根/错误主机名拒绝和独立child fallback roots，无 InsecureSkipVerify；保留 readiness 与业务请求分离、固定 Node/bundle 输入、真实资格与业务断言。没有执行TLS或SDK，故这里只认可源码结构。
- 原权限allow/deny/expire/其他资源阻塞、物理IO、Run/Task、事件先落盘和rollback断言都未削弱；公开同owner attach 校验同Session/revision，原 send revision=1/writer_epoch=1保留。
- Goal mock ValidateLegacySession限定principal/project/session/model/workspace，读取真实clientSessionCreationPrincipal和唯一COMPLETED原goal.start创建回执，未手写这些业务回执；admitErr仍为原未资格化拒绝，LEASE_EXPIRED及goals=1/tasks=1/runs=0原断言保留。它是unit synthetic port，不是runtime/model资格。
- 原FULL raw JSONL独立复算1261 PASS /25 FAIL /4 SKIP，scope-map的10个原失败事件及原始行逐一匹配；原FULL FAILED不提升。

## Verification Story

- Tests reviewed: yes，先看四测试diff/新helper，再追依赖；181调用、196词法if、20 Test名保留且所有已绑定input hashes一致。
- Build verified: no；Go/gofmt/native/SQL/model/DPAPI/Owner命令均0，本轮只有文件读取及固定Python静态检查。未验证类型/编译或任何真实运行成功。
- Security checked: static only；检查synthetic metadata精确边界、TLS验证、来源/租约原断言、无production修改。RootJob实际覆盖与子后代关闭未验证，必须真实回执。
- Source 原工具IO及814 ShellquotingSyntaxError指向原Source IO namespace并保存全部文件pins，不覆盖、不抹除。独立检查自身815 NameError、outer/Python exit1/native null完整保存；临时失败脚本在分配回复前已编辑，failed-script.815.py按精确patch差分重建并明确标注，不谎称原文件未改。更正版本另路径单次运行exit0，原失败不重跑、不reset。
- check首轮严格if统计190，补充按作者词法口径独立计算196，均保留；这一计数差异不是执行失败。
- 全局CP356/OW168/SS/CM、6/22历史与0/42当前、GoalActive按Root输入继续保持；本review不修改或独立重验全局治理计数。
- source的tool-io.json与独立check/recovery公开工具IO均通过input-refs/tool-io绑定；此前只读查看的工具输出保留于会话，不将此包宣称完整会话转储。

下一步限作者新namespace最小修订 child JSONL证据后重新独立Source审查；不在旧封存包原地修订。正式编译、10叶实际执行、Job/lease关闭和独立实际审查仍待Root新授权。STOP。

