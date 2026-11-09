import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parents[1]
C=B/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009'
Q=B/'checkpoint_r367_main_registration_v2_independent_review_codex/cp367v2r-01a11fad'
L=C/'root-postseal-live-950-20261009'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(r):
 assert pin(r['path'])==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
lr=dict(path=str((L/'live-context.actual.root.json').resolve()),sha256='9c68988b96b091c920f3873e7c8c2ad9c41c2212a6928615aa7f27d2e63d9291',bytes=1488)
mr=dict(path=str((L/'failure-origin.949.registration.root.json').resolve()),sha256='55208752514b4ebd9da4ce7ba336dafbc03fd880822755dd3c9cd77ea701bbf2',bytes=1075)
live=load(lr);mapping=load(mr)
source=load(dict(path=str((C/'HDF.json').resolve()),sha256='469de4a7176e25ef0d844824fb97bc02bf0afb3b79b5026f4b7474c24c5a65cb',bytes=2748))
review=load(dict(path=str((Q/'HDF.json').resolve()),sha256='4bb022d282498db9225fbb1b544753b73f1ba11223281424155e79e5a462e4ba',bytes=3827))
for doc in (source,review):
 mf=load(doc['manifest_ref'])
 for ref in mf['members']:read(ref)
facts=load(source['facts_ref']);post=load(dict(path=str((Q/'postseal.json').resolve()),sha256='e8147d47ec38b76f79bb411f0d50ecb6f24916eeaefbe1b058d70d2bb350d24b',bytes=693))
for ref in facts['canonical_refs']:read(ref)
origins=[load(x['origin_ref']) for x in live['pending']]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=dict(path=str(gp.resolve()),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
gm=types.ModuleType('live950reviewguard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(read(gr),str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 writer=read(source['writer_ref']);tree=ast.parse(writer)
 ns=dict(Path=Path,hashlib=hashlib,json=json)
 exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in ('require','pin','read','validate_live_context')],type_ignores=[]),'<pure-live950-validator>','exec'),ns)
 ck('real_source_validator_accepts',ns['validate_live_context'](live,facts)==live)
 ck('review_exact_source_binding',review['source_handoff_ref']==pin(C/'HDF.json') and review['source_manifest_ref']==source['manifest_ref'])
 ck('prior_qualification_exact',review['decision']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION')
 created=datetime.fromisoformat(live['created_utc']);seals=[datetime.fromtimestamp((Q/n).stat().st_mtime,timezone.utc) for n in ('HDF.json','MF.json','postseal.json')]
 ck('real_utc_after_prior_seal',created.tzinfo is not None and all(created>t for t in seals) and created<=datetime.now(timezone.utc))
 ck('cut947_next948_live950',live['source_cutoff']=={'highest_ordinal':947,'next_failure_ordinal':948} and live['next_original_failure_ordinal']==950)
 ck('complete_pending948_949_once',[v['ordinal'] for v in live['pending']]==[948,949] and len({v['origin_ref']['sha256'] for v in live['pending']})==2)
 o948,o949=origins
 ck('origin948_identity_all_exits_null',o948['ordinal']==948 and o948['tool']=='apply_patch' and all(o948[k] is None for k in ('outer_exit','python_exit','native_exit','model_exit')) and o948['count_once'] is True)
 ck('origin949_exact_b7b538_outer1',o949['result']['chunk_id']=='b7b538' and o949['result']['exit_code']==1 and 'Get-Content' in o949['args']['cmd'])
 ck('root949_mapping_exact',mapping['schema']=='researchos.root-original-failure-registration.v1' and mapping['issued_by']=='codex:/root' and mapping['ordinal']==949 and mapping['origin_ref']==live['pending'][1]['origin_ref'] and mapping['source_review_ref']==pin(Q/'HDF.json') and mapping['chunk_id']=='b7b538')
 ck('root949_qualification',mapping['actual_outer_exit']==1 and all(mapping[k] is None for k in ('actual_python_exit','actual_native_exit','actual_model_exit')) and mapping['original_calls']==1 and mapping['replay'] is False and mapping['counter_reset'] is False)
 ck('sealed_null_preserved',review['new_original_failures'][0]['ordinal'] is None and review['new_original_failures'][0]['origin_ref']==mapping['origin_ref'])
 ck('mapping_and_context_same_root_timestamp',mapping['created_utc']==live['created_utc'])
 save('freshness.json',dict(context_created_utc=created.isoformat(),prior_seal_mtimes_utc={name:t.isoformat() for name,t in zip(('HDF.json','MF.json','postseal.json'),seals)},checked_utc=datetime.now(timezone.utc).isoformat(),basis='Pinned prior seal plus filesystem UTC modification times and Root-issued context timestamp; no claim of cryptographic wall-clock attestation'))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_pins_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('qualification.json',dict(status='SOURCE_V2_FRESH_LIVE_CONTEXT_CONDITION_SATISFIED',context_ref=lr,mapping_ref=mr,source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=source['manifest_ref'],prior_independent_review_ref=pin(Q/'HDF.json'),root_registration_qualified=True,scope='Root one CP366/OW170 to CP367/OW171 administrative registration with exact reviewed v2 writer/facts/live950 context and current before pins; no Main adoption or formal acceptance',qualification_lapses_if='Any new original failure changes live state before invocation, any exact input or canonical before pin changes, or different context is supplied',new_original_failures=[],actual_registration_executed=False,Main_adopted=False,formal_case_accepted_delta=0,checks=len(checks),pins=len(pins)))
print(json.dumps(dict(status='SOURCE_V2_FRESH_LIVE_CONTEXT_CONDITION_SATISFIED',checks=len(checks),pins=len(pins),new_failures=0)))
