from pathlib import Path
import hashlib, json, importlib.util
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=B/'historical20_r2_caller_independent_review_codex/h20r2-caller-01a11ee7'
refs={};checks=[]
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def norm(ref):return dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
def read(ref):
 actual=pin(ref['path']);assert actual==norm(ref);refs[actual['path']]=actual;return Path(actual['path']).read_bytes()
def obj(ref):return json.loads(read(ref))
def direct(p):return obj(pin(p))
def members(m):return list(m['members'].values()) if isinstance(m['members'],dict) else m['members']
c=direct(O/'packet/005/source.integration.choice.json');base=direct(c['base_current49']);P=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
sources={Path(ref['path']).relative_to(P).as_posix():norm(ref) for ref in obj(base['formatted_source_ref'])}
for item in c['source_components'][:-1]:
 candidate=B/item['candidate_namespace']/'candidate-root'
 for ref in members(obj(item['source_manifest'])):
  p=Path(ref['path'])
  if p.is_relative_to(candidate):sources[p.relative_to(candidate).as_posix()]=norm(ref)
t11=obj(c['actual_T11_overlay_ref'])['sources'];final=direct(O/'composition.json')['sources']
for ref in list(sources.values())+list(t11.values())+list(final.values()):read(ref)
checks.append(dict(name='exact T11 58 composition',passed=len(sources)==58 and sources=={k:norm(v) for k,v in t11.items()},supersedes='checks.json false caused by relative_path metadata'))
checks.append(dict(name='non H20 unchanged from T11',passed=all(norm(final[k])==norm(v) for k,v in t11.items() if k not in c['h20_candidate_paths']),supersedes='checks.json false caused by relative_path metadata'))
fresh={k:not Path(c[k]).exists() for k in ('fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment')};checks.append(dict(name='four fresh paths remain absent',passed=all(fresh.values())))
can=direct(O/'canonical.observed.json')
for ref in can['refs'].values():read(ref)
checks.append(dict(name='canonical still exact CP364',passed=json.loads(read(can['refs']['checkpoint']))['revision']==364))
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
s=importlib.util.spec_from_file_location('guard',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);g=m.SourceReadGuard()
try:g.acquire(list(refs.values()))
finally:cleanup=g.close()
checks.append(dict(name='recheck handles released',passed=cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0))
result=dict(checks=checks,input_refs=list(refs.values()),guard=cleanup,fresh=fresh,normalization='identity is absolute resolved path, SHA256, bytes; relative_path remains provenance metadata',source_changed=False)
with (O/'reference-identity-recheck.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,inputs=len(refs),actual_Git_Go_SQL_native_API=False),ensure_ascii=False))
