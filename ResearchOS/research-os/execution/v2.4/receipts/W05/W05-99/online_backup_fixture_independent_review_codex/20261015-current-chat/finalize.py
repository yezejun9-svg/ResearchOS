import json,hashlib,time
from pathlib import Path
E=Path(__file__).resolve().parent
def load(n):return json.loads((E/n).read_text(encoding="utf-8-sig"))
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
facts=load("fresh-census-deltas.json")
hist=load("q03-independent-history-review.json")
schema=load("restored-schema-deltas.json")
assert set(schema)=={"('trigger', 'backup_require_fresh_observation')"}
assert facts["all88_source_logical_census_equal"] and facts["acl_equal"] and facts["source_native_file_deltas"]=={}
assert load("live-ready.json")["host_instance_id"]==load("live-after-create.json")["host_instance_id"]
assert load("native-workspace-identity-fixture-change.json")["visible_file_bytes_equal"]
matrix=[
 dict(id="P01",result="PASS",claim="Real unchanged ops/backup native CLI compiled without overlay",evidence=["b01-build-real-cli.exit.json","s04-go-build-info.stdout.raw","source-helper-native-pins.json"]),
 dict(id="P02",result="PASS",claim="Actual Host object plus source SQLite physical connection remained alive throughout true CLI create",evidence=["live_fixture.go","f02-live-host-holder.stdout.raw","f02-live-host-holder.exit.json","live-ready.json","live-after-create.json","f07-real-create.exit.json"]),
 dict(id="P03",result="PASS",claim="Separate-process actual DataRootLease blocks challenge before/after create; normal release permits acquisition",evidence=["f03-probe-before.exit.json","f08-probe-after.exit.json","f16-probe-released.exit.json"]),
 dict(id="P04",result="PASS",claim="88 total tables including sqlite_sequence; 87 non-sqlite tables; complete source schema/logical row census unchanged",evidence=["f04-db-before.stdout.raw","f09-db-after.stdout.raw","f15-db-after-negative.stdout.raw","n02-db-after-native-refusal.stdout.raw"]),
 dict(id="P05",result="PASS",claim="Native file metadata/content census and source ACL unchanged during fresh create",evidence=["f05-files-before.stdout.raw","f10-files-after.stdout.raw","f06-acl-before.stdout.raw","f11-acl-after.stdout.raw"]),
 dict(id="P06",result="PASS",claim="Operational restore preserves small file, empty directory, workspace/project refs and changes native path/revisions/credentials as expected",evidence=["f19-real-restore.exit.json","fresh-census-deltas.json","restored-schema-deltas.json"]),
 dict(id="N01",result="PASS",claim="Existing package refused; package unchanged and source logical state unchanged",evidence=["f13-existing-destination.exit.json","f13-existing-destination.stderr.raw","f12-package-before-negative.stdout.raw","f14-package-after-negative.stdout.raw"]),
 dict(id="N02",result="PASS",claim="Fresh separate wrong recovery key refused; destination not published",evidence=["f18-wrong-key-restore.exit.json","f18-wrong-key-restore.stderr.raw","driver.py"]),
 dict(id="N03",result="PASS",claim="Same visible file bytes under different native workspace root ID refused; destination not published",evidence=["native-workspace-identity-fixture-change.json","n01-native-workspace-id-refusal.exit.json","n01-native-workspace-id-refusal.stderr.raw"]),
 dict(id="H01",result="PASS_LIMITED_SYNTHETIC_HISTORY",claim="Current24 source UNKNOWN effect/queue history remains immutable subset after reconciliation; ten production queue SQL checks pass read-only",evidence=["q03-independent-history-review.json","018-q03-independent.stdout.txt","verified-input-pins.json"]),
 dict(id="U01",result="NOT_TESTED_LIMIT",claim="Concurrent atomic business writer / arbitrary concurrent workspace-file edits / live provider behavior",evidence=[])]
