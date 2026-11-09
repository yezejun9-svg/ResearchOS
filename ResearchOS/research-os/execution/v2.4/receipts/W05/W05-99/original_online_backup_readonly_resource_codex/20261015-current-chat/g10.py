import json,hashlib,time
from pathlib import Path
from collector import E,R,W,D,DB,scope,save,pin
INTENT="Freeze finite COLLECTION_ONLY metadata map from already closed observers; no original resource reads or operations."
SQL=[]
def load(n):return json.loads((E/n).read_text(encoding="utf-8-sig"))
def queries(n):return {q["name"]:q for q in load(n)["queries"]}
if __name__=="__main__":
 q2,q3,q6=queries("g02-results.json"),queries("g03-results.json"),queries("g06-results.json")
 limits=load("workspace-limits.json");host=load("host-deployment-native-metadata.json");cross=load("selected-host-root-crosswalk.json");closure=load("observer-closure.json")
 assert limits["total_tree_metrics_complete"] and limits["outcome"]=="WITHIN_LIMITS_METADATA_ONLY"
 assert q3["active_workspace_count_exact_opsbackup"]["rows"]==[[1]]
 assert q3["table_counts"]["rows"]==[[88,87]]
 assert closure["all_sqlite_observer_connections_explicitly_closed"]
 native_nonzero=[]
 for p in E.glob("*.exit.json"):
  v=json.loads(p.read_text(encoding="utf-8-sig"))
  if v["native_exit"]!=0:native_nonzero.append(dict(id=p.stem,exit=v["native_exit"]))
 assert native_nonzero==[]
 roots=cross["selected_path_matches"];assert len(roots)==1
 initial=load("g02-results.json")["before"];final=closure["final_observer_metadata"]
 differences=[dict(path=x["path"],before=x,after=y) for x,y in zip(initial,final) if x!=y]
 gaps=[
 dict(id="G01",state="UNKNOWN",fact="No independently accepted same-handle 128-bit FileIdInfo/volume/finalpath/reparse/ACL/ancestor-continuity helper. fsutil and stat are auxiliary separate opens only."),
 dict(id="ACL_TRUST",state="OBSERVED_OPEN",fact="Current data root, database and workspace ICACLS show inherited Authenticated Users Modify; no shared ancestor ACL change or protection acceptance."),
 dict(id="HOST_FINAL_PATH",state="UNRESOLVED_METADATA_DIFFERENCE",fact="Selected stored Host final_path differs from its real_path; no native continuity verification or repair is authorized."),
 dict(id="DEPLOYMENT_CONFIG",state="UNKNOWN",fact="Historical activation path and existing public manifests / identical host.js prove public-file mapping, not current process commandline/config or actual RuntimeAssetsRoot equivalence."),
 dict(id="KEY_USABILITY",state="UNKNOWN",fact="No specific authorized recovery-key path supplied; no key contents read, no key created, no decryption test."),
 dict(id="BACKUP_DESTINATION",state="UNKNOWN",fact="No exact destination selected or created; its free space/access/workspace-overlap qualification remains unknown."),
 dict(id="RESTORE_AUTHORITY",state="NOT_GRANTED",fact="This scope grants only readonly metadata collection; no backup, restore, restart or mutation authorization."),
 dict(id="ACTUAL_HISTORY_VALIDATION",state="NOT_QUALIFIED",fact="Selected current DB metadata has RUNNING Run, UNKNOWN dispatch, MODEL CONFIRMED latest effect and UNKNOWN cost. No payload validator, raw journal/ACK read or prior missing nativeWait recovery was run."),
 dict(id="HISTORICAL_REQUEST_BINDING",state="UNKNOWN",fact="Scoped request ID has no row in examined domain_objects/resource_resolutions; this does not determine consumption in another storage surface."),
 dict(id="ONLINE_SNAPSHOT",state="NOT_EXECUTED",fact="Original DB/WAL metadata changed across observation windows. No backup or concurrent-writer snapshot test on original resources; cannot claim all bytes unchanged.")
 ]
 out=dict(schema="researchos.original-online-backup-readonly-resource-map.v1",verdict="COLLECTION_ONLY_RESOURCE_FACTS",source_commit=scope["source_commit"],
  read_only_metadata_authority=True,actual_authority=False,actual_mutation_or_backup_authority=False,formal_increment=0,self_acceptance=False,
  source_clean=True,collection_groups_after_intake=10,original_data_root=str(D),original_database=str(DB),
  exact_production_active_selector=q3["active_workspace_count_exact_opsbackup"],active_workspace_count=1,
  all_workspace_status_counts=q3["workspace_status_counts"],active_workspace_public_fields=q3["active_workspace_public_fields"],
  migration_versions=[r[0] for r in q2["migration_versions"]["rows"]],table_counts=q3["table_counts"]["rows"][0],
  user_version=q2["user_version"]["rows"][0][0],journal_mode="wal",observer_sqlite_version=q2["sqlite_version"]["rows"][0][0],
  queue_state_counts=q3["queue_state_counts"]["rows"],control_state_counts=q3["control_state_counts"]["rows"],
  restore_barriers=0,restore_guard_trigger_present=False,
  workspace_metrics=limits,historical_subject_current_selected_metadata=q6,
  selected_host_identity=host["host_identity"],host_registry_crosswalk=cross,
  original_file_metadata_differences_between_observation_windows=differences,
  within_each_database_group_metadata_equal=all(load(f"g{n:02d}-results.json")["before"]==load(f"g{n:02d}-results.json")["after"] for n in [2,3,6]),
  all_observer_handles_closed=True,no_all_bytes_unchanged_claim=True,
  sqlite_possible_shm_readmark_sideeffects="Not excluded by metadata equality; readonly connection may interact with SHM. No original DB/WAL/SHM content hashes or byte copies.",
  exact_raw3_ack2_revalidated=False,old_missing_native_wait_recovered=False,actual_backup_plan_accepted=False,gaps=gaps,
  old_counts_reset=False,prior_fixture_diagnostics_reimported=False)
 save("resource-map.json",out)
 save("limits.json",dict(production=limits["limits"],measured=limits["observed_lower_bounds"],within_metadata_limits=True,full_tree_completed=True,access="metadata-readable; byte-read authorization and continuity not established",key="UNKNOWN",destination="UNKNOWN",restore_authority="NOT_GRANTED",native_identity="G01_UNKNOWN",bounded_scan_seconds=limits["elapsed_seconds"]))
 save("diagnostic-ledger.json",dict(native_nonzero_count=0,native_nonzero=[],actual_operation_count=0,formal_increment=0,
  old_53_14_records="Previously adopted by Root; not replayed, recounted or reset",
  observations=[dict(id="HOST_REF_LOOKUP",classification="CORRECTED_INSPECTION_ASSUMPTION",fact="G08 direct ref match returned empty because Host root ref differs from domain workspace ref; G09 matched actual production RealPath lookup, found one nonrevoked READ_WRITE root. G08 retained."),
   dict(id="HOST_FINAL_PATH",classification="UNRESOLVED_METADATA_DIFFERENCE",fact=roots[0]["final_path"]),
   dict(id="CURRENT_DB_RUN",classification="CURRENT_SELECTED_FACT_NOT_FAILURE",fact="Run RUNNING, dispatch UNKNOWN, cost UNKNOWN; no false FAILED/SETTLED or old Wait completion."),
   dict(id="SCHEMA_NAMES_CAP",classification="BOUNDED_VIEW",fact="G02 schema_names capped at128 names; not complete trigger inventory. G03 separate exact counts prove88 total tables and queried restore-trigger absence.")],
  all_observer_handles_closed=True,resource_limits_exceeded=False,no_native_probe_denials=True))
 scripts=[pin(p) for p in sorted(E.glob("*.py"))]
 save("collector-pins.json",scripts)
 report=f"""# 原始在线备份资源只读核对

结论：COLLECTION_ONLY_RESOURCE_FACTS。当前资源的有限元数据核对已完成，不能据此批准实际备份计划。actual operation = 0，formal increment = 0。固定 Source 为 {scope['source_commit']}，前后 worktree clean；4项输入 pin 全部一致。共10个有限 collection groups（含报告冻结），未重做此前夹具或重计旧53/14记录。

## 当前事实

| 项目 | 本次只读结果 |
| --- | --- |
| 原数据库 | {DB} |
| SQLite | migration 1–24，user_version 0，WAL，88总表＝87非 sqlite_ 表＋sqlite_sequence |
| 活跃工作区 | 按生产 ops/backup 完全相同选择条件为1；无其他状态binding |
| 工作区ref | wsref-6243c8b1dd686be2，revision2，READ_WRITE |
| 工作区路径 | D:/作品集/ResearchOS/research-os/.local/worktrees/w05-own-cli-product-agent-20261012 |
| 工作区计量 | 659 files，68 dirs，8,587,076 bytes，最大文件380,696 bytes；完整有限扫描无已知reparse |
| 生产上限 | 8 roots /4096 files /4096 dirs /256MiB total /16MiB single file；本次metadata计量在限内 |
| queue / control | 两表当前均0条 |
| 恢复屏障 | backup_restore_barriers为0，backup_require_fresh_observation触发器不存在 |

扫描不读取文件内容，逐级检查reparse并设置10秒与数量/字节边界。已知工作区不在原data root内，但尚无备份目的路径，不能判定目的路径重叠、安全性或可用空间。没有accepted同句柄reader，因此这些数据只说明本次标准metadata观察，没有证明路径在整段读取中的连续性或真实backup byte-read成功。

## 历史subject的当前选定元数据

f3dcb996b2e43cf52cba874be7abfc70 当前仍是 RUNNING，revision2、lease_epoch1；dispatch 705b11ec99044fef19e85f57e2d2b712 为 UNKNOWN、observation_sequence0。一个 MODEL effect 的三条状态为 PREPARED→STARTED→CONFIRMED，最新CONFIRMED，receipt.actual_cost为JSON null。该Run的BudgetLedgerEntry为 UNKNOWN/UNKNOWN/money null，共1条。

该Run当前 runtime_observations 为0；本次按绑定run字段查询的client_control_receipts与MODEL_STREAM_OBSERVATION_V1数量均0。这些是指定表与条件的观察，不替代原始journal的raw3/ACK2证据。没有读模型原始响应、请求body或BLOB，没有补旧native Wait，没有将Run改称已关闭、FAILED或费用SETTLED。

scope给出的request ID在所查domain_objects/resource_resolutions没有记录，不能由此推断其他存储面的消耗状态。所有SQL、参数、URI flags在执行前recipe中固定并保存，结果时间分别记录于g02/g03/g06-results.json。

## Host、部署与原生边界

选读public Host ID为host-0b6cce7079a1，owner principal为owner-95f641f393696f7d1439dc36ae99935d。Host roots registry的ref与domain workspace ref不同；G08直接ref筛选为空，G09按生产SnapshotWorkspace的RealPath匹配找到唯一未撤销READ_WRITE记录（ws-1-1791809357937942400）。旧观察保留，不能把其空数组解释为未pin。

该记录的volume_id为ee413c31，辅助64bit file_id为1125899911390212，与当前stat辅助值一致；其stored final_path实际为：
{roots[0]['final_path']}
这与完整real_path不同。本范围没有修复、执行Host构造或资格验证，差异保留为未解决metadata事实。fsutil所得file IDs和ICACLS来自分别打开对象，不能替代G01所需accepted同句柄128bit身份、volume/finalpath/reparse/ACL/ancestor连续性。

当前data root、DB和workspace三项ICACLS均显示继承Authenticated Users Modify。未改任何ACL、未提升权限、未请求UAC。历史激活路径指向normal-verifier-replacement-4f4023-20261015；其public host.js与固定Source hash一致，公开安装manifest标记Main4f，相关资产文件存在。但没有当前进程命令行/运行配置观察，不能因此宣称实际Core资产配置与generic backup Host构造等价。

## 观察副作用与剩余条件

仅使用 Python sqlite3 URI mode=ro&cache=private，加PRAGMA query_only=ON；没有immutable=1，因而未忽略WAL。未调用store.Open、Host.New、备份CLI/API、VACUUM、checkpoint或任何写事务。所有observer连接已显式close。

每个数据库观察组内的前后file metadata相等，但跨组DB大小由58,732,544增至59,432,960 bytes，WAL mtime也变化。SHM记录mtime未变化不能证明其readmark或所有字节未动；没有取原DB/WAL/SHM内容hash或拷贝。本报告不把在线资源描述成静态快照，也不把这些变化归因于某个未经观测的writer。

仍缺：G01 accepted同句柄native helper、原生路径/ACL可信边界、stored final_path差异解释、实际部署配置等价性、具体可用恢复key、明确备份目的路径及其重叠/空间/访问资格、恢复授权、原实际历史完整backup校验。没有读取key或credential payload，没有创建key/备份/恢复目录，没有provider/worker/Core/Desktop/API/lease acquire/stop/fence/restart操作。资源未知不撤销既有有限Source夹具结论，但当前只读资料不构成实际backup acceptance。
"""
 (E/"RESOURCE-MAP.md").write_text(report,encoding="utf8")
 print(json.dumps(dict(verdict=out["verdict"],groups=10,active_workspaces=1,workspace_files=659,workspace_dirs=68,workspace_bytes=8587076,original_handles_closed=True,actual_operations=0,formal_increment=0,native_nonzero=0)))

