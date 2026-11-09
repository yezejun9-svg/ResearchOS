"""Independent selected AST controls; no SQL, native, model or candidate main."""
import ast,copy,difflib,hashlib,json,pathlib,re
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94'
A=pathlib.Path(__file__).parent
def pin(p):
 b=p.read_bytes()
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def resolve(s):
 p=pathlib.Path(s);return p if p.is_absolute() else R/p
def checkref(ref):
 p=resolve(ref['path']);b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'],p
 return p
def put(name,obj):
 with (A/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(A/name)
mf=json.loads((S/'manifest.json').read_bytes());hf=json.loads((S/'handoff.json').read_bytes())
for x in mf['members']:checkref(x)
assert len(mf['members'])==23
assert set(p.name for p in S.iterdir())=={resolve(x['path']).name for x in mf['members']}|{'manifest.json','handoff.json','postseal-tool-observations.original.json'}
for k,v in hf.items():
 if k.endswith('_ref') and isinstance(v,dict) and {'path','sha256','bytes'}<=set(v):checkref(v)
iv=json.loads((S/'source.inverse.final.json').read_bytes())
inverse=[]
for e in iv['entries']:
 bp,ap=checkref(e['before_ref']),checkref(e['after_ref'])
 before,after=bp.read_bytes(),ap.read_bytes()
 exact=''.join(difflib.unified_diff(after.decode().splitlines(True),before.decode().splitlines(True),fromfile=e['after_ref']['path'],tofile=e['before_ref']['path']))
 assert exact==e['inverse_unified_diff']
 nd=list(difflib.ndiff(before.decode().splitlines(True),after.decode().splitlines(True)))
 assert ''.join(difflib.restore(nd,1)).encode()==before and ''.join(difflib.restore(nd,2)).encode()==after
 ast.parse(after);inverse.append({'target':e['target'],'exact_inverse_and_restore':True})
basis=json.loads((S/'public-source-basis.actual.json').read_bytes())
for ref in basis['members']:checkref(ref)
profile=S/'formal_profile_w05.final.proposed.py'
tree=ast.parse(profile.read_bytes())
funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
selected={'_integer','_native_exit','_nonempty','_json_original','_original','_root_pair','_jsonl','verify_refusal','verify_capture_bundle'}
space={'json':json,'re':re,'IDS':tuple('A04-0'+str(i) for i in range(1,7)),
 'GATES':('W05-G01','W05-G02','W05-H08','W05-P01','W05-U02'),
 'SCENARIOS':('success','tool_failed','request_timeout','pending_queue_cancel','executor_crash'),
 'EXTRA':{'A04-04':'H08','A04-05':'P01','A04-06':'U02'},
 'ASSERTION_LANES':dict(zip(tuple('A04-0'+str(i) for i in range(1,7)),('success','pending_queue_cancel','executor_crash','H08','P01','U02')))}
exec(compile(ast.Module(body=[funcs[n] for n in funcs if n in selected],type_ignores=[]),'<selected pure data guards>','exec'),space)
checks=[]
def observe(name,fn):
 try: result=fn();outcome='ACCEPT';error=None
 except (ValueError,TypeError,KeyError) as e:outcome='REJECT';error=str(e)
 checks.append({'name':name,'outcome':outcome,'error':error,'qualification':'SYNTHETIC_LEAF_ONLY'})
 return outcome,error
for v in (False,True,0.0,None,-1):
 assert observe('count rejects '+repr(v),lambda v=v:space['_integer'](v,'count'))[0]=='REJECT'
assert observe('integer zero valid',lambda:space['_integer'](0,'count'))[0]=='ACCEPT'
def ref(s):return {'path':s,'sha256':'a'*64}
scope={'initial_tool_input':{'cmd':'SYNTHETIC NEVER EXECUTED'}}
initial={'tool':'exec_command','input':scope['initial_tool_input'],'result':{'exit_code':0,'output':json.dumps({'actual_launcher_native_exit':3})}}
pair={'schema':'researchos.w05.original-tool-pair.v2','initial':initial,'terminal':copy.deepcopy(initial)}
row={'id':'A04-02','expected':'FROZEN_NEGATIVE','lane':'pending_queue_cancel','product_identity':{'task_id':'same-task'},'negative_invocation_ref':ref('negative'),'refusal_evidence_refs':[ref('refusal')]}
docs={'refusal':{'schema':'researchos.w05.actual-refusal.v2','assertion_id':row['id'],'run_id':'current-run','lane':row['lane'],'task_id':'same-task','rejected':True,'negative_condition':row['expected'],'invocation_ref':ref('negative'),'original_response_ref':ref('response')},
 'negative':{'native_exit':3,'root_tool_pair_ref':ref('pair'),'scope':scope,'run_id':'foreign-run','lane':'success','task_id':'foreign-task'},
 'pair':pair,'response':{'status':'REJECTED','task_id':'same-task','run_id':'foreign-run','lane':'success','negative_condition':'UNRELATED_AUTH_ERROR'}}
d=lambda r:docs[r['path']]
w=lambda r:json.dumps(d(r)).encode()
assert observe('R02 foreign actual negative invocation and response accepted under relabeled refusal',lambda:space['verify_refusal'](d,w,{'run_id':'current-run'},row))[0]=='ACCEPT'
docs['refusal']['rejected']=False
assert observe('R02 rejected false correctly rejects',lambda:space['verify_refusal'](d,w,{'run_id':'current-run'},row))[0]=='REJECT'
docs['refusal']['rejected']=True
identity={k:k+'-x' for k in ('project_id','session_id','goal_id','task_id','run_id','core_build_id')}
event={'type':'session.event','event':{'sequence':1,'session_id':identity['session_id'],'protocol_version':'researchos-client/2','core_build_id':identity['core_build_id'],'run_id':identity['run_id'],'kind':'RUN_STATE','payload':{}}}
final={'execution':{k:identity[k] for k in ('project_id','session_id','goal_id','task_id','run_id')}}
final['execution'].update(event_sequence=1,independent_acceptance='NOT_EVALUATED',exit_code=0)
def jsonl(e):return (json.dumps(e)+'\n'+json.dumps(final)+'\n').encode()
assert observe('R03 missing required SessionEvent identities accepted',lambda:space['_jsonl'](jsonl(event),identity))[0]=='ACCEPT'
mal=copy.deepcopy(event);mal['event'].update(kind='INVENTED');mal['event'].pop('payload')
assert observe('R03 unknown event kind and absent payload accepted',lambda:space['_jsonl'](jsonl(mal),identity))[0]=='ACCEPT'
bad=copy.deepcopy(event);bad['event']['sequence']=True
assert observe('boolean event sequence correctly rejects',lambda:space['_jsonl'](jsonl(bad),identity))[0]=='REJECT'
dbguard=next(n for n in ast.walk(funcs['_database']) if isinstance(n,ast.If) and 'type(digest)' in ast.unparse(n.test))
dbcode=compile(ast.Module(body=[dbguard],type_ignores=[]),'<exact database digest predicate>','exec')
assert observe('public Task TaskRun NULL hash rejected',lambda:exec(dbcode,{'revision':1,'digest':None,'re':re}))[0]=='REJECT'
# Exercising exact dispatcher data guard with injected semantic functions only;
# this proves the unconditional final OPEN, not any LIVE witness qualification.
space['verify_live_originals']=lambda *args:None
space['verify_refusal']=lambda *args:None
grantref=ref('grant');issuance=ref('issuance');original=ref('original')
b={'schema':'researchos.w05.live-dispatch-bundle.v1','task_id':'W05','case_id':'A04','mode':'LIVE_WINDOWS','run_id':'r','selected_runtime':'mu','fixed_model':'fixed','root_grant_ref':grantref,'root_grant_issuance_ref':issuance,'product_original_refs':[original],'accounting':{'mode':'UNLIMITED_AMOUNT','status':'UNKNOWN','amount_usd':None,'source_refs':[]},'invocations':[],'assertions':[]}
bd={'grant':{'run_id':'r','decision':'GRANTED','mode':'LIVE_WINDOWS','selected_runtime':'mu','fixed_model':'fixed','accounting_mode':'UNLIMITED_AMOUNT'},
 'issuance':{'schema':'researchos.w05.original-root-grant-issuance.v2','actor_id':'codex:/root','run_id':'r','grant_ref':grantref,'original_input':{},'original_result':{'exit_code':0,'output':json.dumps({'grant_ref':grantref})}},'original':True}
for lane in (*space['SCENARIOS'],*space['EXTRA'].values()):
 ir,sr=ref('inv-'+lane),ref('scope-'+lane)
 bd[ir['path']]={'schema':'researchos.w05.live-invocation.v1','run_id':'r','lane':lane,'root_grant_ref':grantref}
 bd[sr['path']]={'schema':'researchos.w05.a04-live-scope.v1','root_grant_ref':grantref}
 b['invocations'].append({'lane':lane,'invocation_ref':ir,'scope_ref':sr})
for cid in space['IDS']:
 p=ref('proof-'+cid);lane=space['ASSERTION_LANES'][cid]
 bd[p['path']]={'schema':'researchos.w05.a04-raw-observation.v1','assertion_id':cid,'run_id':'r','lane':lane,'facts':{'k':True},'fact_source_refs':{'k':original}}
 b['assertions'].append({'id':cid,'lane':lane,'status':'PASS','actual':'data','raw_evidence_refs':[p]})
for selector in ('A04',*space['GATES']):
 outcome,error=observe('dispatcher unconditional OPEN '+selector,lambda selector=selector:space['verify_capture_bundle'](lambda r:bd[r['path']],lambda r:b'',b,selector))
 assert outcome=='REJECT' and error=='OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED'
bd['proof-A04-01']['facts']={};bd['proof-A04-01']['fact_source_refs']={}
outcome,error=observe('R01 empty facts and sources rejected',lambda:space['verify_capture_bundle'](lambda r:bd[r['path']],lambda r:b'',b,'A04'))
assert outcome=='REJECT' and error=='OPEN_EMPTY_OR_UNBOUND_FACT_PROJECTION'
out={'schema':'researchos.a04-revision-independent-controls.v1','source_ref':pin(profile),'checks':checks,'control_count':len(checks),'source_manifest_members_verified':23,'source_inventory_exact_with_declared_external_annex':True,'inverse':inverse,
 'public_basis_pins_verified':len(basis['members']),'source_handoff_ref':pin(S/'handoff.json'),'source_manifest_ref':pin(S/'manifest.json'),'source_report_ref':pin(S/'report.json'),
 'source_postseal_original_io_ref':pin(S/'postseal-tool-observations.original.json'),
 'public_sources':[pin(R/'internal/domain/store.go'),pin(R/'internal/domain/client_protocol_events.go'),pin(R/'apps/cli/cli_stream.go')],
 'actual_sql_calls':0,'actual_native_calls':0,'actual_model_calls':0,'candidate_main_calls':0,'canonical_writes':0,'formal_increment':0}
p=put('independent-controls.json',out)
print(json.dumps({'audit_root':A.relative_to(R).as_posix(),'controls_ref':p,'controls':len(checks),'confirmed_open_findings':3},ensure_ascii=False))
