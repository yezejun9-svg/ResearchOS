# H20R2 actual 独立组件复核

结论：COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY。此次接受固定新隔离目录内五个 History20 父测试、四个漂移子用例的实际组件验证。9 PASS、0 FAIL、0 SKIP，包级 PASS；不批准 W05 父任务、正式 case、Main 采用、CLI、真实发布程序或完整20→24链。

固定 actual validation.closed.json 为 b180ec16163730afbe03f0d62fa0caf368b3d087a048408ddb8d691d7e1fceac / 26677，isolation.ready.json 为 3ca2c6700bcad61b3e614e2683b95898b38635c0a5b58acfd4e0400a49fa6deb / 4045。Root caller HDF/MF 和独立 caller HDF/MF 全部核验；此前 H20R2 Source 587 项检查结论按固定 HDF/MF 复用，未重跑原 Source 构造/测试；914 失败实际与旧独立报告保持原样，未被本次成功改写。

本次独立复核 25,965 项检查，5,049 个输入 pin，全部通过。对 original Root tool IO、10 次调用 receipt、原 stdout/stderr、61 Source 组合、格式化后成员、编译 inventory、所有实际 guard closure、完整 raw JSONL 和实际编译 test Source 逐项核验。原审查 Python initial9d5b53/session27337，completion85f7b3 outer0/明确 REVIEW_PYTHON_EXIT=0；本次没有新的机械失败。

Root actual 隔离调用 initiald52d25/session26386、completiondcebf4 outer0/明确 ROOT_PYTHON_EXIT=0，六次 owned Git 都为0且闭合。验证 initialc585e3/session15116、pollfd412e、completion24f63b outer0/明确 ROOT_PYTHON_EXIT=0。format、go-list、tagged compile、official test2json 四个 owned primary 均为0，10 个 Job 均 confirmed primary exit、zero active、job idle、handles closed，无超时或清理错误。逐个 PID 与 FILETIME 从原 JSON 十进制 token 经 Python int 校验，未经过 JavaScript Number。test2json primary PID72164 / FILETIME134359955602925160 / exit0；单独 descendant test binary exit 仍为 NULL，不从 primary 推造第二个退出码。

实际七个 Source guard 全部 PASSED、closed、zero retained、每个 entry verified/final_path_match/closed。隔离两组 entry 数115、30；验证五组为990、29、62、3925、2。本次独立 SourceReadGuard 也已关闭，无残留；canonical 四文件仅作精确前后读取，未持有其 guard 句柄。只有本次 review 目录产生新文件；没有运行 Git、Go、SQL、product native、product API、私钥或外部模型操作。Root 原实际测试确实执行 public fixture SQL，此处不把审查只读性质误说成原测试未执行 SQL。

61 个原始 Source ref 与独立 caller 组成一致，非 H20 的 T11 refs（包括 AF）保持原始身份。H20R2 测试原始 pin 为 914792b2e903f15026ea0a6d0652e1db5401076dc24fc9132bebaad3fa930f2f / 10174。实际 gofmt 改变12个文件的字节，其中包括 AF 和 H20 文件，详列 format-delta.json；不宣称格式化后仍与原始 T11 字节相同。所有格式化后61成员匹配 guard 和当前隔离文件。

从原 go-list JSON 串逐项重建得到352个包、3733个编译输入、39个 embeds；再按 caller 的完整 product 范围遍历重建607个文件、核实8个 compiler工具，全与封存 inventory 精确一致。tagged domain test binary pin 为14c7fc727df6ac4e12b5a08aa871a7d1ba917f01b6fa9fbb43e3d4066762e992 / 42653696。四个 H20 domain 文件实际进入编译闭包；ops/backup/main.go 仅在 Source overlay/product inventory 中，没有编译或执行 ops/backup CLI。official test2json pin dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c，执行 selector 精确五父，count1，timeout14m。

raw JSONL 恰好9个唯一 run与9个唯一pass，五个父和四个漂移叶子完整，包级最终pass，stderr为空。没有 skip、fail 或其他父测试。59个组件父 Source 保留，其中54个未选择；137个 overlay 测试函数声明只是 Source inventory，不计为本轮执行。

本次成功补齐的实际断言：
- Public UpgradeLocal 从分离的 source/key/snapshot/destination 目录进入 A20→plain21。源 whole rows不变，恢复 invariant通过，ledger21、pending windows为空、未装client_sessions，Owner principal row不变，恢复 credential全部撤销。matching upgrade policy正确密钥先通过、state.sqlite和20项原ledger得到验证；只换错误密钥后精确 BACKUP_MANIFEST_INVALID 且 files=nil。
- 四个漂移分别要求 UPGRADE_RELEASE_HASH: 0021_research_pending_windows.sql、UPGRADE_RELEASE_MIGRATIONS: require exact 1..20、UPGRADE_SOURCE_SCHEMA、UPGRADE_SOURCE_SCHEMA，并都检查 snapshot/destination未发布和源rows不变。不能再由无关路径重叠错误获得误通过。
- ledger insert trigger 的 fixture ledger failure 实际触发后 schema与rows均不变。
- generic RestoreBackup failure 确认 callbackCalled，回调内CREATE TABLE成功后返回context.Canceled，外部errors.Is断言通过；destination未发布、backup仍在、manifest逐字节不变、源rows不变。这是 generic RestoreBackup 组件失败，不扩展为 UpgradeLocal失败路径验收。
- populated source 的隐式启动迁移仍精确拒绝 MIGRATION_PREBACKUP_REQUIRED。

Main 证据边界：实际 pre-run HEAD为adc460c2138528f163f7fdab5e8d81dde157b7fb，原tracked状态13行（11D、2M），staged为空。eight explicitly guarded Main文件和四个canonical全部与实际guard/pre-run refs一致，live checkpoint为364；caller写路径限定新worktree/receipt/environment。没有 post-validation Git 或逐文件全仓 byte baseline，本报告不捏造全仓 hash验收。Main_adopted=False保持原值。

原始 trial DB、真实Owner/发布程序路径、旧trial provider请求、九个 native authority cases、formal42和完整20→24仍OPEN；组件 public fixture program bytes不能当成真实release binary或Owner凭据。Source模型、provider无调用的限定继承本次固定caller与测试路径，原trial provider计数仍NULL。

STOP/FINAL。仅向Root提交组件审查，实际采用和canonical更新仍由Root负责。

