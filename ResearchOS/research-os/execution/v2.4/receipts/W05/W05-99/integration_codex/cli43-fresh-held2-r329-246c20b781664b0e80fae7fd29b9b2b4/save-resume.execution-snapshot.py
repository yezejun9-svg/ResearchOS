"""Save actual r329 failed-run resume; immutable earlier snapshots and counters remain."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).absolute().parent
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode=True
def pin(p):
 p=Path(p).absolute();b=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,d):
 with (OUT/n).open('xb') as h:h.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8'))
old=read(OUT/'RESUME.authorized.snapshot.json');scope=read(OUT/'scope_registration.json')
grantp=Path(scope['new_authorization_root'])/'authorization.execute.json';grant=read(grantp)
canon=[]
for row in grant['canonical_copies']:
 r=pin(ROOT/row['canonical_path']);assert (r['sha256'],r['bytes'])==(row['ref']['sha256'],row['ref']['bytes']);canon.append(r)
closed=read(OUT/'root-launch.outer-completion.json')
assert closed['actual_outer_tool_exit']==closed['actual_python_caller_exit']==closed['actual_launcher_native_exit']==1
assert closed['registered_origin_count']==481 and closed['observed_origin_count_at_closure']==488
assert closed['native_calls']==14
roster=closed['actual_case_roster_original_payload'];assert roster[0]['qualified'] and roster[0]['actual_native_exit']==0
assert roster[1]['actual_native_exit']==1 and not roster[1]['qualified']
late=list(old['outside_fixed_cut'])
for originid,p,native,outer in [
 ('96b781',OUT/'failure-origin.96b781.json',None,0),
 ('df2508',OUT/'failure-origin.df2508.json',None,1),
 ('e4a785',ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c/origin.I18-regex-shape.json',1,1),
 ('1b2841',ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_controller_v3_independent_source_review_codex/3b5ae723087647b6a884329c2ff8518c/origin.I17-diagnostic-literal.json',1,1)]:
 late.append({'origin':originid,'ref':pin(p),'actual_native_exit':native,'actual_outer_exit':outer})
assert len(late)==7 and len({x['ref']['sha256'] for x in late})==7
snapshot={'schema':'researchos.root-resume.actual-execution.v1','actor':'codex:/root',
 'snapshot_stage':'R329_CONSUMED_FIRST_CASE_QUALIFIED_SECOND_CASE_NATIVE_FAILED_TRANSPORT_ORACLE_DEFECT',
 'actual_canonical_tuple':[329,157,481],'canonical_refs':canon,
 'current_head':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','current_card':'W05-99',
 'scope_ref':pin(OUT/'scope_registration.json'),'grant_ref':pin(grantp),
 'actual_execution_completion_ref':pin(OUT/'root-launch.outer-completion.json'),
 'actual_execution_closed_manifest_ref':pin(OUT/'root-launch.closed.manifest.json'),
 'original_tool_observations_ref':pin(OUT/'root-launch.tool-observations.json'),
 'actual_native_calls':14,'first_case_native_exit':0,'first_case_controller_qualified':True,
 'second_case_test2json_and_test_exit':1,'second_case_actual_CLI_exit':3,
 'second_case_CLI_exit3_is_original_expected':True,'second_case_controller_fixture_observation_original':'NOT_STARTED',
 'second_case_actual_HTTP_observed_in_closed_records':True,
 'qualification':'WITHHELD_PENDING_INDEPENDENT_FAILED_EXECUTION_CLOSURE',
 'independent_reported_cause':'cli43AssertBinding canonical.JSON applied to empty-body GET Goal/Task; original CLI TASK_BLOCKED output is complete. Exact cause source/byte links pending W05 seal.',
 'original_cause_native_NULL_preserved':True,'original_E_failure_origin_ref':closed['first_origin_ref'],
 'scope_grant_consumed':True,'same_scope_relaunch_allowed':False,
 'outside_fixed_cut_sealed_metadata_origins':late,'sealed_observed_origin_count':489,
 'I17_new_revision_reported_metadata_origins':{'count':4,'actual_native_outer_report':[1,1],'exact_sealed_refs':None,'authority':'author report; sealed handoff pending'},
 'known_observed_origin_count_at_snapshot':493,'root_closure_488_historical_count_unchanged':True,
 'source_branches':{'driver18_v3':'Source-only tail fix non-author READY; target and authority still OPEN',
 'driver18_missing_modules':'pprof/fileutil bytes delivered and independently source-resource verified; further declared dependencies and actual graph OPEN',
 'I17_revision':'new66ec raw byte/predicate preparation reported; four original metadata failures retained; awaiting sealed refs/non-author review',
 'Desktop15':'HOLD until fresh current43 both held cases independently qualified',
 'F08_SQL24':'OPEN_NOT_ACCEPTED'},
 'next_action':'Wait actual W05 failed-run review, prepare strict transport-aware helper correction and independent source review, capture all exact late origins into new fixed cut and new scope/grant, recompile and execute once.',
 'previous_snapshot_ref':pin(OUT/'RESUME.authorized.snapshot.json'),
 'preserve':old['preserve'],'completion_gate':old['completion_gate'],'cleanup_pending':old['cleanup_pending'],
 'credential_policy':old['credential_policy'],'canonical_writes':0,'formal_increment':0,'source_acceptance':False,
 'automatic_retry':False,'counter_reset':False}
save('RESUME.execution.snapshot.json',snapshot)
with (OUT/'RESUME.execution.snapshot.md').open('xb') as h:h.write(('# ResearchOS r329 实际执行续跑\n\nCP329 / OW157 / 注册481保持。第一例已通过本轮控制器校验，第二例原CLI TASK_BLOCKED/3符合原期望，但新增记录器将GET空body按JSON命令解析，测试进程失败；完整原证据已闭合，旧授权已消耗，不能重跑。独立资格复核尚未封。\n\n下一步 strict transport-aware helper新候选→非作者复核→精确晚到失败cut→全新scope/grant→重编译单次验证。当前已封观察489，另I17作者4条真实metadata失败exactrefs待封，已知观察493，不重置。Desktop15仍HOLD；42正式当前有效接受最后核对0，目标未完成。\n\n误写脚本清理仍被automatic review blocked by policy，保留原文件。\n').encode('utf8'))
save('RESUME.execution.snapshot.manifest.json',{'members':[pin(OUT/n) for n in ('save-resume.execution-snapshot.py','RESUME.execution.snapshot.json','RESUME.execution.snapshot.md')],'self_excluded':True,'formal_increment':0})
print(json.dumps({'snapshot_ref':pin(OUT/'RESUME.execution.snapshot.json'),'manifest_ref':pin(OUT/'RESUME.execution.snapshot.manifest.json')},ensure_ascii=False))
