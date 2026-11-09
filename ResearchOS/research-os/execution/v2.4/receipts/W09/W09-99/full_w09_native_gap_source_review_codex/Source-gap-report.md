# W09 完整 Native 与正式链缺口

结论：Main `ops/ci/retrieval.py` 已具备 G01/G02/A06 生产逻辑；没有可直接复用的、当前 Main 的完整 Root producer 包。下一步先完成 profile/registry 兼容 Source，并基于已接受 C19 两阶段机制编写三个 selector 的新 Source 包。

| 路由 | Native / 模式 | 当前缺口 |
|---|---|---|
| retrieval G01 | 5 tests / 8 IDs / FIXTURE | CM39未登记；无当前 Source21 Native |
| retrieval G02 | 8 tests / 7 IDs / LIVE_WINDOWS | CM39未登记；无当前 Native与host/junction资格 |
| research.fixture C19 | 2 tests / 5 Native IDs / FIXTURE | 实际已合格，保留不重跑；正式profile兼容待修 |
| retrieval C19 | 同一 C19 Native / 独立route模式 | 实际已合格，保留不重跑；正式profile兼容待修 |
| retrieval A06 | 8 tests / 7 IDs / FIXTURE | CM39未登记；无当前 Native |
| security A06 | 可共享上行A06 Native，独立route模式 | 仍为Go/W17处理器，须登记Python router与环境 |

## 会阻止复用现 C19 的两个源码事实

1. `formal_profile_w09.py:304` 把 Native tool-run 限于 `execution/v2.4/receipts/W09/`，真实两次消费者引用却是 `execution/receipts/W09/.../native-tool-run.json`。有限纯 Reader 控制得到 `PATH_SCOPE`。复制 tool-run 不能解决，因为 line459要求实际dispatcher stdout与context引用同一路径。
2. line421要求每次dispatcher记录的整份CM哈希等于当前CM。四缺路登记将改变CM39哈希，旧C19回执便不再满足。必须用真实CM39归档、Root登记的变化链及当前等效C19 binding核验兼容，不能改写旧回执、借新hash或普遍放宽历史receipt。

## 最小生产 Source 范围

三个新selector，各一次：G01、G02、A06。G01的完整5-test roster包含两个C19子测试，这是G01自身新证据；独立C19 selector和其两次dispatcher保持0重跑。G02与A06虽然都有7 IDs，但check/case/scope不同，不能共享一份伪造改头报告。A06两个消费者可以共享一份A06 Native，但各自需要模式决定。

沿用已接受的C19 runtime/launcher/prepare/run作为机制输入，保持 Main Source21字节不变。新choice需要独立run/receipt/temp/profile/gocache，Main产物固定到各自 `run-<id>`；完整调用包是 `./adapters/retrieval` 加 `./internal/domain`，不能继承C19的单包、351-roster和已用输出路径。老finite49包明确 `not_current_combined_Main=true`、未授权且缺combined/runtime/compilation闭包，不能拿来直接运行本任务。

## 正式接受仍缺

四个依赖卡当前均ACCEPTED；CURRENT formal=0。Root capture Canon槽位和固定index不存在。还需六路当前context、C19/A06各四份GLOBAL文件、独立8项verdict、真实Root消息三行capture与index注册、issuance及owner接受。Source/Native/模式/组件资格都不等于FormalCaseAccepted。

精确输入三键refs、每个新job的argv/selector/IDs/输出，以及三个后续Source任务的交付合同见 `Source-gap-report.json`。本轮没有运行产品、SQLite、Native、dispatcher、模型或网络，也没有修改Main/Canon/Scope/计数。

## 执行身份的第三个兼容前置

实际C19 mode决定写明 `producer_id=codex:/root`，两dispatcher的owner与selected_worker也均为Root。profile line492把GLOBAL executor等同context executor；line724/725/727又要求executor、reviewer、Root三个不同身份。Source作者不能仅因写了launcher就被改称实际执行者。当前代码未把context executor绑定mode.producer_id，这一缺口不能用于绕过事实。

兼容Source必须明确并按原始调用、Scope、模式回执绑定Source作者、实际Native/dispatcher执行者、证据assembler、独立verifier、Rootissuer；保留Root实际执行身份。若不调整三身份政策，现C19正式复用仍阻塞。任何角色/schema调整须独立Source审查，不得改写既有producer_id、替换actor字符串或自签正式接受。
