import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parents[1]
C=B/'checkpoint_r367_main_v2_binding_v4_source_root/cp367-bind-v4-20261009'
Q=B/'checkpoint_r367_main_v2_binding_v4_independent_review_codex/cp367v4r-01a11fad'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 assert pin(r['path'])==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
lr=dict(path=str((C/'live951-post-v4-review.root/live-context.actual.root.json').resolve()),sha256='1474f8629697997e230b426bd4a2fcefe2cdab6cd4a5b5057d0deaa40dc683bf',bytes=296)
live=load(lr)
source=load(dict(path=str((C/'HDF.json').resolve()),sha256='2864d5989c0b82c54bc1b81465e27656c68ff2ec8581b4b39096ae2543eeb467',bytes=2715))
review=load(dict(path=str((Q/'HDF.json').resolve()),sha256='95ab93dfd77646bebcba75b1f2f38ea1b8fb38022a80e2c63961b80f671c43b0',bytes=3495))
for h in (source,review):
 for r in load(h['manifest_ref'])['members']:read(r)
post=load(dict(path=str((Q/'postseal.json').resolve()),sha256='fb2018af5f29e0ff2a8632a4d65fe5c86886354623f6409452e21783e818152e',bytes=690))
facts=load(source['facts_ref']);writer=read(source['writer_ref'])
before=[read(r) for r in facts['canonical_refs']]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(dict(path=str(gp.resolve()),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('live951reviewguard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 ns=dict(Path=Path,hashlib=hashlib,json=json)
 exec(compile(ast.Module(body=[v for v in ast.parse(writer).body if isinstance(v,ast.FunctionDef) and v.name in {'require','pin','read','validate_live_context'}],type_ignores=[]),'<pure-live951-validation>','exec'),ns)
 ck('exact_v4_pure_validator_pass',ns['validate_live_context'](live,facts)==live)
 ck('source_review_binding_exact',review['source_handoff_ref']==pin(C/'HDF.json') and review['source_manifest_ref']==source['manifest_ref'] and review['decision']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION')
 ck('facts_writer_exact',source['facts_ref']['sha256']=='f0e358383f6a8c9702a2ffe1770b8d2a76ce1390764383fd02102836014d333d' and source['facts_ref']['bytes']==32485 and source['writer_ref']['sha256']=='40879ec125e975d0f9dddfc046976cedba744a022aa6c4cfba06ebedd2469e79' and source['writer_ref']['bytes']==17931)
 ck('cut950_next951_live951_pending_empty',live['source_cutoff']==dict(highest_ordinal=950,next_failure_ordinal=951) and live['next_original_failure_ordinal']==951 and live['pending']==[])
 ck('Root_actor',live['issued_by']=='codex:/root')
 created=datetime.fromisoformat(live['created_utc']);times={n:datetime.fromtimestamp((Q/n).stat().st_mtime,timezone.utc) for n in ('HDF.json','MF.json','postseal.json')}
 ck('fresh_context_after_review_seal',created.tzinfo is not None and all(created>t for t in times.values()) and created<=datetime.now(timezone.utc))
 ck('new14_cut_originals_preserved',[v['ordinal'] for v in facts['diagnostics']]==list(range(937,951)) and facts['registered_after']==948)
 ck('before_revisions366_170',json.loads(before[0])['revision']==366 and json.loads(before[1])['revision']==170)
 ck('all_four_before_refs_unchanged',[Path(r['path']).read_bytes() for r in facts['canonical_refs']]==before)
 save('freshness.json',dict(context_created_utc=created.isoformat(),review_seal_mtimes_utc={n:t.isoformat() for n,t in times.items()},checked_utc=datetime.now(timezone.utc).isoformat(),basis='Exact pinned review package, filesystem UTC modification times and Root-issued context timestamp'))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_exact_input_pins_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('checks.json',checks);save('input-pins.json',list(pins.values()))
save('qualification.json',dict(status='SOURCE_V4_FRESH_LIVE_CONTEXT_CONDITION_SATISFIED',context_ref=lr,source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=source['manifest_ref'],source_review_ref=pin(Q/'HDF.json'),facts_ref=source['facts_ref'],writer_ref=source['writer_ref'],canonical_before_refs=facts['canonical_refs'],root_once_administrative_registration_qualified=True,scope='One Root CP366/OW170 to CP367/OW171 registration using exact v4 writer/facts/live951 and unchanged four before refs. No Main adoption or formal acceptance granted.',qualification_lapses_if='Any new original failure changes Root live before invocation, or any exact bound input changes',checks=len(checks),pins=len(pins),new_original_failures=[],actual_registration_executed=False,Main_Canon_written=False,Native_Go_SQL_API_model_executed=False,formal_case_accepted_delta=0))
print(json.dumps(dict(status='SOURCE_V4_FRESH_LIVE_CONTEXT_CONDITION_SATISFIED',checks=len(checks),pins=len(pins),new_failures=0)))
