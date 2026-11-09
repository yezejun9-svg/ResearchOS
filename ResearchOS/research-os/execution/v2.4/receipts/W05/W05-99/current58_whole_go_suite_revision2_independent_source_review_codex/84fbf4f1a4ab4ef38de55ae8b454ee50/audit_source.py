import ast,difflib,hashlib,json,re
from pathlib import Path
O=Path(__file__).parent
D=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_revision2_source_preparation_codex/6e6556d821fe4457b23c6191fea96b1d')
checks=[];refs=[]
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ck(label,ok,detail=None):
 checks.append({'label':label,'passed':bool(ok),'detail':detail})
def read(p):
 refs.append(pin(p));return json.loads(p.read_bytes())
def ref(r):
 p=Path(r['path']);a=pin(p);ck('pin '+p.name,a['sha256']==r['sha256'] and a['bytes']==r['bytes']);refs.append(a);return p
def save(name,v):
 with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
h=read(D/'handoff.selected.json');m=read(ref(h['manifest_ref']))
member_key=next((k for k in ['entries','members','files'] if isinstance(m.get(k),list)),None)
ck('manifest member array exists',member_key is not None, list(m))
members=m[member_key];ck('manifest exact count51',len(members)==51 and m.get('count')==51)
for r in members:ref(r)
selected={k:ref(v) for k,v in h['selected_source_refs'].items()}
run=selected['runner'].read_text('utf-8');gate=selected['gate'].read_text('utf-8')
rt=ast.parse(run);gt=ast.parse(gate)
ck('runner and gate parsed AST only',True)
rconst={x.targets[0].id:ast.literal_eval(x.value) for x in rt.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and isinstance(x.value,(ast.Constant,ast.Dict,ast.List,ast.Tuple,ast.Set))}
ck('bootstrap gate exactSHA',rconst['GATE_SHA256']==pin(selected['gate'])['sha256'])
ck('bootstrap gate exactbytes',rconst['GATE_BYTES']==pin(selected['gate'])['bytes'])
ck('selected execution filename','with_name("'+selected['execution_contract'].name+'")' in run)
ck('selected gate filename','with_name("'+selected['gate'].name+'")' in run)
patch=ref(h['whole_inverse_patch_ref']).read_text('utf-8')
lines=patch.splitlines(keepends=True);starts=[i for i,x in enumerate(lines) if x.startswith('--- ')]
inverse=[]
for ix,start in enumerate(starts):
 stop=starts[ix+1] if ix+1<len(starts) else len(lines)
 before=Path(lines[start][4:].rstrip('\r\n'));after=Path(lines[start+1][4:].rstrip('\r\n'))
 old=before.read_bytes();new=after.read_bytes()
 expected=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile=str(before),tofile=str(after)))
 actual=''.join(lines[start:stop])
 ck('whole byte delta '+after.name,expected==actual)
 inverse.append({'before':pin(before),'after':pin(after),'exact_unified_diff_equal':expected==actual})
 for tree,name in [(ast.parse(old),before.name),(ast.parse(new),after.name)] if before.suffix=='.py' else []:pass
ck('four source inverse sections',len(inverse)==4)
report=read(ref(h['report_ref']));finite=read(ref(report['frozen_finite_contract_ref']))
execution=read(selected['execution_contract']);interface=read(selected['authority_interface'])
template=read(ref(h['root_source_members_template_ref']))
for x in template['members']:ref(x)
package_count=len(finite['packages'])
lanes=['BUILD_ONLY_NO_TOP_TEST','STATIC_NO_RESOURCE_SIGNAL_REVIEW','LOCAL_HTTP_FIXTURE_REVIEW','CONDITIONAL_SKIP_REVIEW','LOCAL_NATIVE_CHILD','LOCAL_NODE_MU_TLS']
calls=package_count;selected_ids=[]
for pkg in finite['packages']:
 for lane in lanes:
  entry=pkg['lanes'].get(lane)
  if entry is not None and (entry['windows_candidate_names'] or lane=='BUILD_ONLY_NO_TOP_TEST'):
   calls+=1;selected_ids+=entry.get('test_ids',[])
