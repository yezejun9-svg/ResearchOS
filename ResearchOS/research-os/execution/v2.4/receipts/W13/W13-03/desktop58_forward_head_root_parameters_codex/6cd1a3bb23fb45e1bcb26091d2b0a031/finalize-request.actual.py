"""Root pure IO final request construction from sealed actual facts. No engine import, helper, Git, product or canonical write."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,os
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
CONFIG=json.loads(r'''{"partial_ref":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_forward_head_root_parameters_codex\\6cd1a3bb23fb45e1bcb26091d2b0a031\\root-facts.partial.json","sha256":"3c9bff2fbf02ecf2aecab53332643f14f49f9a16bb680efecc08e3d67cc80500","bytes":8862},"capture_manifest_ref":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop58_forward_head_root_parameters_codex\\6cd1a3bb23fb45e1bcb26091d2b0a031\\capture-inputs.manifest.json","sha256":"855c51471b3ff43f59ea5519a6aa0f441cfbd721c8a159c9adc40dd07c9e7973","bytes":2380},"code_refs":{"engine":{"path":"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a/forward_head_engine.selected.proposed.py","sha256":"b9318a1f361b9ed4aa42e1e21e41bb4eefd5909310a73f396820e1680286ef47","bytes":44596},"builder":{"path":"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a/build_forward_draft.selected.proposed.py","sha256":"69c9c94a9e1b46fc85312743cb1899c0948f0d3e1ade93c6eda97e054297ce75","bytes":1146}},"code_manifest_ref":{"path":"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a/manifest.json","sha256":"150f52178b664ae3e019b5c28dab445c0827ea9c6be84bd5b70204212f3e4240","bytes":9897},"code_handoff_ref":{"path":"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a/handoff.json","sha256":"66ed76d859c4e92668cc0d222b5ae378eb4ef279ae9d90ddf955f020b4cac006","bytes":3772}}''')
def need(v,m):
    if not v:raise RuntimeError(m)
def parse(b):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(b.decode('utf-8','strict'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def pin(v):
    p=Path(v).resolve();b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def raw(r):
    p=Path(r['path']).resolve()
    need(p.is_relative_to(ROOT),'Root request input boundary')
    for q in [p,*p.parents]:
        if os.path.lexists(q):need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'reparse ancestor')
    b=p.read_bytes()
    need(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'sealed input drift')
    return b
def save(name,d):
    with (OUT/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(OUT/name)
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and Path.cwd()==ROOT,'isolated flags/cwd')
f=parse(raw(CONFIG['partial_ref']));basis=parse(raw(f['basis_prepared_ref']))
r=parse(raw(f['source_closure_review_ref']));scope=parse(raw(r['scope_ref']))
runtime=parse(raw(f['runtime_resources_ref']));cut=parse(raw(f['origin_cut_ref']))
need(type(runtime) is dict and type(runtime['files']) is list and len(runtime['files'])==1212,'runtime public1212')
after_ref=pin(Path(r['manifest_ref']['path']).parent/'immutable-inputs.after.json')
after=parse(raw(after_ref));need(type(after) is list,'actual source after vector list')
canon={Path(x['path']).resolve() for x in f['canonical_before']}
items={}
def add(row):
    need(type(row) is dict and {'path','sha256','bytes'}<=set(row),'protected REF shape')
    p=Path(row['path']);p=p if p.is_absolute() else ROOT/p;p=p.resolve()
    if p in canon:return
    n={'path':str(p),'sha256':row['sha256'],'bytes':row['bytes']}
    key=str(p).casefold()
    need(key not in items or items[key]==n,'conflicting immutable pin for same path')
    items[key]=n
for group in [basis['immutable_inputs'],after,runtime['files'],f['original_copy_refs'],list(CONFIG['code_refs'].values()),f['source_closed_refs']]:
    need(type(group) is list,'input groups are lists')
    for row in group:add(row)
for row in [CONFIG['partial_ref'],CONFIG['capture_manifest_ref'],CONFIG['code_manifest_ref'],CONFIG['code_handoff_ref'],f['basis_prepared_ref'],f['origin_cut_ref'],f['source_closure_review_ref'],f['source_closure_manifest_ref'],f['runtime_resources_ref'],f['toolchain_lock_ref'],f['helper_ref'],scope['status_ref'],after_ref,pin(__file__)]:
    raw(row);add(row)
for row in cut['origins']:raw(row['evidence_ref']);add(row['evidence_ref'])
for row in CONFIG['code_refs'].values():raw(row)
union=sorted(set(scope['shared38_paths']+scope['cli8_paths']+r['source_paths']))
need(len(union)==58,'actual current58 membership')
for rel in union:
    current=pin(ROOT/rel);add(current)
need(all(str((ROOT/rel).resolve()).casefold() in items for rel in union),'complete current58 protected')
need(raw(scope['status_ref'])==raw(f['status_ref']),'same actual old13 status bytes')
for live,copied in zip(f['canonical_before'],f['original_copy_refs']):
    need(raw(live)==raw(copied),'current canonical four exact immutable copies')
q={k:f[k] for k in ['registration_namespace','run_uuid','timestamp','before_tuple','after_tuple','head_before','head_after','canonical_before','original_copy_refs','origin_cut_ref','source_closure_review_ref','source_closure_manifest_ref','old_deleted_paths','runtime_resources_ref','toolchain_lock_ref','helper_ref']}
q.update(schema='researchos.desktop58-forward-head-request.v1',actor='codex:/root',authorized=False,source_acceptance=False,formal_increment=0,new_execution_grant=None,status_ref=scope['status_ref'],code_refs=CONFIG['code_refs'],immutable_inputs=list(items.values()))
need(not Path(q['registration_namespace']).exists(),'fresh registration namespace')
request_ref=save('root-request.actual.json',q)
audit_ref=save('root-request.construction.json',{'request_ref':request_ref,'partial_facts_ref':CONFIG['partial_ref'],'input_capture_manifest_ref':CONFIG['capture_manifest_ref'],'protected_immutable_refs':len(items),'actual_current58_paths':union,'status_ref_preserves_original_source_scope_identity':True,'partial_after_status_bytes_equal_original_source_status':True,'canonical_writes':0,'engine_helper_Git_product_calls':0,'actual_registration_executed':False,'source_acceptance':False,'formal_increment':0})
mf=save('root-request.manifest.json',{'entries':[request_ref,audit_ref,pin(__file__)],'count':3,'self_excluded':True,'formal_increment':0})
print(json.dumps({'request_ref':request_ref,'audit_ref':audit_ref,'manifest_ref':mf,'immutable_count':len(items),'planned_before':q['before_tuple'],'planned_after':q['after_tuple'],'canonical_writes':0,'engine_imports':0,'actual_registration_executed':False},ensure_ascii=False))
