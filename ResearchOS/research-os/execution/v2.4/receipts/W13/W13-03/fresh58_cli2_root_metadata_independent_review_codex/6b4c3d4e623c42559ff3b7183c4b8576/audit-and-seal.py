"""Own source-only read/hash/AST review; no candidate imports or native calls."""
import ast
import hashlib
import json
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W13/W13-03'
N=P/'fresh58_cli2_root_metadata_preparation_codex/900837a405be433f83524eddcc1c6bd8'
O=Path(__file__).resolve().parent
seen={}; checks=[]
def read(p):
    p=Path(p); p=p if p.is_absolute() else R/p
    b=p.read_bytes(); seen[str(p)]=b; return b
def pin(p,b=None):
    p=Path(p); p=p if p.is_absolute() else R/p
    if b is None:b=read(p)
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
def verify(r,n):
    b=read(r['path']);ck(n,len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def doc(p):return json.loads(read(p))
def put(n,v):
    b=(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (O/n).open('xb') as f:f.write(b)
    return pin(O/n,b)

mf=doc(N/'manifest.json');h=doc(N/'handoff.json')
ck('manifest-pin',pin(N/'manifest.json')['sha256']=='cc8209dc535f5bba682bea74bf741de3ad0b221d5edd393679af2ad1dca44b7c')
ck('manifest-count',len(mf['entries'])==mf['count']==14 and mf['self_excluded'] is True)
for i,r in enumerate(mf['entries']):verify(r,'MF-'+str(i))
ck('handoff-pin',pin(N/'handoff.json')['sha256']=='d23502bd2d85158c4ebd1e87b67844a3c38dc5a8c7c8bd973831a05d97248f7f')
for i,r in enumerate(h['new_module_refs']):verify(r,'module-'+str(i))
proofs=[doc(N/'source-delta.json'),doc(N/'wrapper-source-delta.json')]
ck('proof-cardinalities',len(proofs[0]['changes'])==2 and len(proofs[1]['changes'])==6)
oldgate='8b63b6cfd6d3bae72adc65e4fd5aa8c57fe3d81bf9bac0b00ab3977baf534b28'
newgate='6ff7a907980da9ffe50a7a2f3ba5669820cd1d99a820be476e5327abd0dec782'
oldhead='a510dbef4a7e08fb5c428df44c39b133f3ffa856'
newhead='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
module_name='metadata_pipeline.current58.proposed.py'
rows=[]
for proof in proofs:
    for item in proof['changes']:
        old=verify(item['original_ref'],'original-'+item['name']); new=read(N/item['name'])
        edits=item['exact_replacements']; restored=new
        for i,e in enumerate(reversed(edits)):
            before=e['before'].encode('utf-8'); after=e['after'].encode('utf-8')
            ck('unique-inverse:'+item['name']+':'+str(i),restored.count(after)==1)
            restored=restored.replace(after,before,1)
        ck('whole-byte-inverse:'+item['name'],restored==old)
        oa=ast.parse(old);na=ast.parse(new)
        count=None
        if item['name'] in ['build_binding.current58.proposed.py',module_name]:
            od=[x for x in oa.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))]
            nd=[x for x in na.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))]
            ck('all-definitions-AST:'+item['name'],[ast.dump(x,include_attributes=False) for x in od]==[ast.dump(x,include_attributes=False) for x in nd])
            ck('all-definitions-bytes:'+item['name'],[ast.get_source_segment(old.decode('utf-8'),x) for x in od]==[ast.get_source_segment(new.decode('utf-8'),x) for x in nd])
            count=len(nd)
            expected=[{'before':oldgate,'after':newgate}]
            if item['name']==module_name:expected.append({'before':oldhead,'after':newhead})
            ck('exact-three-authorized-constants:'+item['name'],edits==expected)
        else:
            calls=[n for n in ast.walk(na) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='main']
            want={'scope_builder.py':'scope','grant_preflight.py':'grant'}.get(item['name'],Path(item['name']).stem)
            ck('wrapper-dispatch:'+item['name'],len(calls)==1 and len(calls[0].args)==1 and isinstance(calls[0].args[0],ast.Constant) and calls[0].args[0].value==want)
            string_values=[n.value for n in ast.walk(na) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
            ck('wrapper-exact-module-path:'+item['name'],str(N/module_name) in string_values)
            ck('wrapper-exact-module-SHA:'+item['name'],pin(N/module_name)['sha256'] in string_values)
            ck('wrapper-no-pyc:'+item['name'],b'sys.dont_write_bytecode=True' in new)
        rows.append({'old_ref':item['original_ref'],'new_ref':pin(N/item['name'],new),'whole_byte_inverse':restored==old,'unchanged_definition_count':count})

builder=read(N/'build_binding.current58.proposed.py');pipeline=read(N/module_name)
ga=P/'fresh58_cli2_controller_revision_preparation_codex/48d76385c123478e90864ebbfc2ad24a/authorization_gate.current58.final.proposed.py'
gate=read(ga)
ck('selected-current58-gate',hashlib.sha256(gate).hexdigest()==newgate and len(gate)==30328)
for name,b in [('builder',builder),('pipeline',pipeline)]:
    top=ast.parse(b)
    values={n.targets[0].id:n.value.value for n in top.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant)}
    ck('gate-constant-match:'+name,values['V3_GATE_SHA']==newgate)
    if name=='pipeline':ck('SOURCE-current58',values['SOURCE']==newhead)
