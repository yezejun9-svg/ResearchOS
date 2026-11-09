"""Seal bounded read-only W09 gaps; no implementation or execution authority."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

N=Path(__file__).resolve().parent;R=N.parents[5];W=N.parent;P=R.parent/'ResearchOS_Implementation_Package_v2.4'
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def module(p):
 m=types.ModuleType('gap_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m

def main():
 inv=read(N/'inventory.json');receipts=sorted(N.glob('guarded-read-*.json'));allrefs=[]
 for p in receipts:allrefs.extend(read(p)['inputs'])
 ig=read(N/'inventory.guard.closed.json')
 for cleanup in ig.values():allrefs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in cleanup['entries'])
 c19=W/'w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
 reg=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
 qualified=W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd'
 oldcontroller=W/'finite_controller_preparation_revision_codex/b9b9b105f8e74cc4a7b39a0c059914b8'
 native_report=next(x['report_ref'] for x in inv['existing_Main_native_reports'] if x['source21_current'])
 native_tool=pin(Path(native_report['path']).parent/'native-tool-run.json')
 allrefs += [pin(p) for p in [*receipts,N/'inventory.json',N/'inventory.guard.closed.json',Path(__file__),qualified/'actual-decision.final.json',qualified/'consumer-summary.json',reg/'register_cp370.source.py',reg/'ROOT_BUILDER_CONTRACT.source.md',reg/'HDF.json',reg/'MF.json']]
 allrefs += [native_tool,pin(N/'failure-ec18d2.actual-host.raw.jsonl'),pin(N/'failure-ec18d2.actual-host.binding.json')]
 unique={}
 for ref in allrefs:
  key=ref['path'].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
 refs=list(unique.values())
 G=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
 spec=importlib.util.spec_from_file_location('gap_final_guard',G);gm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=gm;spec.loader.exec_module(gm)
 guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 checks=[]
 def check(name,ok,detail=None):
  assert ok,name
  checks.append(dict(name=name,passed=True,detail=detail))
 try:
  guard.acquire(refs)
  current=[pin(r['path']) for r in inv['current_canonical_refs']]
  check('current CP370 OW174 SS and CM39 unchanged',current==inv['current_canonical_refs'])
  check('frozen dependencies all accepted',set(inv['dependency_statuses'].values())=={'ACCEPTED'})
  check('only exact C19 Native Source21 current',len(inv['existing_Main_native_reports'])==7 and len([x for x in inv['existing_Main_native_reports'] if x['source21_current']])==1 and read(native_report['path'])['case_id']=='C19')
  check('current formal zero and Root capture authority absent',inv['current_formal_count']==0 and inv['root_capture_authority'] is None and inv['fixed_root_capture_index_exists'] is False)
  api=module(R/'execution/v2.4/formal_case_index.py')
  profile=module(R/'execution/v2.4/formal_profile_w09.py')
  reader=api.Reader(R)
  tool_relative=Path(native_tool['path']).relative_to(R).as_posix()
  path_error=None
  try:reader.ref({'path':tool_relative,'sha256':native_tool['sha256']},profile.SOURCE_PREFIX)
  except api.InvalidEvidence as exc:path_error=exc.code
  check('real C19 Native tool rejected by current profile SOURCE_PREFIX',path_error=='PATH_SCOPE',dict(actual_tool_ref=native_tool,profile_expected_prefix=profile.SOURCE_PREFIX,actual_prefix=profile.NATIVE_PREFIX,expected_control_error=path_error))
  routes=[]
  for row in inv['routes']:
   selector='check_id' if row['check_id'] else 'case_id';identifier=row['check_id'] or row['case_id'];entry=row['registry_entry']
   bound='W09' in entry['selectors'].get('task_id',[]) and identifier in entry['selectors'].get(selector,[])
   routes.append({k:v for k,v in row.items() if k!='registry_entry'}|dict(current_registry_binding=bound,actual_current_C19_qualified=row['case_id']=='C19',native_required_scope='LIVE_WINDOWS_LOCAL' if row['check_id']=='W09-G02' else 'FIXTURE_IMPLEMENTED_SERVICE'))
  check('CM39 exactly two C19 routes enabled four missing',sum(x['current_registry_binding'] for x in routes)==2 and all(x['current_registry_binding']==(x['case_id']=='C19') for x in routes))
  source=Path(R/'execution/v2.4/formal_profile_w09.py').read_text(encoding='utf-8')
  check('profile current whole registry equality and exact tool output link present','receipt.get("registered_command_revision") == pinned.get(registry_path)' in source and 'output.get("native_tool_run_ref") == row["native_tool_run_ref"]["path"]' in source)
  mode_path=W/'main_c19_native_actual_independent_review_codex/review-1a12035-v2/test-research-fixture.mode-decision.json'
  mode=read(mode_path);actual_owner=read(reg/'owner-document.root.json')
  check('actual Root producer and dispatcher owner conflict with current three-actor rule',mode['producer_id']=='codex:/root' and actual_owner['owner_id']==actual_owner['selected_worker_id']=='codex:/root' and 'len({executor.casefold(), reviewer.casefold(), "codex:/root"}) == 3' in source)
  consumer=read(qualified/'consumer-summary.json')
  check('qualified pair unchanged and nonformal',read(qualified/'actual-decision.final.json')['decision']=='ACTUAL_MAIN_C19_TWO_CONSUMERS_COMPONENT_FIXTURE_VERIFIED' and len(consumer['consumers'])==2 and all(x['mode']=='FIXTURE' and x['formal_acceptance'] is False for x in consumer['consumers']))
  check('old finite49 source not Main-ready',inv['legacy_finite_controller']['spec_scalar_fields']['not_current_combined_Main'] is True and inv['legacy_finite_controller']['spec_scalar_fields']['combined_source_closure_ref'] is None and inv['legacy_finite_controller']['spec_scalar_fields']['execution_authorized'] is False)
  for p in receipts:
   gr=read(p)['source_guard'];check('guarded read released '+p.name,gr['closed'] is True and gr['retained_handles_count']==0 and gr['errors']==[])
  for ref in refs:check('held current input '+ref['path'],pin(ref['path'])==ref)
 finally:cleanup=guard.close()
 check('final finite Source guard released0',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 guardref=save('source-guard.final.closed.json',cleanup)
 checkref=save('bounded-checks.json',dict(checks=checks,count=len(checks),expected_PATH_SCOPE_control_caught=True,product_or_dispatcher_or_producer_or_SQLite_or_network_executed=False))
 source_inputs={
  'Main_formal_case_index':pin(R/'execution/v2.4/formal_case_index.py'),
  'Main_formal_profile':pin(R/'execution/v2.4/formal_profile_w09.py'),
  'Main_native_producer':pin(R/'ops/ci/retrieval.py'),
  'Main_router':pin(R/'ops/ci/w09_formal_router.py'),
  'Main_closure':pin(R/'ops/ci/w09_evidence_closure.py'),
  'CM39':current[3],
  'frozen_plan':pin(P/'contracts/execution.plan.json'),
  'frozen_card':pin(P/'tasks/steps/W09-99.md'),
  'frozen_acceptance':pin(P/'contracts/acceptance.json'),
  'C19_reusable_actual_decision':pin(qualified/'actual-decision.final.json'),
  'C19_producer_HDF':pin(c19/'HDF.json'),
  'C19_producer_MF':pin(c19/'MF.json'),
  'C19_producer_contract':pin(c19/'root-calling-contract.json'),
  'C19_runtime_base':pin(c19/'main_c19_runtime.source.py'),
  'C19_launcher_base':pin(c19/'main_c19_launcher.source.py'),
  'C19_prepare_base':pin(c19/'prepare_main_c19.actual_owned.py'),
  'C19_run_base':pin(c19/'run_main_c19.actual_owned.py'),
  'C19_choice_base':pin(c19/'source.choice.json'),
  'registration_mechanism_reference':pin(reg/'register_cp370.source.py'),
  'registration_contract_reference':pin(reg/'ROOT_BUILDER_CONTRACT.source.md'),
  'old_finite49_not_current_Main':pin(oldcontroller/'spec.v2.final.json'),
  'current_C19_native_report':native_report,
  'current_C19_native_tool':native_tool,
  'C19_actual_mode_actor_evidence':pin(mode_path),
  'C19_actual_dispatcher_owner':pin(reg/'owner-document.root.json'),
 }
 gaps=[
  dict(id='GAP_PROFILE_REUSE',severity='BLOCKING_SOURCE',summary='Three current profile compatibility blockers: Native tool prefix rejects real C19 path; new registry hash rejects CM39 C19 receipts; current three-distinct-actors rule excludes actual Root Native/dispatcher executor.',evidence=[dict(file_ref=source_inputs['Main_formal_profile'],lines=[20,304,421,459,492,724,725,727]),dict(file_ref=source_inputs['Main_formal_case_index'],lines=[143,150,151]),dict(file_ref=native_tool,lines=[]),dict(file_ref=source_inputs['C19_actual_mode_actor_evidence'],json_pointers=['/producer_id','/reviewer_id']),dict(file_ref=source_inputs['C19_actual_dispatcher_owner'],json_pointers=['/owner_id','/selected_worker_id'])],required_change='Prepare minimal profile compatibility Source: permit canonical same-run Native tool path; pin actual historical CM39 bytes and Root-approved transition/route-equivalence evidence per reused C19 receipt. Explicitly bind source author, actual Native/dispatcher executor, evidence assembler, independent verifier and Root issuer to their real evidence. Preserve Root as actual C19 producer/executor. Current context executor is copied into GLOBAL/review/issuance but not explicitly joined to mode.producer_id; that missing join does not authorize attributing Root execution to the Source author. If the current three-distinct-actors policy is retained unchanged, formal reuse is blocked; resolve role/schema policy explicitly under independent Source review. Never replace old actors or CM39 hashes.'),
  dict(id='GAP_FOUR_ROUTE_REGISTRATION',severity='BLOCKING_SOURCE',summary='CM39 leaves retrieval G01/G02/A06 and security W09/A06 unbound; security still points to Go W17 handler.',evidence=[dict(file_ref=current[3],json_pointers=['/commands/test.retrieval/selectors','/commands/test.security'])],required_change='Prepare exact four-route registration delta: preserve existing W09-01/W08/W17 behavior, add retrieval G01/G02/A06 selectors; change security executable to locked Python W09 router with required Native/mode env and W09/A06 selectors while retaining PRESERVED W17 behavior. Freeze CM39 archive and prove unchanged effective C19 argv/tool/env/pointer/selector interpretation.'),
  dict(id='GAP_THREE_MAIN_NATIVE_PACKETS',severity='BLOCKING_SOURCE_THEN_ACTUAL',summary='Main retrieval.py implements selectors, but only current C19 has current Source21 Native evidence; six other Main reports are stale17-source artifacts. Existing C19 two-stage wrapper is fixed to C19, used run paths, one domain package and351 package roster.',evidence=[dict(file_ref=source_inputs['Main_native_producer'],lines=[16,28,33,37,135,145,178,190,191,232]),dict(file_ref=source_inputs['C19_runtime_base'],lines=[90,155,168,175,329,346,348,355,359,401])],required_change='Create fresh Main-only producer Source for exactly three selectors G01/G02/A06, each once, fresh run/output/receipt/scratch directories; preserve Main Source21. Adapt finite guarded compiler closure for adapters/retrieval plus internal/domain rather than reusing C19 351 constant; do not directly rerun old C19 launcher or generic49 controller.'),
  dict(id='GAP_MODES_AND_FOUR_CONSUMERS',severity='ACTUAL_AFTER_SOURCE',summary='G01 FIXTURE and G02 LIVE_WINDOWS each need own later independent mode qualification; one A06 FIXTURE Native packet may feed retrieval/security but each route requires a distinct mode decision. Four new dispatcher receipts are required.',evidence=[dict(file_ref=source_inputs['Main_closure'],lines=[565,572,604,612,625,636]),dict(file_ref=source_inputs['Main_formal_profile'],lines=[299,313,314,315,388,393])],required_change='Preserve complete raw/owned evidence; G02 bind same-run Windows11 x64 host and junction witnesses, allowlist, command, output pin, Source21 and locked Go. Maintain each run TEMP/TMP at consumer verification; do not rerun existing C19 consumers.'),
  dict(id='GAP_FORMAL_ROOT_AND_GLOBAL',severity='FORMAL_FINAL_OPEN',summary='Current formal0, all four predecessor cards ACCEPTED, W09-99 row absent, Root capture authority slot and fixed index absent. Six-route context, two GLOBAL four-file groups, independent formal review and actual Root-delivery capture/issuance remain required.',evidence=[dict(file_ref=source_inputs['Main_formal_profile'],lines=[473,479,491,519,552,557,576,583,596,719,724,744,765,779,795])],required_change='After all six actual routes close, build current version/source coverage vector and C19/A06 run-receipt/version-manifest/command-receipt/assertion-results. Independent review must have8 verdict IDs and no missing/failed; Root captures actual delivery three raw lines and registers fixed index before issuance/owner acceptance. Do not equate Source, mode qualification, or component closure with FormalCaseAccepted.'),
 ]
 producer_jobs=[]
 for key in ('W09-G01','W09-G02','A06'):
  row=next(x for x in routes if (x['check_id'] or x['case_id'])==key)
  producer_jobs.append(dict(selector=dict(task_id='W09',check_id=row['check_id'],case_id=row['case_id']),mode=row['mode'],native_scope=row['native_required_scope'],selected_tests=row['selected_tests'],expected_native_ids=row['native_ids'],packages=row['packages'],native_run_count=1,go_list_argv_suffix=['list','-test','-deps','-compiled','-export','-json',*row['packages']],go_test_argv_suffix=['test','-count=1','-json','-run','^(?:'+'|'.join(row['selected_tests'])+')$',*row['packages']],fresh_path_contract=dict(run_id='fresh unique32hex per selector',output_root='research-os/execution/receipts/W09/retrieval/run-<run_id>',scratch_root='research-os/.local/<new-source-owned-selector-run-id>',receipt_root='<new Source namespace>/actual/<selector>/<run_id>'),required_outputs=['prepare.ready.json','compiler-input-list.stdout.raw','compiler-input-list.stderr.raw','actual-compiler-input-inventory.json','launcher.permit.json','launcher.started.json','launcher.closed.json','report.json','native-tool-run.json','go-test.stdout.jsonl','go-test.stderr.txt','owned/**','native-packet.public-index.json','validation.closed.json','complete Root original tool IO and actual host binding']))
 next_tasks=[
  dict(id='SOURCE_PROFILE_AND_REGISTRATION_COMPATIBILITY',priority=1,existing_inputs=[source_inputs[k] for k in ('Main_formal_profile','Main_formal_case_index','CM39','frozen_plan','Main_router','C19_reusable_actual_decision','current_C19_native_report','current_C19_native_tool','C19_actual_mode_actor_evidence','C19_actual_dispatcher_owner','registration_mechanism_reference','registration_contract_reference')],proposed_outputs=['formal_profile_w09.after.py','formal_profile_w09.forward.diff','formal_profile_w09.inverse.diff','commands.after.json','commands.forward.diff','commands.inverse.diff','historical-CM39-archive.contract.json','execution-actor-role.contract.json','registration.source.py','ROOT_CALLING_CONTRACT.source.md','bounded-controls.json','HDF.json','MF.json'],acceptance='Pure checks prove current C19 exact historical record remains unchanged and qualified after controlled four-route addition; wrong CM39 archive, changed effective C19 tool/argv/env, wrong Native run/path, forged registry transition and relabeled actual executor reject. Explicit role schema retains Root Native/dispatcher executor and requires independently evidenced non-author/non-executor verifier; Root issuer is a separate role even when same actor, not a fabricated third executor. If three-distinct actor rule remains mandatory, report formal reuse blocked rather than relabel. Old W17 behavior remains preserved. Source review before Root adoption.'),
  dict(id='SOURCE_THREE_SELECTOR_MAIN_PRODUCER',priority=2,existing_inputs=[source_inputs[k] for k in ('Main_native_producer','Main_router','Main_closure','C19_producer_HDF','C19_producer_MF','C19_producer_contract','C19_runtime_base','C19_launcher_base','C19_prepare_base','C19_run_base','C19_choice_base','frozen_plan','registration_mechanism_reference')],source21=inv['Main_source21'],proposed_outputs=['full_w09_runtime.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py','source.choice.json','compiler-source-blueprint.json','ROOT_CALLING_CONTRACT.source.md','source-controls.json','HDF.json','MF.json'],jobs=producer_jobs,acceptance='No Main21 changes; no actual producer during Source preparation. Finite Source guards and unnamed Job lifecycle mirror accepted C19 mechanism; exact current scope/owner/worker and vectors required later.0 independent C19 selector runs and0 reruns of its two dispatchers. Full G01 own5-test roster necessarily includes C19 subtests; never splice old C19 report into G01.'),
  dict(id='SOURCE_FOUR_CONSUMER_AND_FORMAL_ASSEMBLY',priority=3,existing_inputs=[source_inputs[k] for k in ('Main_formal_profile','Main_formal_case_index','Main_router','Main_closure','frozen_plan','frozen_acceptance','C19_reusable_actual_decision')],proposed_outputs=['four_remaining_consumers.source.py','six-route-context.contract.json','GLOBAL-C19.contract.json','GLOBAL-A06.contract.json','Root-capture-registration.contract.json','HDF.json','MF.json'],acceptance='Consume3 new Native packets with4 new exact dispatcher routes, reuse2 immutable C19 receipts under explicit historical compatibility. Full formal evidence has all6 routes and both GLOBAL groups; root delivery authority is actual later evidence, never self-generated approval.'),
 ]
 report=dict(schema='researchos.w09-full-native-source-gap-report.v1',decision='GAPS_IDENTIFIED_NEXT_SOURCE_CONTRACT_READY',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',reviewed_at=datetime.now(timezone.utc).isoformat(),scope='READ_ONLY_SOURCE_GAP_REVIEW',source_inputs=source_inputs,current_canonical_refs=current,dependency_statuses=inv['dependency_statuses'],route_matrix=routes,existing_native_report_inventory_ref=pin(N/'inventory.json'),gaps=gaps,next_source_tasks=next_tasks,Source_is_actual=False,Source_is_formal=False,Main_Canon_Scope_counter_parent_status_written=False,Native_SQLite_dispatcher_model_network_executed=False,CURRENT_formal=0,ParentW09=False,WholeGoalDONE=False,original_diagnostic=dict(Root_assigned_ordinal=1011,chunk_id='ec18d2',actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,guard_acquired=False,guard_closed_claim=None,actual_host_capture_ref=pin(N/'failure-ec18d2.actual-host.raw.jsonl'),actual_host_binding_ref=pin(N/'failure-ec18d2.actual-host.binding.json')),Root_next_ordinal_reported_by_parent=1013,bounded_checks_ref=checkref,source_guard_ref=guardref,all_read_refs=refs)
 rr=save('Source-gap-report.json',report)
 text='''# W09 完整 Native 与正式链缺口\n\n结论：Main `ops/ci/retrieval.py` 已具备 G01/G02/A06 生产逻辑；没有可直接复用的、当前 Main 的完整 Root producer 包。下一步先完成 profile/registry 兼容 Source，并基于已接受 C19 两阶段机制编写三个 selector 的新 Source 包。\n\n| 路由 | Native / 模式 | 当前缺口 |\n|---|---|---|\n| retrieval G01 | 5 tests / 8 IDs / FIXTURE | CM39未登记；无当前 Source21 Native |\n| retrieval G02 | 8 tests / 7 IDs / LIVE_WINDOWS | CM39未登记；无当前 Native与host/junction资格 |\n| research.fixture C19 | 2 tests / 5 Native IDs / FIXTURE | 实际已合格，保留不重跑；正式profile兼容待修 |\n| retrieval C19 | 同一 C19 Native / 独立route模式 | 实际已合格，保留不重跑；正式profile兼容待修 |\n| retrieval A06 | 8 tests / 7 IDs / FIXTURE | CM39未登记；无当前 Native |\n| security A06 | 可共享上行A06 Native，独立route模式 | 仍为Go/W17处理器，须登记Python router与环境 |\n\n## 会阻止复用现 C19 的两个源码事实\n\n1. `formal_profile_w09.py:304` 把 Native tool-run 限于 `execution/v2.4/receipts/W09/`，真实两次消费者引用却是 `execution/receipts/W09/.../native-tool-run.json`。有限纯 Reader 控制得到 `PATH_SCOPE`。复制 tool-run 不能解决，因为 line459要求实际dispatcher stdout与context引用同一路径。\n2. line421要求每次dispatcher记录的整份CM哈希等于当前CM。四缺路登记将改变CM39哈希，旧C19回执便不再满足。必须用真实CM39归档、Root登记的变化链及当前等效C19 binding核验兼容，不能改写旧回执、借新hash或普遍放宽历史receipt。\n\n## 最小生产 Source 范围\n\n三个新selector，各一次：G01、G02、A06。G01的完整5-test roster包含两个C19子测试，这是G01自身新证据；独立C19 selector和其两次dispatcher保持0重跑。G02与A06虽然都有7 IDs，但check/case/scope不同，不能共享一份伪造改头报告。A06两个消费者可以共享一份A06 Native，但各自需要模式决定。\n\n沿用已接受的C19 runtime/launcher/prepare/run作为机制输入，保持 Main Source21字节不变。新choice需要独立run/receipt/temp/profile/gocache，Main产物固定到各自 `run-<id>`；完整调用包是 `./adapters/retrieval` 加 `./internal/domain`，不能继承C19的单包、351-roster和已用输出路径。老finite49包明确 `not_current_combined_Main=true`、未授权且缺combined/runtime/compilation闭包，不能拿来直接运行本任务。\n\n## 正式接受仍缺\n\n四个依赖卡当前均ACCEPTED；CURRENT formal=0。Root capture Canon槽位和固定index不存在。还需六路当前context、C19/A06各四份GLOBAL文件、独立8项verdict、真实Root消息三行capture与index注册、issuance及owner接受。Source/Native/模式/组件资格都不等于FormalCaseAccepted。\n\n精确输入三键refs、每个新job的argv/selector/IDs/输出，以及三个后续Source任务的交付合同见 `Source-gap-report.json`。本轮没有运行产品、SQLite、Native、dispatcher、模型或网络，也没有修改Main/Canon/Scope/计数。\n'''
 text += '\n## 执行身份的第三个兼容前置\n\n实际C19 mode决定写明 `producer_id=codex:/root`，两dispatcher的owner与selected_worker也均为Root。profile line492把GLOBAL executor等同context executor；line724/725/727又要求executor、reviewer、Root三个不同身份。Source作者不能仅因写了launcher就被改称实际执行者。当前代码未把context executor绑定mode.producer_id，这一缺口不能用于绕过事实。\n\n兼容Source必须明确并按原始调用、Scope、模式回执绑定Source作者、实际Native/dispatcher执行者、证据assembler、独立verifier、Rootissuer；保留Root实际执行身份。若不调整三身份政策，现C19正式复用仍阻塞。任何角色/schema调整须独立Source审查，不得改写既有producer_id、替换actor字符串或自签正式接受。\n'
 with (N/'Source-gap-report.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
 md=pin(N/'Source-gap-report.md')
 mf=save('MF.json',dict(schema='researchos.w09-full-native-source-gap-manifest.v1',members=[rr,md,checkref,guardref,pin(N/'inventory.json'),pin(N/'inventory.guard.closed.json'),pin(N/'inventory.py'),pin(N/'read_batch.py'),pin(__file__),pin(N/'failure-ec18d2.actual-host.raw.jsonl'),pin(N/'failure-ec18d2.actual-host.binding.json'),*[pin(p) for p in receipts]],source_input_refs=source_inputs))
 hdf=save('HDF.json',dict(schema='researchos.w09-full-native-source-gap-handoff.v1',decision=report['decision'],actor_id=report['actor_id'],actor_role=report['actor_role'],manifest_ref=mf,source_gap_report_ref=rr,readable_report_ref=md,checks_ref=checkref,source_guard_ref=guardref,read_refs_count=len(refs),checks=len(checks),all_guards_closed=True,retained_handles_count=0,next_source_tasks=[x['id'] for x in next_tasks],CURRENT_formal=0,ParentW09=False,WholeGoalDONE=False,Source_only=True,Main_Canon_written=False,actual_execution=False,STOP=True,FINAL=True))
 for ref in (hdf,mf,rr):assert pin(ref['path'])==ref
 print(json.dumps(dict(HDF=hdf,MF=mf,report=rr,checks=len(checks),guard_refs=len(refs),expected_path_scope_control='PASS',new_original_failure_ordinal=1011),ensure_ascii=False))

if __name__=='__main__':main()