save("fresh-test-matrix.json",matrix)
limits=[
 "No concurrent business writer executed. The positive fixture has a live idle Host and open SQLite, not an executing worker/provider.",
 "SQLite snapshot consistency is supported by production code and official documentation; this review does not claim executed concurrent-writer qualification.",
 "Workspace bytes are read from native pinned roots after the database snapshot; no single atomic snapshot across SQLite and changing external files was demonstrated.",
 "Pinned Main4f Host Config has no RuntimeAssetsRoot field. Actual Core assets are wired separately through apps/control NewRuntimeSetup(...assets); generic backup Host.New cannot qualify that deployment configuration.",
 "Actual original root/workspace count, bounds, access, native IDs, source identity/config/assets, key usability and restore authority remain unknown and separately scoped.",
 "Author Q03 is synthetic current24 data with public effect calls plus explicit fixture SQL queue UNKNOWN; it does not establish original actual raw3/ACK2/MODELCONFIRMED/costUNKNOWN facts.",
 "No actual-root, Main/package or formal acceptance; Root must separately adopt this independent finite review.",
]
review=dict(schema="researchos.online-backup-fixture-independent-review-result.v1",
 verdict="LIMITED_FIXTURE_SOURCE_CAPABILITY_ACCEPTED",root_adoption_required=True,actual_authority=False,formal_increment=0,self_acceptance=False,
 source_commit="4f4023c956f84d65743f39ce77d6c8899a21ada1",source_tree="3db13a15cc52b2b0bd75cae3452c66509a9f55c9",source_clean=True,
 scope_sha256="b6cfd9fdd2406ae771e6a8949dedba611dc0764bd4671747c49a654c208c45a3",
 author_scope_inputs_sha256_verified=11,new_live_host_fixture=True,
 concurrent_writer_tested=False,all_source_tables_equal=True,total_table_count=88,non_sqlite_table_count=87,
 source_schema_equal_before_after=True,restored_schema_equal=False,restored_schema_expected_addition="backup_require_fresh_observation",
 new_meaningful_negative_count=3,source_native_census_equal=True,source_native_acl_equal=True,
 known_limits=limits,actual_resource_gaps=limits[4],formal_cases_new=0,
 historical_root_capture_verification=dict(recipes=195,files=777,fully_captured_at_author_freeze=193,fully_captured_after_selfseal=194,bootstrap_capture_gap=1,initial_wrongpath_prewrite_preserved=True,prior_nonzero_native_groups=25,recount_or_reset=False),
 own_diagnostics=dict(native_nonzero_expected=5,native_nonzero_diagnostics=2,auxiliary_rg_nonzero=2,nonterminating_inspection_errors=1,tool_parse_errors=2,initial_text_encoding_loss_preserved=True),
 review_timestamp=time.time())
save("review.json",review)
ledger=dict(
 prior_author_ledger="Preserved pinned author diagnostic-ledger.json and Root capture verification; no rewriting or recounting. 25 old nonzero groups remain 7 expected lease10 +3 expected CLI1 +8 primary diagnostics +7 auxiliary. Root old bootstrap gap+wrong path remain.",
 new_native_expected=[
  dict(id="f03-probe-before",exit=10),dict(id="f08-probe-after",exit=10),
  dict(id="f13-existing-destination",exit=1),dict(id="f18-wrong-key-restore",exit=1),dict(id="n01-native-workspace-id-refusal",exit=1)],
 new_native_diagnostics=[
  dict(id="001",exit=1,cause="Windows PowerShell5 read UTF8 no-BOM script as ANSI; Chinese scope path unavailable",resolution="002 new BOM script; original 001 preserved"),
  dict(id="014-verify-fresh",exit=1,cause="Reviewer asserted 88 non-sqlite tables; actual 88 total incl sqlite_sequence; also pre-run restore delta expectation corrected from four tables to measured two",resolution="verify.py v1 retained; verify_v2.py correct explicit 87+1 count; 016 passes")],
 auxiliary=[
  dict(id="004",native_exit=2,wrapped_exit=0,cause="rg included nonexistent adapters/sqlite path; stderr retained; actual internal/store/sqlite.go read in 005"),
  dict(id="012",native_exit=2,wrapped_exit=0,cause="rg included nonexistent internal/domain/service.go path; raw explicitly prints RG_NATIVE_EXIT=2; corrected directory lookup013 and store.go015"),
  dict(id="005",native_exit=None,wrapped_exit=0,cause="PowerShell Get-Content guessed absent author q03-current-db-before output; correct pinned report plus independent DB read018 used"),
  dict(id="tools-js-parse-before-verify-file",native_exit=None,cause="JS parse rejected embedded backtick before any tool/file command executed; corrected payload created verify.py"),
  dict(id="tools-js-parse-before-finalize-file",native_exit=None,cause="JS parse rejected Markdown backtick in report before any tool/file command executed; corrected payload created finalize.py"),
  dict(id="002-003-output-encoding",native_exit=0,cause="native redirected text initially garbled Chinese; scope verified via Python007; clean UTF8 AGENTS read022; originals retained"),
  dict(id="006-web-first-response",native_exit=None,cause="first official browse response was tool-visible; own stored006 contains subsequent follow-up response. Complete relevant official text retained020 plus WAL006; not a shell process")],
 no_product_failure_detected_in_executed_fixture=True)
