"""Pure IO/AST construction only; never imports or executes candidate code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
P = ROOT / 'execution/v2.4/receipts'
B = P / 'W13/W13-03/desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060'
C = P / 'W13/W13-03/desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916'
Q = P / 'W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0'
reads = {}
checks = []
def pin(p):
    p = Path(p); b = p.read_bytes()
    row = {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes':len(b)}
    if str(p) in reads:
        assert reads[str(p)] == row, ('input drift', str(p))
    reads[str(p)] = row
    return row
def load(p):
    pin(p); return json.loads(Path(p).read_bytes())
def write(name, data):
    if not isinstance(data, bytes):
        data = (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    p = OUT / name
    with p.open('xb') as f: f.write(data)
    return {'path':str(p), 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)}
def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition, name

q = load(Q/'qualification.json'); r=load(Q/'review.json'); h=load(Q/'handoff.json')
refs={k:pin(Q/n) for k,n in [('qualification_ref','qualification.json'),('review_ref','review.json'),('manifest_ref','manifest.json'),('handoff_ref','handoff.json')]}
expected={'qualification_ref':'b4756653eaa85825f7ec0f787ae3970c9462694439dca6440ee791fb3dc93efe',
          'review_ref':'2d50355615924976b526aae4b3932c9f3b9d491b9da277ef833c36151a4b482a',
          'manifest_ref':'f54787dfafdb645d8e88a866f43e020dfc6f62d8475d84cd71002ba6c7238b90',
          'handoff_ref':'bb3a32c797620f3260fb28807534059c18e46d6f419cbedd55bf62cb97423327'}
for k,v in expected.items(): check('fixed_'+k,refs[k]['sha256']==v)
check('limitations_exact', q['limitations']==r['limitations'])
e=q['evidence_refs']; result=load(e['result_ref']['path']); outer=load(e['root_completion_ref']['path'])
for k,x in e.items():
    check('review_evidence_'+k, x==r[k]); actual=pin(x['path']); check('evidence_hash_'+k,actual['sha256']==x['sha256'] and actual['bytes']==x['bytes'])
# Shape/cross-ref checks only; do not run the gate or audit candidate assertions by importing it.
def ident(x): return str(Path(x['path']).resolve()).casefold(), x['sha256'], x['bytes']
mf=load(e['executor_manifest_ref']['path'])
members={ident(x) for x in mf['files']}
required=[e['result_ref'],outer['closed_graph_ref'],outer['compiled_closure_ref'],outer['test2json_artifact_ref']]
required += [x['result_ref'] for x in result['stages']]
required += [x[k] for x in q['case_facts'] for k in ['invocation_ref','verified_ref','stdout_ref','stderr_ref']]
for i,x in enumerate(required): check('executor_manifest_required_'+str(i),ident(x) in members)
for i,x in enumerate(result['stages']):
    v=load(x['result_ref']['path']); check('stage_sequence_'+str(i),v['request']['sequence']==i+1 and v['actual_exit']==0 and v['result']['actual_exit']==0)

gate=(OUT/'qualification-gate.fragment.py.txt').read_bytes()
ast.parse(gate)
constant=('CLI43_BOUNDED_QUALIFICATION_REFS = '+repr(refs)+'\n\n\n').encode('utf-8')
common=(constant+gate).replace(b'\n',b'\n')
inputs={'builder':B/'build-scope.py','controller':C/'integrate_desktop15.v2.py','scope':C/'scope.v3.proposed.json',
        'launcher':C/'launch_desktop15.v2.py','metadata_builder':B/'build-metadata-templates.py','metadata_engine':B/'metadata-engine.template.py'}
raw={k:p.read_bytes() for k,p in inputs.items()}
for k,p in inputs.items(): pin(p); write('original.'+k+('.json' if k=='scope' else '.py.txt'),raw[k])
changes={}
def changed(name,filename,edits):
    old=raw[name]; new=old
    for before,after in edits:
        check(name+'_unique_anchor_'+str(len(new)),new.count(before)==1)
        new=new.replace(before,after,1)
    inverse=new
    for before,after in reversed(edits):
        check(name+'_inverse_unique_'+str(len(inverse)),inverse.count(after)==1)
        inverse=inverse.replace(after,before,1)
    check(name+'_whole_inverse',inverse==old)
    ast.parse(new,filename=filename)
    before_ast=ast.parse(old); after_ast=ast.parse(new)
    oldf={x.name:ast.dump(x,include_attributes=False) for x in before_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    newf={x.name:ast.dump(x,include_attributes=False) for x in after_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    allowed='main' if name=='builder' else 'grant_check'
    for fn in oldf:
        if fn!=allowed: check(name+'_unchanged_function_'+fn,oldf[fn]==newf[fn])
    rr=write(filename,new)
    write(name+'.diff', ''.join(difflib.unified_diff(old.decode('utf-8').splitlines(True),new.decode('utf-8').splitlines(True),fromfile=str(inputs[name]),tofile=rr['path'])).encode('utf-8'))
    write(name+'.inverse.json', {'original_ref':pin(inputs[name]),'candidate_ref':rr,'whole_inverse_byte_equal':True,
        'edits':[{'before_utf8':a.decode(),'after_utf8':b.decode()} for a,b in edits]})
    changes[name]=rr
    return rr

ca=b'\ndef grant_check(scope,sref,grant):\n'
call=b"    desktop_review=document(scope['desktop_source_review_ref'])\n"
cr=changed('controller','integrate_desktop15.qualification.proposed.py',[
    (ca,b'\n'+common+ca),
    (call,b"    cli43_bounded_qualification_gate(scope['cli43_bounded_qualification_refs'], document, verify, bounded)\n"+call)])
ba=b'\ndef main():\n'
bc=b"        old = doc(ref(N05 / 'integration_codex/cli-exact8-source-integration-r323/scope_registration.json', '52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71'))\n"
addition=("        cli43_bounded_qualification_gate(request['cli43_bounded_qualification_refs'], doc, verify, bounded)\n"
          "        scope['cli43_bounded_qualification_refs'] = request['cli43_bounded_qualification_refs']\n"
          "        scope['controller_ref'] = "+repr(cr)+"\n"
          "        verify(scope['controller_ref'])\n").encode('utf-8').replace(b'\n',b'\n')
br=changed('builder','build-scope.qualification.proposed.py',[(ba,b'\n'+common+ba),(bc,addition+bc)])
scope=json.loads(raw['scope']); original_scope=json.loads(raw['scope'])
scope['controller_ref']=cr; scope['cli43_bounded_qualification_refs']=refs
sr=write('scope.qualification.proposed.json',scope)
back=dict(scope);del back['cli43_bounded_qualification_refs'];back['controller_ref']=original_scope['controller_ref']
check('scope_only_two_deltas',back==original_scope)
check('launcher_byte_reuse',pin(inputs['launcher'])['sha256']=='3669c0c76413728de8157b4f03e27773b25f3c9ad6da600d237629df2c4ae87b')
for a,b in [(b"        cli_ref = ref(",b"        old = doc(ref("),(b"    c43=document(",b"    desktop_review=document(")]:
    name='builder' if a.startswith(b'        ') else 'controller'
    segment=raw[name][raw[name].index(a):raw[name].index(b)]
    new=Path(changes[name]['path']).read_bytes()
    check(name+'_original_sourceimport_predicates_contiguous',segment in new)
write('scope.delta.json',{'original_scope_ref':pin(inputs['scope']),'candidate_scope_ref':sr,
    'changed_only':['controller_ref','cli43_bounded_qualification_refs'],'inverse_original_object_equal':True,
    'original_raw_preserved_ref':{'path':str(OUT/'original.scope.json'),'sha256':hashlib.sha256(raw['scope']).hexdigest(),'bytes':len(raw['scope'])}})
write('request-extension.proposed.json', {'action':'PREPARE_BOUND_PROPOSAL_ONLY','authorized':False,'future_root_grant':None,
    'cli43_bounded_qualification_refs':refs,'future_expected_before':None,'future_expected_after':None,
    'usage':'Merge only cli43_bounded_qualification_refs into the future actual Root request. Existing required fields remain mandatory.'})
before=list(reads.values()); write('inputs.before.json',before)
for p in list(reads): pin(p)
write('inputs.after.json',list(reads.values()))
write('static-audit.json',{'checks':checks,'check_count':len(checks),'failed':sum(not x['passed'] for x in checks),
    'AST_only_candidate_not_executed':True,'candidate_imports':0,'input_drift':[], 'actual_Go_SQL_Node_SDK_HTTP_model_CAS':0,
    'new_failure_origins':[],'actual_native_exit':None})
write('handoff.json',{'schema':'researchos.desktop15-cli-qualification-gate-preparation.v1','actor':'codex:/root/command_queue_impl',
    'status':'SOURCE_PREPARATION_REPORTED_STOPPED_PENDING_NONAUTHOR_REVIEW','authorized':False,'source_acceptance':False,
    'builder_ref':br,'controller_ref':cr,'scope_ref':sr,'qualification_refs':refs,
    'reused_unchanged_refs':{k:pin(inputs[k]) for k in ['launcher','metadata_builder','metadata_engine']},
    'inverse_proofs':['builder.inverse.json','controller.inverse.json','scope.delta.json'],
    'runtime_note':'Gate is embedded identically; launcher already calls grant_check before helper/native. All gate reads enter existing READS closure. Existing metadata builder copies full scope and its immutable inputs; no engine/launcher changes.',
    'authority_order':['old Main38/CLI43 source-import predicates unchanged','fixed nonauthor r331 bounded qualification gate','existing Desktop review and actual new Root scope/CAS/grant'],
    'closed_only':'Two held2 current43 fixture cases; this package does not re-review or re-execute them.',
    'OPEN':['Independent review of this changed builder/controller and final actual scope','Actual Root parameters/current source/resources/tuple/origin cut','New reviewed metadata drafts and actual sealed CAS/grant','Exact15 source-only commit and forward-head registration','Fresh58/169Node/installedGUI and remaining product/formal gates'],
    'future_execution':'NOT_RUN','new_failure_origins':[],'formal_increment':0})
entries=[]
for p in sorted(OUT.iterdir()):
    if p.is_file():
        b=p.read_bytes();entries.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
write('manifest.json',{'count':len(entries),'entries':entries,'excluded_only_self':True})
print(json.dumps({'handoff':pin(OUT/'handoff.json'),'manifest':pin(OUT/'manifest.json'),'builder':br,'controller':cr,'checks':len(checks)},ensure_ascii=False))
