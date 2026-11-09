import datetime,hashlib,json,pathlib,sqlite3,subprocess
P=pathlib.Path(__file__).resolve().parent
W=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012')
A=P.parent.parent/'workspace_projection_repair_codex'/'20261012-current-chat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(W),*args]).decode('utf-8').strip()
m=json.loads((A/'author-manifest.json').read_text('utf-8-sig'))
verification=json.loads((P/'input-verification.json').read_text('utf-8'))
assert all(x['pass_'] for x in verification['checks'])
assert sha(A/'author-manifest.json')=='4c5894536bb889cb866732a5a9d35ff7457366c34f9389ac3ccba617cbfaa56f'
assert all(sha(W/x['path'])==x['sha256'] for x in verification['source_inputs'])
assert git('rev-parse','HEAD')==m['source_commit'] and git('status','--short','--untracked-files=no')==''
assert json.loads((P/'test-result.json').read_text())['exit_code']==0
snapshot=P/'native-http-evidence/TestConfigurationActualWindowsHostOfflineHTTP/public-host.sqlite'
db=sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True)
responses=[]
for principal,operation,key,body in db.execute("SELECT principal,operation,key,body FROM idempotency WHERE operation LIKE 'v2:%' ORDER BY operation,key"):
 responses.append(dict(principal=principal,operation=operation,command_id=key,response=json.loads(body)))
bindings=[json.loads(x[0]) for x in db.execute("SELECT body FROM domain_objects WHERE kind='WorkspaceBinding'")]
counts={kind:db.execute('SELECT count(*) FROM domain_objects WHERE kind=?',(kind,)).fetchone()[0] for kind in ['Task','Run']}
counts['resource_effects']=db.execute('SELECT count(*) FROM resource_effects').fetchone()[0]
counts['client_sessions']=db.execute('SELECT count(*) FROM client_sessions').fetchone()[0]
db.close()
assert counts==dict(Task=0,Run=0,resource_effects=0,client_sessions=1),counts
assert len(bindings)==1 and bindings[0]['revision']==2 and bindings[0]['status']=='ACTIVE'
by_id={x['command_id']:x for x in responses}
assert by_id['send-unqualified']['response']['status']=='REJECTED'
assert by_id['create-offline']['principal']==bindings[0]['principal_id']
assert by_id['status-bootstrap']['response']['result']['workspaces']==by_id['list-bootstrap']['response']['result']['items']
assert by_id['status-bootstrap']['response']['result']['workspaces'][0]['authorized_workspace_ref']==bindings[0]['authorized_workspace_ref']
assert by_id['create-offline']['response']['result']['workspace_ref']==bindings[0]['authorized_workspace_ref']
assert by_id['create-offline']['response']['result']['project_id']==bindings[0]['project_id']
write('native-http-snapshot-audit.json',dict(snapshot_sha256=sha(snapshot),counts=counts,public_binding=by_id['status-bootstrap']['response']['result']['workspaces'][0],command_responses=responses,assertions_passed=True))
write('end-verification.json',dict(source_commit=git('rev-parse','HEAD'),tracked_status=git('status','--short','--untracked-files=no'),author_manifest_sha256=sha(A/'author-manifest.json'),unchanged_source_inputs=len(verification['source_inputs']),all_unchanged=True))
matrix=[
 ('same_transaction_current_state_and_rollback','author projection test independently rerun: uncommitted registration/bootstrap and rollback'),
 ('principal_project_grants','rerun exact-principal/OWNER isolation/task-only grants; independent two-project filtering, current grant removal, 1000 foreign rows'),
 ('local_remote_readonly','rerun DeviceID rejection and local PLANNER READ_ONLY visibility; unchanged native file authority gates source-reviewed'),
 ('revocation','rerun own REVOKED visibility; independent revoked-principal/credential rejection and revoked binding checkClientBinding refusal'),
 ('frozen_reply_shape','exact7 fields schema validation and sensitive-field exclusion; independent native HTTP equality and same projection reference'),
 ('malformed_state','independent8 own-row malformed variants all typed RESOURCE_BLOCKED; author foreign malformed row excluded'),
 ('capacity_order','rerun1000 success/1001 typed RESOURCE_BLOCKED no partial output; independent foreign1000 do not consume limit and ordered two-project/unbound result'),
 ('envelope','rerun direct dispatch session/CAS/writer rejection and actual HTTP payload/foreign scope; independent direct request-schema protocol/native/secret/payload rejection'),
 ('fresh_replay','independent full Execute observes current grant removal/new command and preserves original exact replay; HTTP registration rev1/bootstrap rev2/empty replay'),
 ('db_errors','independent closed tx returns error not empty success; source row/query/scan error propagation reviewed'),
 ('actual_windows_http','independently rerun actual Windows Host/SID and authenticated loopback; deterministic native chooser; projected ref creates one offline Session, unqualified send rejected and0 Task/Run/resource effects')]