save("diagnostic-ledger.json",ledger)
report="""# 在线备份有限夹具独立复核

结论：LIMITED_FIXTURE_SOURCE_CAPABILITY_ACCEPTED，待 Root 采纳。本结论只覆盖固定 Main4f 源码的有限夹具能力；actual authority = 0，formal increment = 0，self acceptance = false。Source HEAD 4f4023c956f84d65743f39ce77d6c8899a21ada1 / tree 3db13a15cc52b2b0bd75cae3452c66509a9f55c9，前后 worktree clean，未改任何 tracked Source、tests 或 Git。11 项 scope 输入 SHA-256 与大小均核验一致。

## 新独立证据

生产 ops/backup 编译没有 overlay；仅夹具 helper 使用 overlay。fresh key 与 wrong key 由真实 CLI keygen 创建，保存在独立私有目录，证据不含 key bytes。Go build-info 确认原生产 CLI、Go1.27.1、vcs.modified=false。程序和 helper pin 在 source-helper-native-pins.json。

作者 fixture_setup.go 的 DB defer Close 在 setup 结束执行，后续 lease_holder.go 只持 lease，因此旧 Q01/Q02/Q03 不能单凭 holder 推断 live Host/DB。本次 live_fixture.go 在新的小型 Host 授权 workspace 完成后，保持真实 Host 对象和 SQLite 连接，用 runtime.KeepAlive 保证 Host 生命周期；create 前后 Ping 成功、OpenConnections>=1、Host instance ID 相等，直到明确 release 才正常关闭。这个 holder 与真实 CLI 为不同进程，没有替换备份实现。

跨进程 root lease 在 create 前、后令独立 probe 返回10；holder 正常退出0后 probe 返回0。真正 encrypted create 与 operational restore 均返回0。fixture 只含一个小文件及 empty directory；恢复后文件 SHA-256 c9f09e0a76fbbf83847013f7d79aa09c1566778489cc499e76e3e5d72b1c8db6、空目录、authorized workspace ref 与 project ref 保留，路径移至新恢复根。

全部88张表（87张非 sqlite_ 表加 sqlite_sequence）的逐行值摘要、schema、版本及 integrity 在 create 前后完全相同，源 native files/sidefiles 的完整 census 与 ACL 也完全相同。否定例后源逻辑 census 仍相等。这里不能把88误说成88张业务表。恢复仅 auth_credentials 与 domain_objects 表值变化：WorkspaceBinding real_path/display_path/revision、Project real_path/revision；凭据重新签发。恢复 schema 另新增 backup_require_fresh_observation 触发器，这是 backup_recovery.go:233 的恢复屏障，因此源前后 schema 相等不等于恢复 schema 完全相同。

本次独立执行三个否定例：已有目的包 → DESTINATION_EXISTS，包完整 census 不变；新错误 key → BACKUP_MANIFEST_INVALID，未发布恢复目录；相同可见文件字节但新 native workspace file ID → BACKUP_WORKSPACE_PIN_CHANGED，未发布备份包。旧作者的通过结果不替代这三次新执行。

## 源码语义及官方文档

ops/backup/main.go 不调用 DataRootLease acquisition。它以 store.Open 打开源；internal/store/sqlite.go 设置/验证 foreign_keys、WAL、FULL、busy_timeout=5000 并 quick_check，不能称为只读 URI。active workspace=0 时直接 Service.CreateBackup；大于0则 Host.New 后 CreateBackupWithWorkspaces。

backup.go:380 执行 VACUUM INTO，之后 runtime、migration/schema、inventory、sealed BLOB、portable objects、queue 等都从该 snapshot DB 导出，并关闭/checkpoint snapshot 后加密；没有重读原业务 DB 导出这些内容。SQLite 官方说明 VACUUM INTO 可生成 live DB 的一致快照，未完成时的中断仍可能留下不完整输出。[VACUUM INTO](https://www.sqlite.org/lang_vacuum.html)

WAL 的读事务保持自己的已提交视图，读写可并行，但 writer 仍串行；独立连接通常只见已提交事务。这些说明支持代码的 SQLite 快照设计；本次没有执行并发业务 writer，不把文档推断记成实测。[WAL](https://www.sqlite.org/wal.html)、[Isolation](https://www.sqlite.org/isolation.html)。官方浏览内容保存在006/020。

Host.New 并非纯读：会 MkdirAll、privateDir 修改 DACL；打开 credentials/workspaces/selections 目录与 registry/vault/state；domain.NewCurrentMu→New 包含迁移安全检查、可能迁移与 session additive schema/fence事务。已有初始化夹具重复构造无差异不能保证任意实际根无副作用。固定 Main4f host.Config 没有名为 RuntimeAssetsRoot 的字段；实际 Core 资产在 apps/control/main.go:277-286 解析 runtimeAssetsDir/安装目录，再传 NewRuntimeSetup(...assets)。备份 CLI 的 generic Host config 不走该资产接线，因此尚未核验实际部署的配置等价性。

SQLite 中的 workspace binding 来自 snapshot，但 native workspace 文件由 Host.SnapshotWorkspace 在其后逐文件读取，有 native pin、路径/文件/字节上限及身份检查；不能把它说成 SQLite 与所有变化中文件的统一原子快照。此 finite 小工作区没有并发外部文件写入。上限为8 roots、4096 files、4096 dirs、总256MiB、单文件16MiB，实际根资源是否符合未知。

## Q03 历史复核

作者 current24/88表 Q03 由当前 public Prepare/Begin/ObserveEffect 创建 UNKNOWN effect，并显式使用 fixture SQL 为 queue UNKNOWN 及 revoked binding 造状态；未借旧22版本复制后迁移冒充。独立只读查询确认源 Run QUEUED、effect UNKNOWN1、queue UNKNOWN1、control REQUESTED、binding REVOKED；恢复 Run/control RECONCILING、queue UNKNOWN1、binding REVOKED。

原3条 resource_effects、原1条 client_control_receipts 及 uploaded_content 全部以完整行值保留于恢复结果；effect 追加一条 UNKNOWN、receipt 追加恢复记录。另执行生产 validateBackupQueue 中10条无参数绑定 SQL，源/恢复均0违规；完整生产 validator 的既有作者执行与真实CLI证据已 pin，不伪称这10条等于所有Go校验。未执行外部 provider 或 worker。此 synthetic 事实不能证明原实际 f3d raw3/ACK2/MODELCONFIRMED/costUNKNOWN 已具备备份资格。

## 限制与证据完整性

本次仅证明 live idle Host/SQLite + root lease + 小型 Host-pinned workspace 的 finite create/restore；未测试并发业务writer、任意并发workspace改动、真实worker/provider。实际root/workspace计数、尺寸上限、访问权限、source identity/config/assets、native accepted ID、key可用性及恢复授权均待独立实际资源范围。本复核不因未来实际资源未知否定已测Source能力，也不据fixture批准实际backup计划。

旧作者195recipes/777files、freeze时193完整及随后自封完成194、bootstrap缺口与初始错误路径、25非零分组全部保留原口径，不重置、不重算。新失败诊断亦保留：001编码路径失败、014表数量口径断言、两次辅助rg错误路径、一次缺失作者文件读取、两次工具JS解析失败。它们与5项预期非零拒绝分别记录在 diagnostic-ledger.json。早期文字编码和首个web本地捕获边界如实记录，正确读取与官方引用有后续完整证据。

可重建 Go cache 259672073 bytes 已仅从本支 ownTMP 删除；小型encrypted fixture、fresh keys、原生程序保留供Root复核。final manifest 不包括 key文件；receipts包含命令、原始输出、native exit、census/deltas、source/helper pins与测试矩阵。Root采纳属于下一步，本报告不写共享state。
"""
(E/"review.md").write_text(report,encoding="utf8")
print(json.dumps({"verdict":review["verdict"],"matrix_cases":len(matrix),"actual_authority":False,"formal_increment":0,"review_files":["review.md","review.json"]}))

