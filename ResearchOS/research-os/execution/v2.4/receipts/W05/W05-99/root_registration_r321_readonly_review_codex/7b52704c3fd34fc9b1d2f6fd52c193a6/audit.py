import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
P=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320'
checks=[];reads={}
def check(n,v):checks.append({'name':n,'pass':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);raw=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if str(p) in reads:check('unchanged:'+str(p),reads[str(p)]==r)
 reads[str(p)]=r;return raw
def ref(p):read(p);return reads[str(path(p))]
def verify(r):
 b=read(r['path']);check('ref:'+r['path'],hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']);return b
def doc(p):return json.loads(read(p))
def recursive(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():verify(v)
  else:
   for x in v.values():recursive(x)
 elif isinstance(v,list):
  for x in v:recursive(x)
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
pins={'register.py':'199e46d1db99b7c18053759d69a920330df92b1bf901637beb675aef06c82dcd','run.py':'dcff04204ca0461eefadb763ef2cec68826b2e6b7dabad4c9dd770b29c342b3a','prepared_refs.json':'1d10ff495924f1c3b9b6a6a9fe927ff5c6c5bde99a61f189ea4d741ff434efcf','audit.json':'80c24d54d2998688e483a8c6a887f6be7f5f7ac6da1878c38c668681ecdfb68b','seal.py':'d55bd1cce6fe1a0a76e7dc8f8966b0d499ead0d5a4d7cc2383e30ffacebf0b77'}
texts={}
for name,h in pins.items():
 b=read(S/name);check('draft-pin:'+name,hashlib.sha256(b).hexdigest()==h)
 if name.endswith('.py'):ast.parse(b,filename=name);check('AST:'+name,True);texts[name]=b.decode()
prepared=doc(S/'prepared_refs.json');audit=doc(S/'audit.json')
recursive(prepared);recursive(audit)
check('verified_refs42',len(prepared['verified_refs'])==42)
canonical=prepared['canonical_before'];names=['checkpoint','path_ownership','step_state','commands']
check('ordered-canonical4',[x['path'] for x in canonical]==['execution/v2.4/'+n+'.json' for n in names])
copies=[];docs=[]
for name,item in zip(names,canonical):
 b=verify(item);docs.append(json.loads(b))
 old=P/(name+('.desired.json' if name in names[:2] else '.original.json'))
 check('prior320-original-compatible:'+name,b==read(old))
 with (O/(name+'.before.json')).open('xb') as f:f.write(b)
 rr=ref(O/(name+'.before.json'));rr['path']=(O/(name+'.before.json')).relative_to(R).as_posix();copies.append(rr)
cp,ow=docs[:2];check('actual-before',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[320,148,417])
check('head-pinned',cp['head']==prepared['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079')
check('status-pin',prepared['git_status_sha256']=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4')
check('audit-tuples',audit['expected_before']==[320,148,417] and audit['expected_after']==[321,149,422])
check('cut-equality',audit['new_origins']==prepared['origins'])
oldkeys={x.get('origin_key') for x in cp['failure_counters']};newkeys=[x['origin_key'] for x in prepared['origins']]
check('five-unique-new-origins',len(newkeys)==len(set(newkeys))==5 and not oldkeys.intersection(newkeys))
native_expected=[1,None,None,None,1]
for i,row in enumerate(prepared['origins']):
 original=json.loads(verify(row['evidence_ref']))
 check('original-exact-payload:'+row['origin_key'],row['original_payload']==original)
 check('origin-typed-exits:'+row['origin_key'],row['actual_outer_exit']==1 and row['actual_native_exit']==native_expected[i] and row['actual_native_product_exit'] is None and row['product_cases_run']==0)
check('two-pending',len(prepared['pending_origin_refs'])==2)
check('pending-not-cut',not {x['sha256'] for x in prepared['pending_origin_refs']}.intersection(x['evidence_ref']['sha256'] for x in prepared['origins']))
bindings=prepared['pins'];cr=json.loads(verify(bindings['integration_controller_review']))
check('current-controller-independent-review',cr['decision']=='READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE' and cr['reviewer']=='codex:/root/w05_merge_review' and cr['requested_changes']==[] and cr['actual_integration_executed'] is False)
check('reviewed-exact-launcher',bindings['integration_launcher']['sha256']==cr['launcher_sha256']=='be5fdfae7c321376dc60f964167a92f06725bfe83e97a826e50a6eae8f2a2bc2')
check('reviewed-exact-controller',bindings['integration_controller']['sha256']==cr['controller_sha256']=='e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff')
check('reviewed-exact-scope',bindings['scope']['sha256']==cr['scope_sha256']=='254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90')
scope=json.loads(verify(bindings['scope']));check('only-after-cas-seal-grant',scope['effective_only_after_actual_registration_seal_and_once_grant'] is True and scope['Main_integration_currently_authorized'] is False)
check('W09-original-writer',ow['card_path_bindings']['W09-99']['subtasks']['causal_test_source_exact4']['current_source_writer']=='codex:/root/sources_parent_impl')
for task,sub in [('W05-99','session_list_closedcopy_root_finite14'),('W05-99','session_list_closedcopy_exact1'),('W13-03','go3_debug_component_root_once')]:check('existing-binding:'+sub,sub in ow['card_path_bindings'][task]['subtasks'])
for key,decision in [('root14_review','READY_FOR_ROOT_REGISTERING_BOUNDED14_LIST_FIX_SOURCE_WITH_DECLARED_OPEN_GATES'),('w09_review','SOURCE_IMPLEMENTED_STATIC_REVIEWED_WITH_EXPLICIT_UNRUN_GATES')]:check('bounded-decision:'+key,json.loads(verify(bindings[key]))['decision']==decision)
r=texts['register.py'];w=texts['run.py'];s=texts['seal.py']
guard_literals={
 'four-live-before-each-replace':'assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)',
 'expected-live-updated':'expected_live[path] = raw',
 'cached-canonical-updated':'READS[path] = raw',
 'cached-inputs-current-before-write':'assert all(path.read_bytes() == raw for path, raw in READS.items())',
 'old417-prefix-after':'assert actual[\'failure_counters\'][:417] == old_failures',
 'formal-unchanged':'assert actual[\'current_effective_formal_status\'] == json.loads(before[CANON[0]])[\'current_effective_formal_status\']',
 'original-intent-before-write':"intent_ref = save('canonical-write.intent.json'",
 'exclusive-temporary':"path.with_name(path.name + '.root321.tmp').open('xb')",
 'failure-journal':"save('canonical-write.exception.json'",
 'pending-lowerbound':"['observed_actual_tool_origin_lower_bound_after_r321_cut'] = 424",
 'no-optimized-asserts':"if sys.flags.optimize:",
 'completed-only-after-verify':"save('canonical-write.verified.json'"}
for n,literal in guard_literals.items():check(n,literal in r)
check('intent-before-first-replace',r.index("intent_ref = save(")<r.index('os.replace('))
check('4pin-loop-before-replace',r.index('assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)')<r.index('os.replace('))
check('wrapper-copies-within-review-parent','assert copied_path.is_relative_to(review_path.parent)' in w)
check('wrapper-current4-before-child',w.index("for item in prepared['canonical_before']:")<w.index('subprocess.run('))
check('wrapper-no-site-utf8',"[sys.executable, '-I', '-S', '-X', 'utf8', str(runner)]" in w)
check('sealer-actual0-required',"assert invocation['actual_exit'] == 0" in s)
check('sealer-raw-stream-hashes',all("invocation['"+x+"_sha256'] == ref(OUT / '"+x+".raw')['sha256']" in s for x in ['stdout','stderr']))
check('sealer-old320-4copies',"PREVIOUS = OUT.parent / 'parallel-source-and-go3-r320'" in s and "assert original == previous.read_bytes()" in s)
check('sealer-actual-target',"== [321, 149, 422]" in s and "cp_after['failure_counters'][:417] == cp_before['failure_counters']" in s)
check('sealer-current-reg-review-pin',"'fresh38_controller_review_ref': prepared['pins']['integration_controller_review']" in s)
check('sealer-nonacceptance',"'source_only38_actual_merge': 'NOT_STARTED_AT_REGISTRATION_SEAL', 'source_acceptance': False" in s)
for p,row in list(reads.items()):
 b=Path(p).read_bytes();check('after-read-unchanged:'+p,len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'])
save('checks.json',{'checks':checks,'failed':[x for x in checks if not x['pass']],'target_executions':0})
save('reads.json',list(reads.values()))
save('canonical-copies.json',copies)
print(json.dumps({'checks':len(checks),'failed':sum(not x['pass'] for x in checks),'reads':len(reads),'out':str(O)},ensure_ascii=True))
