import ast,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent;R=B.parents[4]
S=B/'integration_codex/native-positive-root-api-6957929b0a784a91/root_public_api.actual.py'
V=B/'integration_codex/native-positive-serve-v2-root-75dc3afca9b34a99/serve_one_positive.actual_owned.py'
C=B/'integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller.public.config.json'
refs={}
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def add(r):
 r=dict(path=str(Path(r['path'])),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);k=r['path'].casefold()
 assert k not in refs or refs[k]==r
 refs[k]=r
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ('path','sha256','bytes')):add(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
def read(p):
 add(pin(p));return json.loads(Path(p).read_bytes())
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
add(pin(S));add(pin(V))
assert pin(S)['sha256']=='f3f4aa28ec23cfe1c73381ff7a82fbd6f8fb0feb15c0e3cc74fea80d21dea7e8' and pin(S)['bytes']==11261
assert pin(V)['sha256']=='e686e3c523829f959f091fcdeee0ee9e1f8fdf0ac42638bd83c7a306f29db084'
cfg=read(C);walk(cfg);assert pin(C)['sha256']=='9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc'
hc=read(cfg['HarnessConfig']['path']);walk(hc)
root=Path(hc['BuildRoot'])
files=[root/'internal/domain/contracts.go',root/'internal/domain/backup_prepared_abandonment_upgrade.go',root/'internal/canonical/jcs.go',root/'migrations/sqlite/0005_runtime.sql',root/'migrations/sqlite/0004_sources.sql',R/'.local/tools/go1.27.1/go/src/encoding/json/jsontext/value.go',R/'.local/tools/go1.27.1/go/src/encoding/json/jsontext/options.go']
for p in files:add(pin(p))
key=B/'integration_codex/recoveryauthority-key-provision-root-9b42b8e7072a40b1/key-provision.closed.json'
kr=pin(key);assert kr['sha256']=='873953117beb0f5730674d130e49c18502b6e5821ea37f5658af3c80f1e7d5fe' and kr['bytes']==2375;add(kr)
# Only metadata pin is recorded; private-resource contents/paths are not decoded here.
source=S.read_text();tree=ast.parse(source);v2=ast.parse(V.read_bytes())
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
oldfunctions={n.name:n for n in v2.body if isinstance(n,ast.FunctionDef)}
for name in ('pin_raw','pin','plain','checked','save','module_raw','unique','runtime_pins'):
 assert ast.dump(functions[name],include_attributes=False)==ast.dump(oldfunctions[name],include_attributes=False)
assert source.splitlines()[:51]==V.read_text().splitlines()[:51]
assert 'canonical.JSON(Bytes(v))' in files[0].read_text()
assert 'v.Canonicalize()' in files[2].read_text()
assert 'epoch>0' in files[3].read_text() and "page_cursor_out<>''" in files[4].read_text()
calls=[dict(line=n.lineno,call=ast.unparse(n)) for n in ast.walk(tree) if isinstance(n,ast.Call)]
assert any(c['line']==138 and "'?mode=ro'" in c['call'] for c in calls)
assert any(c['line']==139 and "PRAGMA query_only=ON" in c['call'] for c in calls)
assert any(c['line']==90 and 'controller.sign_reviewed(config_ref, approval_ref, issuer_path)'==c['call'] for c in calls)
assert not any('issuer_path' in c['call'] for c in calls if c['call'].startswith(('save(','print(','pin(','Path(')))
jcs_example=json.dumps(['CHECK(epoch>0)'],ensure_ascii=False,separators=(',',':'))
wrong_example=jcs_example.replace('>',r'\u003e')
assert jcs_example!=wrong_example
example=dict(input=['CHECK(epoch>0)'],expected_JCS_string_only_bytes_hex=jcs_example.encode().hex(),api_current_bytes_hex=wrong_example.encode().hex(),expected_JCS_sha256=hashlib.sha256(jcs_example.encode()).hexdigest(),api_current_sha256=hashlib.sha256(wrong_example.encode()).hexdigest(),basis='Independent illustrative string-only encoding comparison; not Go/native/SQL target execution.')
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
for r in canonical:add(r)
assert canonical[0]['sha256']=='71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f'
for r in refs.values():assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=list(refs.values()),api_source_ref=pin(S),v2_launch_ref=pin(V),config_ref=pin(C),canonical_refs=canonical,unchanged_bootstrap_functions=True,unchanged_first_51_lines=True,illustrative_hash_mismatch=example,private_metadata_pin_only=kr,all_current_pins_match=True,static_calls=calls,SQL_executions=0,Go_executions=0,private_key_reads=0,target_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),drift=0,hash_mismatch_example=example,target_executions=0,new_mechanical_errors=0)))