ck('58package frozen finite',package_count==58)
ck('all local planned calls136',calls==136,{'calls':calls,'selected_test_ids':len(selected_ids),'finite_keys':list(finite)})
matrix=[
 ('R01 overflow immediate lock','def note_overflow' in run and '"OUTPUT_OVERFLOW"' in run and 'with cause_lock:' in run,'runner158-167'),
 ('R01 raw EOF/partial separate','saw_eof[label]' in run and 'receipt[label + "_partial_raw"] = raw_pin' in run,'runner239-249'),
 ('R01 list and lane refuse incomplete','receipt.get("stdout_raw_complete")' in run and 'receipt.get("stderr_raw_complete")' in run,'runner265-298,332-339'),
 ('R01 launch wall recalc','wall = guarded_wall(budgets, deadline)\n        receipt["timeout_seconds"] = wall\n        proc = subprocess.Popen' in run,'runner195-201'),
 ('R01 sealed snapshot under lock','frozen_receipt = json.loads(json.dumps(receipt))' in run,'runner253-262'),
 ('R02 no attestation review backref','and "independent_review_ref" not in attestation' in gate,'gate147-181'),
 ('R02 scope pins both','scope.get("go_tree_attestation_review_ref")' in gate,'gate298-301'),
 ('R03 compile only verified raw','code = compile(raw, str(GATE), "exec"' in run and 'exec(code, gate.__dict__)' in run and 'importlib' not in run,'runner95-116'),
 ('R03 parents reparse','list(GATE.parents)[:8]' in run and 'GATE_BOOTSTRAP_PARENT_REPARSE' in run,'runner99-105'),
 ('R03 root actual cwd','Path.cwd().resolve(strict=True) == root' in gate and 'scope.get("worktree") == str(root)' in gate,'gate242-246,440-442'),
 ('R03 grants registration paths cwd','grant.get("cwd") == str(root)' in gate and 'registration.get("cwd") == str(root)' in gate and 'paths.get("cwd") == str(root)' in gate,'gate343-344,369-370,408-409')
]
for label,ok,where in matrix:ck(label,ok,where)
findings=[
 {'id':'GO58-R2-CONTRACT-ATTESTATION-VERSION','severity':'BLOCKER','path':str(selected['execution_contract']),'line':22,'actual':execution['go_hash_attestation_schema'],'consumer':{'path':str(selected['gate']),'line':147,'requires':'researchos.current58-frozen-go-hash-attestation.v2'},'why':'A Root producer following the selected execution contract emits v1, while the selected gate unconditionally requires v2. The attestation sequence itself is now acyclic; the published producer contract remains contradictory.','required_fix':'New immutable selected contract must specify v2 and preserve the native->attestation->independent review->scope order; update exact source manifest and linkage hashes. Do not mutate old attestation or add review backreference.'},
 {'id':'GO58-R2-AUTHORITY-SELECTED-PINS','severity':'BLOCKER','path':str(selected['authority_interface']),'lines':[124,164],'actual_gate_hash':interface['actual_cap_preflight']['gate_raw_sha256_before_compile'],'selected_gate_hash':pin(selected['gate'])['sha256'],'actual_final_source_files':interface['final_candidate_source_files'],'why':'The Root authority interface describes a different gate SHA and rev8 interface instead of selected rev9. Runtime runner bootstrap correctly pins selected gate, so following the interface can reject valid selected bytes or stage the wrong package.','required_fix':'New immutable interface must name/hash the selected gate and itself/current selected source list consistently. Keep raw-before-compile bootstrap and all source-manifest exact-pin checks.'}
]
save('audit.json',{'schema':'researchos.source-static-audit.v1','checks':checks,'checks_total':len(checks),'checks_passed':sum(x['passed'] for x in checks),'inverse':inverse,'input_refs':refs,'manifest_shape':{'member_key':member_key,'count':len(members)},'finite':{'packages':package_count,'all_local_planned_calls':calls,'selected_test_ids':len(selected_ids)},'candidate_imported':False,'candidate_executed':False})
save('review.json',{'schema':'researchos.current58-whole-go-revision-independent-source-review.v1','actor_id':'codex:/root/w05_merge_review','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':'REQUEST_CHANGES','stage':'SOURCE_PREPARATION_ONLY','requested_changes':findings,'selected_source_refs':h['selected_source_refs'],'audit_ref':pin(O/'audit.json'),'prior_review_ref':h['prior_non_author_review_ref'],'prior_R_disposition':{'R01':'Code paths close overflow/raw/lock and relaunch wall issues statically; no controls executed.','R02':'Attestation and independent review have a forward immutable order. Remaining selected contract/interface mismatches block Root composition. Other registration->source review->grant/auth dependencies are forward; root-source-members.template.root_registration_ref must remain NULL/omitted because registration pins source manifest.','R03':'Same verified gate raw is compiled, no pyc loader, ancestor reparse and canonical ROOT cwd checks present. Actual Root cap producer still absent.'},'positive_negative_controls':'STATIC_PATH_REVIEW_ONLY_NOT_RUN','still_open':['Actual Root cap/process/HTTP/model-zero producer, source review and exact authority are absent. JSON assertions or any-job membership are not real cap qualification.','Root source manifest must be sealed before registration; do not fill its root_registration_ref with the registration that hashes this manifest.','Actual curated Go directory/native hash attestation plus distinct review remain missing.','Fresh Root scope/lease/cwd/env/cache/resources/budgets/Windows outer Job+meters and exact plan review remain required.','58 actual roster probes and136 selected local plan calls are NOT_RUN;745 all-platform source test identifiers do not mean745 observed passes.','No whole suite/source/parent/formal acceptance.'], 'new_tool_diagnostic_origins':[pin(O/'origin.manifest-shape-4c43a8.json')],'new_nonzero_tool_failure_count':0,'inherited_author_origins_recounted':False,'candidate_imported_or_executed':False,'Go_calls':0,'model_calls':0,'source_acceptance':False,'whole58_test_suite_qualified':False,'formal_case_accepted_delta':0})
print(json.dumps({'review_ref':pin(O/'review.json'),'audit_ref':pin(O/'audit.json'),'checks':len(checks),'passed':sum(x['passed'] for x in checks),'findings':len(findings),'origin':pin(O/'origin.manifest-shape-4c43a8.json')},ensure_ascii=False))

