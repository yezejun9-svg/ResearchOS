"""Independent read/hash/AST audit. Does not import or execute any candidate."""
import ast
import hashlib
import json
import os
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
P = R/'execution/v2.4/receipts/W13/W13-03'
N = P/'fresh58_public_source_authority_preparation_codex/52d89f9f274642189817dd242291ad8c'
O = Path(__file__).resolve().parent
checks = []
observed = {}

def ck(name, value):
    checks.append({'name':name,'passed':bool(value)})

def raw(p):
    p = Path(p)
    if not p.is_absolute(): p = R/p
    b = p.read_bytes()
    observed[str(p)] = b
    return b

def ref(p, b=None):
    p = Path(p)
    if not p.is_absolute(): p = R/p
    if b is None: b = raw(p)
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def verify(r, name):
    b = raw(r['path'])
    ck(name, len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'])
    return b

def doc(p): return json.loads(raw(p))
def vdoc(r,n): return json.loads(verify(r,n))
def put(name,value):
    b = (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (O/name).open('xb') as f: f.write(b)
    return ref(O/name,b)

mf = doc(N/'manifest.json')
ck('preparation-manifest-pin',ref(N/'manifest.json')['sha256']=='a4278350fb970fbd6bc3c9597850b9d140023f18f3d9ea1fb7040665bd0c1be9')
ck('manifest-count',len(mf['entries'])==mf['count']==15 and mf['self_excluded'] is True)
for i,r in enumerate(mf['entries']): verify(r,'manifest-member-'+str(i))
h = doc(N/'handoff.json'); fixed = doc(N/'fixed-inputs.json'); contract = doc(N/'contract.json')
for k,v in fixed.items(): verify(v,'fixed-'+k)
for i,v in enumerate(h['additional_input_refs']): verify(v,'additional-'+str(i))
src = raw(N/'publish.proposed.py'); syntax = ast.parse(src)
gate = raw(fixed['gate']['path']); ga = ast.parse(gate)
ck('producer-pin',hashlib.sha256(src).hexdigest()=='a3da1646eb2b745595885a0f9bae8cf6aafd1ccc83f4640244943d3da9f5cf90' and len(src)==17469)
ck('fixed-pin',ref(N/'fixed-inputs.json')['sha256']=='bc865b00f4093f14b6cb5d40ba05099cd13e6b39cfb36ac8d520eb7eecac0a93')
imports = [ast.unparse(n) for n in ast.walk(syntax) if isinstance(n,(ast.Import,ast.ImportFrom))]
ck('no-native-or-network-imports',not any(t in '\n'.join(imports) for t in ['subprocess','ctypes','socket','sqlite3','urllib']))
ck('no-mutation-of-source',not any(isinstance(n,ast.Attribute) and n.attr in ['unlink','replace','rename','rmdir'] for n in ast.walk(syntax)))
predicate = next(n for n in ga.body if isinstance(n,ast.FunctionDef) and n.name=='validate_current58_source')
methods = sorted({n.func.attr for n in ast.walk(predicate) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='reader'})
ck('prospective-reader-interface',methods==['doc','verify'])
ck('prospective-before-allocation',src.index(b'module.validate_current58_source(')<src.index(b'    out.mkdir()'))
ck('no-grant-entry-call',b'module.load_scope(' not in src and b'module.validate_grant(' not in src)
ck('no-site/no-pyc',b'sys.flags.no_site' in src and b'sys.dont_write_bytecode = True' in src)
ck('pending-ref-check',b"need(pin_bytes(Path(key),raw) == ref, 'Prospective exact ref')" in src)
ck('review-ref-no-selfhash-cycle',b"review['producer_ref'] == q['producer_ref']" in src and b"review['fixed_inputs_ref'] == q['fixed_inputs_ref']" in src)

selection=doc(N/'selection.static.json'); old=doc(fixed['old_catalog']['path']); closure=doc(fixed['closure']['path']); scope=doc(fixed['source_scope']['path'])
tree_raw=raw(fixed['tree']['path']); tree={}
ck('tree-NUL',tree_raw.endswith(b'\0'))
for item in tree_raw[:-1].split(b'\0'):
    metadata,name=item.split(b'\t',1); mode,kind,blob=metadata.decode('ascii').split(' ')
    tree[name.decode('utf-8')]={'mode':mode,'kind':kind,'git_blob':blob}
ck('full-tree-casefold-unique',len(tree)==len(tree_raw[:-1].split(b'\0'))==len({p.casefold() for p in tree}))
oldnames={x['path'] for x in old['files']}
combined=set(scope['shared38_paths']+scope['cli8_paths']+closure['source_paths'])
go={p for p in tree if p.endswith('.go') and not p.startswith(('execution/','.local/'))}
extra={'apps/desktop/build-validator.py','spec/v2.0/ui/design-tokens.json','tests/contracts/fixtures/client_protocol_v2_fixtures.json','tests/ui/desktop/w13-react.test.js','apps/desktop/package.json','apps/desktop/package-lock.json','apps/web/package.json','apps/web/package-lock.json'}
for p in tree:
    if p.startswith(('apps/desktop/main/','apps/desktop/preload/','apps/desktop/validator/','apps/web/src/','apps/web/public/')) or (p.startswith('apps/web/') and p.count('/')==2) or (p.startswith('tests/ui/desktop/') and p.count('/')==3 and p.endswith('.mjs')) or (p.startswith('apps/desktop/tests/') and p.count('/')==3 and p.endswith('.js')): extra.add(p)
names=oldnames|go|combined|extra|{'go.mod','go.sum'}|{p for p in tree if p.startswith(('migrations/sqlite/','spec/v2.0/contracts/'))}
ck('selection-exact-current',sorted(names)==[x['path'] for x in selection['files']])
ck('selection-counts',len(names)==639 and len(go)==559 and len(oldnames)==597 and len(names-oldnames)==42 and len(combined)==58)
ck('combined-union',set(selection['combined58_paths'])==combined)
oldrows={x['path']:x for x in old['files']}
currentrows={x['path']:x for x in selection['files']}
for p in sorted(names):
    b=raw(R/p); row=currentrows[p]; info=tree[p]
    ck('source:'+p,info=={k:row[k] for k in ['mode','kind','git_blob']} and info['mode']=='100644' and info['kind']=='blob' and len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode('ascii')+b'\0'+b).hexdigest()==info['git_blob'])
    ancestors=[R/p,*(R/p).parents]
    for ancestor in ancestors:
        st=os.lstat(ancestor)
        ck('nonreparse:'+str(ancestor),not ancestor.is_symlink() and not (getattr(st,'st_file_attributes',0)&0x400))
        if ancestor==R: break
ck('old597-unchanged',all(all(currentrows[p][k]==oldrows[p][k] for k in ['sha256','bytes','git_blob']) for p in oldnames))
inv=doc(fixed['tree_invocation']['path'])
ck('tree-invocation',inv['argv'][-4:]==['ls-tree','-r','-z',h['source_commit']] and inv['actual_native_exit']==0 and inv['wrapper_error'] is None and inv['process_observation']['actual_exit']==0 and inv['automatic_retry'] is False)
source_mf=doc(closure['manifest_ref']['path'])
ck('tree-receipt-membership',all(any(Path(m['path'])==Path(fixed[k]['path']) and m['sha256']==fixed[k]['sha256'] and m['bytes']==fixed[k]['bytes'] for m in source_mf['entries']) for k in ['tree','tree_invocation']))
forward=vdoc(h['additional_input_refs'][0],'forward-review')
ck('forward-closure',forward['actual_head']==h['source_commit'] and forward['actual_parent']==h['source_parent'] and forward['decision']=='SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' and forward['canonical_tuple']==[333,161,524] and forward['actual_registration_evidence_closed'] is True and forward['source_acceptance'] is False and forward['fresh58_qualified'] is False)
canonical=[]
for i,r in enumerate(forward['canonical_refs']):
    b=verify(r,'current-canonical-'+str(i)); canonical.append(json.loads(b))
ck('current-observed-tuple',[canonical[0]['revision'],canonical[1]['revision'],len(canonical[0]['failure_counters'])]==[333,161,524])
ck('current-observed-head',canonical[0]['head']==h['source_commit'])
wip=canonical[0]['work_in_progress']; lease=canonical[1]['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']
ck('gate-current-source-state',wip['desktop_exact15_source_integration_state']=='CLOSED_PENDING_FRESH58_VALIDATION' and wip['desktop_exact15_actual58_head']==h['source_commit'] and wip['desktop_exact15_actual_combined_source_paths']==58 and lease['current_source_writer'] is None and lease['state']=='CLOSED_PENDING_FRESH58_VALIDATION')
for k,v in [('desktop_exact15_source_integration_execution_review_ref',fixed['closure']),('desktop_exact15_source_integration_completed_ref',closure['completed_ref']),('desktop_exact15_source_integration_manifest_ref',closure['manifest_ref']),('desktop_exact15_source_integration_outer_manifest_ref',closure['outer_manifest_ref']),('desktop_exact15_source_integration_grant_ref',closure['grant_ref'])]:
    ck('gate-WIP:'+k,verify(wip[k],'wip-ref:'+k)==verify(v,'closure-ref:'+k))
fm=doc(fixed['forward_manifest']['path']); ck('forward-MF-shape',len(fm['entries'])==fm['count']==87 and fm['self_excluded'] is True)
for i,r in enumerate(fm['entries']): verify(r,'forward-member-'+str(i))
fa=doc(fixed['forward_audit']['path']); fi=doc(fa['invocation_ref']['path']); intent=doc(fa['intent_ref']['path']); fv=doc(fa['verified_ref']['path'])
ck('gate-forward-refs-exactdict',all(r in fm['entries'] for r in [fixed['forward_audit'],fa['invocation_ref'],fa['intent_ref'],fa['verified_ref']]))
ck('gate-forward-actual-facts',fa['registered_head']==h['source_commit'] and fa['actual_registration_exit']==0 and fi['actual_exit']==0 and fi['wrapper_error'] is None and fv['intent_ref']==fa['intent_ref'] and len(intent['metadata'])==2 and len(intent['unchanged'])==2)

lines=src.decode('utf-8').splitlines()
def line(needle): return next(i+1 for i,t in enumerate(lines) if needle in t)
findings=[{'id':'PUB-01','priority':'BLOCKER','path':str(N/'publish.proposed.py'),'lines':[line("copies = q['canonical_copies']"),line("for i, original in enumerate(forward_review['canonical_refs'])"),line('    stable()')],
 'problem':'Copies are checked against the historical r333 review, but the publisher never reads the four live canonical files. stable() only re-reads READS, so a later live revision or writer change is not detected and the old copied tuple can still be published as current.',
 'required_change':'In a new immutable producer, compare all four current canonical raw bytes against their reviewed immutable copies before allocation and again before successful publication; preserve the same comparison across publication checks. Treat these as current observations, not immutable live-input refs. Keep immutable copies and their source identity/order bound to r333.',
 'completion_criterion':'Static data flow proves all four live paths are read and byte-compared to the corresponding copied raw buffers and any mismatch fails before allocation or prevents success after allocation. Do not grant execution or reset counters.'}]
conditions=[{'id':'PUB-PATH-01','path':str(N/'publish.proposed.py'),'line':line('PUBLISH_PARENT ='),
 'condition':'Actual Root request must use '+str(P/'fresh58_public_source_authority_codex')+'/<publish_uuid>. The announced P05/integration_codex/cli58-public-source-16e... is rejected by out.parent == PUBLISH_PARENT. Correct future request path; no unreviewed widening of producer output family.',
 'actual_request_seen':False}]
for p,b in list(observed.items()): ck('after-drift:'+p,Path(p).read_bytes()==b)
failed=[x for x in checks if not x['passed']]
audit=put('audit.json',{'schema':'researchos.fresh58-catalog-producer-readonly-audit.v1','checks':checks,'check_count':len(checks),'failed_checks':failed,'observed_input_count':len(observed),'selection_current_source_rows_rehashed':639,'gate_imported':False,'candidate_executed':False,'native_Git_Go_Node_Job_SQL_HTTP_SDK_models':0,'new_failure_origins':[]})
inputs=put('inputs.json',{'files':[ref(p,b) for p,b in sorted(observed.items())],'source_file_count':639,'actual_compiler_graph':None,'self_excluded':True})
review=put('review.json',{'schema':'researchos.fresh58-catalog-producer-independent-review.v1','reviewer':'codex:/root/w05_merge_review','author':'codex:/root/command_queue_impl','nonauthor':True,'decision':'REQUEST_CHANGES','requested_changes':findings,'composition_conditions':conditions,'producer_ref':h['producer_ref'],'fixed_inputs_ref':h['fixed_inputs_ref'],'contract_ref':h['contract_ref'],'preparation_manifest_ref':ref(N/'manifest.json'),'forward_registration_review_ref':h['additional_input_refs'][0],'gate_ref':fixed['gate'],'audit_ref':audit,'inputs_ref':inputs,'source_commit':h['source_commit'],'source_parent':h['source_parent'],'canonical_tuple_observed':[333,161,524],'actual_source_publication':False,'source_acceptance':False,'formal_increment':0,'execution_authorized':False,'future_scope_grant':None,'new_failure_origins':[],
 'verified_summary':{'all_preparation_members':15,'fresh_selected_files':639,'Go_files':559,'old597_unchanged':True,'added':42,'exact_union':58,'gate_reader_required_methods':methods,'gate_call_before_leaf_allocation':True,'prospective_refs_verified_in_memory':True,'no_review_request_hash_cycle':True,'strict_JSON_and_reparse_guards_preserved':True,'checks':len(checks),'failed_checks':len(failed)},
 'limits':['No publisher/gate import, execution, subprocess or native helper was performed. Static interface/data checks are not an executed positive control.','Actor strings are attribution, not cryptographic identity or execution permission. Root-owned request and external orchestration remain required.','Current canonical equality was observed by this reviewer; it does not close the missing future producer guard.','Source rows were independently read/hash-checked. Source closure/native history is transparently reused from f14/7d82; no native integration was rerun.','Fresh compiler graph, generated inputs, runtime catalogs, SDK/GUI/Node/CLI cases and formal acceptance remain OPEN.']})
handoff=put('handoff.json',{'schema':'researchos.independent-review-handoff.v1','review_ref':review,'decision':'REQUEST_CHANGES','check_count':len(checks),'failed_audit_checks':len(failed),'blocking_findings':1,'composition_conditions':1,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file()]
manifest=put('manifest.json',{'schema':'researchos.immutable-public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'review_ref':review,'handoff_ref':handoff,'manifest_ref':manifest,'checks':len(checks),'failed_audit_checks':len(failed),'decision':'REQUEST_CHANGES','new_failure_origins':[]},ensure_ascii=False))