ck('failure430-prefix-kept',b"need(len(prefix)==430 and cp['failure_counters'][:430]==prefix" in pipeline)
ck('full-before-prefix-kept',b"desiredcp['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters']" in pipeline)
ck('canonical-four-before-and-immediate-grant',b"current four CAS" in pipeline and b"immediate pre-grant live four CAS" in pipeline)
ck('metadata-runtime-strict-success-marker',b"all_observed_inputs_pre_pinned" in pipeline and b"point_in_time" in pipeline)
ck('source-roster-two',b"['real-existing-open-readonly','real-existing-self-send']" in pipeline)
ck('review-via-future-path-no-SHA-cycle',b"safe(rreview['path'])==safe(a.controller_review_path)" in builder)
ck('preparation-not-execution',h['actual_candidate_runs']==0 and h['actual_canonical_writes']==0 and h['execution_authorized'] is False and h['source_acceptance'] is False and h['formal_increment']==0)
for p,b in list(seen.items()):ck('after-drift:'+p,Path(p).read_bytes()==b)
failed=[x for x in checks if not x['passed']]
audit=put('audit.json',{'schema':'researchos.fresh58-root-metadata-source-readonly-audit.v1','checks':checks,'count':len(checks),'failed':failed,'whole_byte_inverse_count':len(rows),'source_pairs':rows,'candidate_imports':0,'candidate_executions':0,'native_calls':0,'canonical_writes':0})
inputs=put('inputs.json',{'files':[pin(p,b) for p,b in sorted(seen.items())],'drift':[],'self_excluded':True})
decision='READY_SOURCE_PREPARATION_ONLY' if not failed else 'REQUEST_CHANGES'
review=put('review.json',{'schema':'researchos.fresh58-root-metadata-preparation-independent-review.v1','reviewer':'codex:/root/w05_merge_review','source_author':'codex:/root','nonauthor':True,'decision':decision,'requested_changes':failed,'builder_ref':pin(N/'build_binding.current58.proposed.py'),'metadata_engine_ref':pin(N/module_name),'metadata_pipeline_ref':pin(N/module_name),'module_refs':h['new_module_refs'],'wrapper_refs':[pin(N/n) for n in h['wrapper_names']],'preparation_manifest_ref':pin(N/'manifest.json'),'preparation_handoff_ref':pin(N/'handoff.json'),'selected_gate_ref':pin(ga),'source_delta_ref':pin(N/'source-delta.json'),'wrapper_delta_ref':pin(N/'wrapper-source-delta.json'),'audit_ref':audit,'inputs_ref':inputs,'source_commit':newhead,'source_parent':oldhead,'whole_byte_inverse_count':8,'allowed_code_changes':['builder V3_GATE_SHA -> selected current58 gate6ff7','pipeline SOURCE -> e2ee and V3_GATE_SHA -> selected current58 gate6ff7','six wrappers update only pinned module path/hash'],'protocol_unchanged':['all existing function bytes and AST in both modules','four-canonical CAS immediately around each original write sequence','strict module observation, metadata ABS projection and success marker','ROOT-relative serialized metadata refs and scopeRef','original430 and whole-current failure-prefix preservation','two held-case roster, all stop/caps/source/formal restrictions','preflight authority before exclusive auth leaf, second actual Git round and immediate pre-grant live-four check'],'required_future_binding':['Publish corrected fresh639 catalog/current58 authority with actual Root copies and live-canonical equality.','Materialize a new immutable scope template with catalog_ref populated; scope_build does not fill it from binding.','Stage six wrappers in a NEW Root registration namespace, bind all eight metadata refs ROOT-relative with actual SHA/bytes; add canonical ABS equivalent rows to runtime preapproved inventory.','Set actual current before tuple, explicit next tuple/origin cut, source-input rows, current runtime/compiler catalogs and five absent disjoint roots. Preserve source e2ee and parent a510.','Acquire independent full-scope review, prepare new immutable draft, acquire registration review, then actual Root run/seal/grant.','Use new Root outer metadata caller pins; original r331 BUILDER path/hash and scope hash are historical and must not be reused unchanged.','Actual fresh Go graph/compiler WORK/archive/exe/hFile closure and held2 execution remain unperformed by this review.'],'historical_note':'source-delta.json wrapper_changes_pending=true is an earlier preparation phase marker; separate sealed wrapper-source-delta, six actual wrappers and handoff establish completed static preparation. It is not execution evidence.','actual_candidate_imports':0,'actual_candidate_executions':0,'actual_canonical_writes':0,'actual_registration_executed':False,'source_acceptance':False,'fresh58_qualified':False,'execution_authorized':False,'formal_increment':0,'future_root_scope':None,'future_grant':None,'new_failure_origins':[]})
handoff=put('handoff.json',{'schema':'researchos.independent-review-handoff.v1','review_ref':review,'decision':decision,'checks':len(checks),'failed_checks':len(failed),'new_failure_origins':[],'status':'STOPPED'})
entries=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
manifest=put('manifest.json',{'schema':'researchos.immutable-public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'review_ref':review,'handoff_ref':handoff,'manifest_ref':manifest,'checks':len(checks),'failed_checks':len(failed),'decision':decision,'new_failure_origins':[]},ensure_ascii=False))
