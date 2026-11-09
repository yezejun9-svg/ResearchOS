import pathlib,json,hashlib,datetime
O=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01'
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321'
def ref(p):
 p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(pathlib.Path(p).read_bytes())
def write(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def tree(n):
 rows={}
 for raw in (P/n).read_bytes().split(b'\0'):
  if not raw:continue
  meta,path=raw.decode('utf-8').split('\t',1);mode,kind,blob=meta.split();rows[path]={'mode':mode,'kind':kind,'blob':blob}
 return rows
scope=load(S/'scope_registration.json');exact=load(P/'exact38.json');before=tree('tree-before.stdout.raw');after=tree('tree-after.stdout.raw')
checks=[]
def ck(n,v,d=None):checks.append({'name':n,'passed':bool(v),'details':d})
delta=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
ck('NUL-tree-exact38',delta==[x['path'] for x in exact])
for row in exact:ck('actual-tree:'+row['path'],before.get(row['path'])==row['before_git'] and after.get(row['path'])==row['after_git'])
for i in [1,2,3]:
 inv=load(P/f'parent-{i}.invocation.json');observed=(P/f'parent-{i}.stdout.raw').read_text(encoding='utf-8').strip()
 ck(f'actual-parent-{i}',inv['argv'][-2:]==['rev-parse',scope['source_chain'][i]+'^'] and observed==scope['source_chain'][i-1])
 ds=(P/f'delta-{i}.stdout.raw').read_text(encoding='utf-8').splitlines();ck(f'actual-delta-{i}',len(ds)==[38,2,1][i-1] and set(ds)<=set(delta))
prior_review=load(scope['root14_review_ref']['path']);prior=load(prior_review['source38_final_hashes_ref']['path']);missing=[x for x in prior if 'mode' not in x]
ck('sole-mode-omission',len(missing)==1 and missing[0]['relative_path']=='apps/control/main.go')
attr=R/'.gitattributes';raw=attr.read_bytes();gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
ck('attribute-original-tree',before['.gitattributes']==after['.gitattributes'] and after['.gitattributes']['blob']==gitsha)
write('raw-format-correction.json',{'schema':'researchos.independent-static-raw-format-correction.v1','original_audit_ref':ref(O/'read_audit.v2.json'),'original_actual_exit':0,'correction':'Author tree stdout is NUL-delimited ls-tree -r -z; saved parent queries are rev-parse commit^, not the future controller rev-list argv. Original derived false rows preserved, not product failures.','checks':checks,'raw_refs':[ref(P/x) for x in ['tree-before.stdout.raw','tree-after.stdout.raw','tree-before.invocation.json','tree-after.invocation.json']]+[ref(P/f'parent-{i}.invocation.json') for i in [1,2,3]],'controller_mode_failure_still_actual_static_defect':True})
assert all(x['passed'] for x in checks)
write('original-attribute-and-missing-mode.json',{'original_attribute_ref':ref(attr),'original_attribute_bytes_utf8':raw.decode('utf-8'),'original_attribute_git':before['.gitattributes'],'same_target_attribute_git':after['.gitattributes'],'missing_mode_row':missing[0],'pinned_prior_map_ref':prior_review['source38_final_hashes_ref'],'target_tree_control_entry':after['apps/control/main.go'],'target_tree_ref':ref(P/'tree-after.stdout.raw'),'boundary':'Source hash remains independently established. Do not rewrite prior map or use an unbounded default mode for arbitrary omissions.'})
source=(P/'integrate_exact38.py').read_text(encoding='utf-8').splitlines()
loc=lambda s:next(i+1 for i,l in enumerate(source) if s in l)
findings=[
 {'id':'I38-SR-01','priority':'BLOCKER','file':str(P/'integrate_exact38.py'),'line':loc("match['mode']"),'problem':'A pinned historical supplemental row for apps/control/main.go lacks mode; direct match[mode] raises before output/failure receipt creation.','actual_product_execution':False,'evidence_ref':ref(O/'original-attribute-and-missing-mode.json'),'minimal_change':'Use a new immutable independently reviewed exact map/supplement binding that sole row to the pinned target Git tree mode/blob/SHA. Alternatively explicitly handle only this known supplemental row with the same fixed raw tree proof; preserve strict mode equality for all others. No generic 100644 default or omission acceptance.'},
 {'id':'I38-SR-02','priority':'BLOCKER','file':str(P/'integrate_exact38.py'),'line':loc("'Nonempty checkout attributes need separate scope'"),'problem':'Current tracked root .gitattributes is the nonempty byte-preservation rule * -text; the blanket non-comment-line rejection blocks this reviewed existing baseline.','actual_product_execution':False,'evidence_ref':ref(O/'original-attribute-and-missing-mode.json'),'minimal_change':'Bind and allow only the exact existing root attribute bytes and matching base/target Git blob. Preserve rejection of all other nonempty nested/info/external attributes, filter/include configuration, and any changed root attribute; do not normalize content or permit arbitrary -text files.'},
 {'id':'I38-PRECONDITION-01','priority':'PRELAUNCH_REQUIRED','file':str(P/'integrate_exact38.py'),'line':loc('out.mkdir()'),'problem':'Fixed parent main_exact38_integration_executor_codex is currently absent; out.mkdir without parents runs before controller try/finally.','minimal_change':'Root may close this in a separately inspected immutable prelaunch producer: only after actual CAS321 + seal, validate fixed ancestor identities/no aliases/reparse, create only the exact parent, preserve absent UUID leaf for controller exclusive creation; outer finally records any preflight failure with nullable native exit.','status':'Root acknowledged planned producer; not read or executed in this review.'}
]
audit=load(O/'read_audit.v2.json')
nonformat=[x for x in audit['failed_checks'] if not x['name'].startswith(('complete-tree-','tree-modes-','chain-parent-','chain-delta-'))]
assert [x['name'] for x in nonformat]==['independent-after:apps/control/main.go']
review={'schema':'researchos.exact38-integration-controller-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','controller_sha256':ref(P/'integrate_exact38.py')['sha256'],'scope_sha256':ref(S/'scope_registration.json')['sha256'],'actual_integration_executed':False,'requested_changes':findings,'controller_ref':ref(P/'integrate_exact38.py'),'scope_ref':ref(S/'scope_registration.json'),'preparation_handoff_ref':ref(P/'handoff.json'),'preparation_manifest_ref':ref(P/'manifest.json'),'audit_ref':ref(O/'read_audit.v2.json'),'raw_format_correction_ref':ref(O/'raw-format-correction.json'),'actual_readonly_audit_exit':0,'actual_readonly_audit_tool':'82a298','prior_audit_failure_ref':ref(O/'failure-origin.828f8b.json'),
 'verified_inputs':{'preparation_manifest_members':63,'protected_current_files':5172,'public_runtime_catalog_files':1211,'exact_source_paths':38,'commit_delta_counts':[38,2,1],'source_chain':scope['source_chain'],'current_canonical_tuple':[320,148,417],'source_after_integration_claim':False},
 'static_guards_reviewed':['Strict duplicate-key/nonfinite JSON decoder and explicit require guards, -I -S -X utf8 optimize0.','Actual future Root321 tuple, independent controller review, ordered canonical byte copies, both cp.work_in_progress refs, unchanged failure prefix, sealed registration refs and original/desired intent bind.','Actual Root320 register/run/seal.v2 output schemas expose all consumed audit/invocation/intent/verified/member fields; future321 scripts and actual output are not yet reviewed/executed.','Fixed source-only parent chain/38 union/current before hash/38 target Git blobs and old11 deletion/index/status checks.','56 fixed owned Git calls maximum; 60s queries/180s sole FF/owned cleanup; Python read/hash IO outside those child intervals.','Exclusive empty hooks, isolated public Git env, disabled replace/system/global config, no filter/include or unapproved checkout attributes; attribute baseline defect separately recorded.','Failure after once leaf persists output and raw nullable native observations; no retry/reset/rollback/clean/commit/push. Post-FF mismatch needs independent new forward-only scope.'],
 'limitations':['Runtime catalog is Python point-in-time observation, not Git full-lifecycle OS module proof.','Same-user TOCTOU not excluded; Root must retain sole serial Main/index/canonical integration lease.','Pre-authority and pre-output failures depend on a separately reviewed outer prelaunch recorder; no actual grant or producer is accepted here.','Original Root306 HOLD/old integration script not reused. Handler/source-only integration is not combined product validation, CLI43/Desktop58/provider/F08/W09 or formal acceptance.'],
 'new_failure_origins':[ref(O/'failure-origin.828f8b.json')],'additional_static_findings_are_native_failures':False,'formal_increment':0,'parent_acceptance':False,'product_or_SQL_or_native_executions':0}
write('review.json',review)
members=[ref(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']]
write('manifest.json',{'schema':'researchos.independent-review-manifest.v1','root':str(O),'member_count':len(members),'members':members,'self_excluded':True,'handoff_excluded':True})
write('handoff.json',{'schema':'researchos.exact38-controller-independent-handoff.v1','decision':review['decision'],'review_ref':ref(O/'review.json'),'manifest_ref':ref(O/'manifest.json'),'controller_ref':review['controller_ref'],'scope_ref':review['scope_ref'],'new_failure_origins':review['new_failure_origins'],'actual_integration_executed':False,'formal_increment':0})
print(json.dumps({'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'handoff':ref(O/'handoff.json'),'failure_origin':ref(O/'failure-origin.828f8b.json')},ensure_ascii=False))
