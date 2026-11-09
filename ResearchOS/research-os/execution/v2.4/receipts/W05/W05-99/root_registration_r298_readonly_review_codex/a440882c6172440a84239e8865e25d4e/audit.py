import pathlib,json,hashlib,subprocess,collections,datetime
OUT=pathlib.Path(__file__).resolve().parent; ROOT=pathlib.Path(__file__).resolve().parents[7]
RP=pathlib.Path('execution/v2.4/receipts/W05/W05-99'); IP=ROOT/RP/'integration_codex'
HP=RP/'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
WT=ROOT/'.local/worktrees/codex-w0599-host-configuration-handler'
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def put(n,v):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]; errors=[]; copies=[]
def check(p,expected=None,size=None):
 p=pathlib.Path(p)
 if not p.is_absolute():p=ROOT/p
 p=p.resolve()
 if not p.is_relative_to(ROOT):errors.append({'path':str(p),'error':'outside project'});return None
 if not p.is_file():errors.append({'path':str(p),'error':'missing'});return None
 b=p.read_bytes();d={'path':str(p),'sha256':sha(b),'bytes':len(b)}
 if expected is not None and d['sha256']!=expected:errors.append({'path':str(p),'error':'hash','expected':expected,'actual':d['sha256']})
 if size is not None and len(b)!=size:errors.append({'path':str(p),'error':'bytes'})
 checks.append(d);return d
def copy(p,name):
 r=check(p);b=pathlib.Path(p).read_bytes();q=OUT/'inputs'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);copies.append({'source':r,'snapshot':str(q.relative_to(OUT))})