report=dict(schema='researchos.workspace-projection-independent-review/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT',acceptance_scope='SOURCE_AND_LOCAL_NATIVE_HTTP_FIXTURE_ONLY',source_commit=m['source_commit'],base_commit=m['base_commit'],source_tree=m['source_tree'],author_manifest_sha256=sha(A/'author-manifest.json'),bundle_sha256=m['bundle']['sha256'],scope_sha256=m['scope_sha256'],assessment_sha256=m['assessment_sha256'],findings=[],verification=dict(binding_checks=23,source_inputs_observed_and_rechecked=642,author_targeted_cases_independently_rerun=3,independent_matrix_subcases=16,test_exit_code=0,go_overlay='Only adds reviewer test; no source replacement or Source writes',native_http_snapshot_sha256=sha(snapshot)),review_matrix=[dict(boundary=a,evidence=b,status='PASS') for a,b in matrix],historical_failures=dict(author_raw_preserved=True,old_regression_failures=['max migration24 versus old test23','artifact.import old test missing writer_epoch'],classification='Author baseline replay evidence and raw hashes reviewed; not independently rerun and not repaired; not counted as candidate passes'),limitations=['No whole Go suite rerun or desktop binary rebuild','Actual Windows Host/SID is exercised in temporary fixture with deterministic chooser; no visible Root GUI trial','No provider/model/tool/live writes or user dataRoot access','No parent or42 formal acceptance claimed; Root is sole integrator'],execution_notes=['prepare.py initial scope parent index was wrong and raised FileNotFoundError before testing; corrected exact root then23 bindings PASS','All reviewer tests first actual run passed; no source edits or behavior patches','Automatic approval rejected native PowerShell cleanup of exact owned go-cache/go-tmp/test-tmp paths: blocked by policy; retained with no alternate deletion'],gates=dict(source_canon_main_mutations=0,actual_model_calls=0,actual_tool_calls=0,root_gui_actions=0,parent_acceptance_delta=0,formal_acceptance_delta=0))
write('independent-review.json',report)
(P/'README.md').write_text('''# Workspace projection 独立审查

结论：ACCEPT，范围仅 SOURCE_AND_LOCAL_NATIVE_HTTP_FIXTURE_ONLY。候选 cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8，基线 1004cf9b8414ee4a248301ead447bc4a022f87d7。无新增 actionable findings。

23 项输入绑定通过；记录并复核 642 个执行相关源文件。独立重放作者 2 个投影测试与 1 个实际 Windows Host/SID HTTP 流程，另用仅新增测试的 Go overlay 运行 16 个边界子例，全部通过。覆盖事务内状态、principal/project/grant、远端隔离、READ_ONLY、REVOKED、损坏记录、1000/1001、七字段协议、envelope、fresh/replay 和 DB 失败。

HTTP 快照确认只有 1 个 offline Session，其 principal/project/workspace 与新投影一致，Task/Run/resource_effects 均 0，未资格化发送 REJECTED。实际 Windows Host/SID 与认证 HTTP 已运行；native chooser 是确定性测试回调，没有实际 Root GUI 验收。

作者保留的两个扩展旧回归失败在精确 base 同现；本审查核对证据哈希，未再次复跑或修旧测试。未整套重跑 Go，未重建 Desktop。Source、Canon、Main、Root 真实数据未修改；真实 model/tool 为 0；parent/42 正式验收增量为 0。Root 唯一负责整合和真实界面重试。

自动审批拒绝了本次自有 go-cache/go-tmp/test-tmp 清理，原因 blocked by policy；目录保留并从证据清单排除，没有绕过。首次验证脚本路径层级计算错误在测试前报错，纠正后所有绑定通过。
''','utf-8')
excluded={'go-cache','go-tmp','test-tmp'}
members=[]
for p in sorted(P.rglob('*')):
 rel=p.relative_to(P)
 if not p.is_file() or rel.parts[0] in excluded or p.name in ['receipt_manifest.json','review-seal.json']:continue
 members.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write('receipt_manifest.json',dict(schema='researchos.independent-review-receipt/1',decision='ACCEPT',members=members,excluded_runtime_dirs=sorted(excluded)))
write('review-seal.json',dict(decision='ACCEPT',report_sha256=sha(P/'independent-review.json'),manifest_sha256=sha(P/'receipt_manifest.json'),member_count=len(members)))
print((P/'review-seal.json').read_text('utf-8'))