canon=[ROOT/'execution/v2.4'/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
before={p:p.read_bytes() for p in canon};cp=j(canon[0]);ow=j(canon[1]);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=no'],cwd=ROOT)
(OUT/'git-status.raw').write_bytes(status)
for p in canon:copy(p,'canonical/'+p.name)
dirs=['cli-and-g1-original-failures-r298','cli-g1-failure-registration-corrected-r298','cli-g1-registration-reviewed-draft-r298']
inv=[]
for dn in dirs:
 d=IP/dn
 for p in sorted(d.iterdir()):
  if p.is_file():copy(p,dn+'/'+p.name)
 if (d/'invocation.json').exists():
  v=j(d/'invocation.json');check(d/'stdout.raw',v['stdout_sha256']);check(d/'stderr.raw',v['stderr_sha256']);inv.append({'namespace':dn,'exit':v['actual_exit'],'invocation':check(d/'invocation.json')})
draft=IP/dirs[2]/'register.py';check(draft,'53be1948cf81a61f8aa9178442d6c9ecf34fd2956519227f47fe30e7fa04da4b')
S=HP/'cli-first-cohort-failures-b5c03eb15d494ebfbb52eddbc36b010a/failure_origins.json';check(WT/S,'9467528fefec731e4c2563954997a87b9fa8621a4e2acbe2a93326b90a0d767a');s=j(WT/S);copy(WT/S,'supplement.json');check(ROOT/S,sha((WT/S).read_bytes()))
def walk_refs(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
   rel=pathlib.Path(v['path'])
   if rel.is_relative_to(HP):
    check(WT/rel,v['sha256'],v.get('bytes'));check(ROOT/rel,v['sha256'],v.get('bytes'))
  for x in v.values():walk_refs(x)
 elif isinstance(v,list):
  for x in v:walk_refs(x)
walk_refs(s)
coh=[]
for row in s['runs']:
 refs=row['refs'];resultp=ROOT/next(x['path'] for x in refs if x['path'].endswith('/result.json'));ip=ROOT/next(x['path'] for x in refs if x['path'].endswith('/command.invocation.json'))
 result=j(resultp);iv=j(ip);bef=next(x for x in refs if x['path'].endswith('/source.before.json'));aft=next(x for x in refs if x['path'].endswith('/source.after.json'))
 coh.append({'origin':row['origin'],'kind':result['kind'],'exit':result['exit'],'invocation_exit':iv['exit'],'input_count':result['input_count'],'drift':result['source_drift'],'stored_vectors_same':bef['sha256']==aft['sha256'],'test_events':result.get('test_events')})
 if result['kind']=='contract':
  raw=ROOT/next(x['path'] for x in refs if x['path'].endswith('/command.stdout'));report=json.loads(raw.read_bytes());copy(raw,'contract.stdout.original.json');contractrawref=check(raw)
report=s['contract_actual_report']; rawreport=j(OUT/'inputs/contract.stdout.original.json')
cor=WT/HP/'contract-count-correction-d344de6ea1134acb8c8dcaa56fccb510/correction.json';check(cor,'5dd620972f04876158108d0a29be1c9075ab4f1b39d7d03e0a44186b5443e112');copy(cor,'count-correction.json');corj=j(cor);check(ROOT/corj['original_stdout_ref']['path'],corj['original_stdout_ref']['sha256'])
copy(ROOT/'tests/runtime/cli_contract/main.go','contract-report-producer.go')
ids=report['assertion_ids'];fails=report['failures']
reportaudit={'embedded_report_equals_original_stdout':report==rawreport,'status':report['status'],'assertions_type':type(report['assertions']).__name__,'assertions':report['assertions'],'success_check_ids_count':len(ids),'success_ids_unique':len(set(ids))==len(ids),'failure_entries':len(fails),'failure_ids_unique':len(set(x['id'] for x in fails))==len(fails),'success_failure_overlap':sorted(set(ids)&set(x['id'] for x in fails)),'not_verified':report['not_verified'],'failure_ids_match_correction':[x['id'] for x in fails]==corj['failure_ids'],'no_suite_pass_total_inferred':True,'original_stdout_ref':contractrawref}
G1=ROOT/RP/'provider_whole9_g1_root_executor_codex/093a934167674f6ca02e0a09dc5d5010'
for p in sorted(G1.iterdir()):
 if p.is_file():check(p)
alias=j(G1/'node-resolve-alias.invocation.json')
for k in ['stdout','stderr']:check(G1/('node-resolve-alias.'+k+'.raw'),alias[k+'_sha256'])
outer=IP/'provider-g1-and-f08-review-r297';oi=j(outer/'g1.outer.invocation.json');check(outer/'g1.outer.invocation.json')
for k in ['stdout','stderr']:check(outer/('g1.outer.'+k+'.raw'),oi[k+'_sha256'])
f=j(G1/'failure.origin.json');check(G1/'failure.origin.json','b1c8179a05d5af8d830e519a235d5d0453ea96bfeb4f8097f4a38f37c26f290f')
for p,e in f['candidate9_current'].items():check(ROOT/p,e['sha256'],e['bytes'])
v1=j(G1/'inputs.before.json');v2=j(G1/'inputs.failure.current.json');pkg=ROOT/'third_party/mu/node_modules/@earendil-works/pi-ai/package.json';check(pkg);pk=j(pkg)
g1audit={'before_after_saved_vectors_equal':v1==v2,'stored_vector_count':len(v1),'current47300file_contents_independently_rehashed':False,'current_source9_checked':9,'outer_exit':oi['actual_exit'],'child_exit':alias['actual_exit'],'alias_error_present':b'ERR_PACKAGE_PATH_NOT_EXPORTED' in (G1/'node-resolve-alias.stderr.raw').read_bytes(),'actualargv':alias['actualargv'],'sdk_version':pk['version'],'exports':pk['exports']['.'],'same_parent_child_attempt_count_once':True,'bundle_go_js_not_run_per_failure_scope':True}
pre=ROOT/RP/'handler38_cli_preliminary_review_codex/acf3406cef3a4fe8b20e0ee340bafc55';pm=j(pre/'manifest.json');check(pre/'manifest.json','dcbf50ea41cf11d1945ad4f0986400e0ac4486ffcb1f76c1d48e9f55ebd04d51')
for e in pm['files']:check(pre/e['path'],e['sha256'],e.get('bytes'))
check(pre/'review.json','1ffe82710a12218cec54cc6afdf9cf910b1c1074eaaf74d406248732ef28aa43');check(pre/'handoff.json','8c8090c75644bf1c114b056d0cdbf4f87144e25f68c059b37c1d4aa0566376d1');check(pre/'failure_origins.json')
origins=['W05-99/provider-whole9-g1/093a934167674f6ca02e0a09dc5d5010']+['W05-99/handler-cli-first/'+x['origin'] for x in s['runs']]+['W05-99/handler-cli-first/tool-'+x['chunk'] for x in s['new_tool_origins']]+['W05-99/handler38-cli-preliminary/tool-7f01c3']+['W05-99/root-failure-registration/tool-'+x for x in ['933bc6','32f688','6ec8e0']]
existing={x.get('origin_key') for x in cp['failure_counters']}
counter={'before':len(cp['failure_counters']),'draft_new_origins':origins,'unique_count':len(set(origins)),'already_present':sorted(set(origins)&existing),'draft_expected_after':len(cp['failure_counters'])+len(set(origins)-existing),'same_registration_chain':{'failed_attempts':2,'chunks':['933bc6','6ec8e0'],'display_32f688_separate':True},'additional_current_reviewer_origin':{'chunk':'176c1f','outer_exit':1,'cause':'readonly exploratory script attempted slicing report.assertions int; TypeError int not subscriptable','original_tool_locator':'functions.exec chunk176c1f','separate_from_two_root_attempts':True,'not_in_current_draft10':True},'if_root_imports_this_new_review_origin_total':len(cp['failure_counters'])+len(set(origins)-existing)+1}
put('verified_fields.json',{'cohorts':coh,'contract':reportaudit,'G1':g1audit,'preliminary_manifest_count':len(pm['files']),'canonical':{'cp':cp['revision'],'ow':ow['revision'],'failure_count':len(cp['failure_counters']),'head':head,'git_status_lines':len(status.splitlines()),'old_deletions':sum(x[:2]==b' D' for x in status.splitlines())},'reference_checks':checks,'reference_errors':errors,'limits':['No SQL opened, DB ref hashed as opaque bytes only.','Stored source vector equality checked; does not recreate original time or separately hash all47300 current files.','No corrected source author green or future G1 evidence accepted.']})
put('counter_origins.json',counter)
findings=[
 {'id':'R298-01','status':'FIXED_IN_DRAFT','detail':'按kind读取Go test_events；contract没有该字段。现report69成功ID、26failure entries、0not_verified与原stdout及producer一致；原29口述已immutable勘误，不能声称整组69PASS。'},
 {'id':'R298-02','status':'FIXED_IN_DRAFT','detail':'新草案10个unique origins得到302->312，并保留Root两个登记失败chain2。每个父/子/叶按原invocation一因计一次，32f688独立显示错误；原unknown/nonverified不猜总PASS。'},
 {'id':'R298-03','status':'MUST_RESOLVE_BEFORE_EXECUTION','detail':'本独审新增176c1f真实只读TypeError1不在当前10。Root可明确defer到下一次登记（本次仍312并挂pending），或导入成为313并同步所有record/integrity/handoff计数；不能盲用312同时声称已导入全部新origin。'},
 {'id':'R298-04','status':'MUST_RESOLVE_BEFORE_EXECUTION','detail':'当前两canonical文件逐个os.replace，若第一checkpoint完成而第二ownership创建/replace失败，会留298/125且run.exit1；没有prepare双payload/持久intent/partial phase或恢复分支。本次正是失败修复登记，建议执行前生成两份desired bytes/hash与before refs并留immutable intent；异常封存阶段，Root只在live值仍等原值/本事务desired值时按明确计划完成或撤回自身写，不覆盖外部变化。严禁失败后直接第三份同baseline盲跑。'},
 {'id':'R298-05','status':'EXECUTION_PRECONDITION','detail':'assert承担全部hash/CAS/计数门：实际执行必须固定无Python优化（sys.flags.optimize==0，PYTHONOPTIMIZE未启用），或改不可省略的显式异常。此处不运行脚本，不能确认未来环境。'},
 {'id':'R298-06','status':'EXECUTION_PRECONDITION','detail':'须在全只读验证/desired生成后，再一次性CAS全部4metadata原字节、精确HEAD及原status字节，并在每次replace前核其他canonical仍为预期。step_state/commands不写。成功后重读两revision、原302前缀、去重origin数及2链，再写成功marker；现仅检查未写2文件不足。'},
 {'id':'R298-07','status':'CLARIFY_CURRENT_STATUS','detail':'G1 audit只证明首次CJS准备失败，work_in_progress/ownership固定FIRST_FAILURE和repair-pending文字不能覆盖Root后来独立授权/执行的ESM新attempt。若另有current G1阶段，原失败作为历史增量登记，当前状态引用真实新scope；本次不重跑/不自接受G1。'},
 {'id':'R298-08','status':'REFERENCE_COMPLETENESS','detail':'原ref()先hash后另read存在时间窗；冻结输入应缓存同次已hash bytes用于parse/copy，copied目标若存在核同字节。第二登记stdout也应按invocation stdout_sha256验证（本独审已核）。新增勘误应parse并核原stdout/report字段/IDs，不只hash copy。所有解析/manifest/source checks在canonical写前完成。'}]
put('findings.json',findings)
put('failure_origins.json',{'tooling':[counter['additional_current_reviewer_origin']],'expected_nonzero_queries':[{'chunk':'07c654','exit':1,'reason':'git diff --no-index differences expected, not execution failure'}],'registration_executions':0,'product_executions':0})
after={p:sha(p.read_bytes()) for p in canon};put('read_audit.json',{'copies':copies,'canonical_before':[{'path':str(p),'sha256':sha(b),'bytes':len(b)} for p,b in before.items()],'canonical_after':[{'path':str(p),'sha256':v} for p,v in after.items()],'canonical_unchanged':all(after[p]==sha(b) for p,b in before.items()),'registered_scripts_executed':False,'tests_SQL_HTTP_Node_model':0})
put('review.json',{'decision':'DATA_ASSUMPTIONS_VERIFIED_DRAFT_NEEDS_FINAL_EXECUTION_GUARDS','reviewer':'/root/w05_merge_review','reviewed_draft':check(draft),'findings':findings,'counts':counter,'all_existing_references_checked':not errors,'reference_check_count':len(checks),'reference_errors':errors,'canonical_unchanged':all(after[p]==sha(b) for p,b in before.items()),'executable_registration_ready':False,'next':'Root封存一次精确修案（计数/当前状态/双写intent与失败恢复/无优化/最终CAS），复用此次引用验证，不执行旧2脚本或新草案；旧失败不覆盖。','formal_increment':0})
files=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
put('manifest.json',{'listed_count':len(files),'files':files})
put('handoff.json',{'decision':'DATA_ASSUMPTIONS_VERIFIED_DRAFT_NEEDS_FINAL_EXECUTION_GUARDS','review':check(OUT/'review.json'),'manifest':check(OUT/'manifest.json'),'namespace':str(OUT),'canonical_mutations':0})
print(json.dumps({'review':check(OUT/'review.json'),'manifest':check(OUT/'manifest.json'),'handoff':check(OUT/'handoff.json'),'errors':errors,'counter_total_draft':counter['draft_expected_after'],'with_new_reviewer_tool':counter['if_root_imports_this_new_review_origin_total'],'canonical_unchanged':all(after[p]==sha(b) for p,b in before.items())},ensure_ascii=True))
