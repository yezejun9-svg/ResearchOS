import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
C=Path(__file__).resolve().parent.parent
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/product-v1-build-14-20261105'
B=R/'execution/product-v1/receipts/single-harness-20261104/build14-scope'
S=C/'product-v1-owned-verification-20261104/scopes/product-v1-build-14.json'
P=C/'product-v1-build14-prep-rev2-20261105'
seen={}
def sha(p):
 p=Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();seen[str(p)]=h;return h
def read(p):
 sha(p);return json.loads(Path(p).read_bytes())
def ref_head(root):
 d=root/'.git'
 if d.is_file():d=(root/d.read_text(encoding='utf8').strip().removeprefix('gitdir: ')).resolve()
 common=d
 if (d/'commondir').is_file():common=(d/(d/'commondir').read_text(encoding='utf8').strip()).resolve()
 text=(d/'HEAD').read_text(encoding='utf8').strip()
 if not text.startswith('ref: '):return text
 ref=text[5:]
 for base in (d,common):
  path=base/ref
  if path.is_file():return path.read_text(encoding='utf8').strip()
 packed=(common/'packed-refs').read_text(encoding='utf8')
 return next(row.split()[0] for row in packed.splitlines() if row and not row.startswith(('#','^')) and row.split()[1]==ref)

scope=read(S);reg=read(B/'registration.json');binding=read(B/'registration-binding.json')
assert sha(S)==binding['scope_sha256']=='3338c07aa9fbcec4f96c149265b6865aae2d8e5121ecc9c15ce6313f417489fa'
assert reg['status']==binding['status']=='REGISTERED_NOT_EXECUTED'
assert reg['main_head']==binding['main_head']==ref_head(R)==ref_head(W)=='360c3eefd06ba82255352357c05ece00dae00d3a'
assert reg['main_checkpoint']==693
state=read(R/'execution/product-v1/state.json')
pins={k:v for row in state['integrated_source'] for k,v in row['source_sha256'].items()}
union=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert pins==reg['source_sha256'] and len(pins)==70
assert union==reg['source_union_sha256']==binding['source_union_sha256']=='954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2'
for ref,h in pins.items():assert sha(R/ref)==sha(W/ref)==h,ref
assert len(scope['inputs'])==101
for row in scope['inputs']:assert sha(row['path'])==row['sha256'],row['path']
outer={str(Path(row['path'])).casefold():row['sha256'] for row in scope['inputs']}
for ref,h in pins.items():assert outer[str(W/ref).casefold()]==h
assert outer[str(B/'registration.json').casefold()]==sha(B/'registration.json')
assert scope['controller_sha256']==sha(C/'product-v1-owned-verification-20261104/owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert sha(scope['executable'])==scope['executable_sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
assert scope['scope_id']=='product-v1-build-14' and scope['purpose']=='build'
assert Path(scope['cwd'])==W
assert scope['argv']==['-B','-X','utf8',str(P/'build_desktop_serial14.py'),str(W/'apps/desktop/build-development.py'),*reg['builder_argv']]
assert reg['builder_sha256']==sha(W/'apps/desktop/build-development.py')=='8654e7955c12de11a80149d6cdfcb0e58d8ff4df69cadc5fc9d70cd97fe4f8e3'
manifest=read(P/'MANIFEST.json');review=read(C/'product-v1-build14-rev2-independent-review-20261105/REVIEW.json')
assert sha(P/'MANIFEST.json')==review['candidate_manifest']['sha256']=='d4cfcd25a3554703d9a1cfbbd40b1ba357f025e1d7c9a7167111f839afb82dff'
for row in manifest['files']:assert sha(P/row['path'])==row['sha256']
for ref,h in manifest['fixed_external_sha256'].items():assert sha(Path(ref) if Path(ref).is_absolute() else C/ref)==h
assert reg['gomaxprocs']==1 and "os.environ['GOMAXPROCS'] = '1'" in (P/'build_desktop_serial14.py').read_text(encoding='utf8')
limits={'timeout_seconds':1200,'process_limit':48,'memory_mib':6144,'max_raw_bytes':67108864,'cleanup_seconds':5,'graceful':'none','grace_seconds':0}
for key,value in limits.items():assert scope[key]==value
assert scope['env']=={'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off'}
qual=C/'product-v1-native-qualification-中文-root-01'
helper=C/'product-v1-native-helper-build01/buildout/qualification-helper.exe'
assert Path(reg['qualification_root'])==qual and Path(reg['qualification_helper'])==helper
assert sha(helper)==sha(qual/'S/qualification-helper.exe')==reg['qualification_helper_sha256']=='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
assert sorted(p.name for p in (qual/'S').iterdir())==['README.md','probe.txt','qualification-helper.exe']
for name,h in reg['qualification_canaries_sha256'].items():assert sha(qual/'S'/name)==h==outer[str(qual/'S'/name).casefold()]
assert reg['qualification_canaries_sha256']=={'README.md':'bbf19460eb93f739649abce74a96c045bb03dfebe500220d6b1c7c75e768dbb9','probe.txt':'c22341092e51220d3dc26a8a13dbec78b9e65b40096cf1365363cf8471bddfd3'}
cp=read(R/'execution/v2.4/checkpoint.json')
assert cp['revision']==694 and cp['current_Main_HEAD']==reg['main_head']
result=dict(status='REGISTERED_INPUTS_VERIFIED_RUNTIME_AUDIT_PENDING',at=datetime.now(timezone.utc).isoformat(),scope_sha256=sha(S),registration_sha256=sha(B/'registration.json'),head=reg['main_head'],head_method='Read-only .git HEAD and refs resolution; no Git execution',checkpoint=694,scope_input_rows=101,unique_input_paths=len(outer),source_count=70,source_union_sha256=union,source_Main_and_WT_hashes_match=True,recipe_review_pins_match=True,helper_and_canaries_match=True,exact_argv_match=True,gomaxprocs=1,limits=limits,registration_status_semantics='Immutable original registration remains REGISTERED_NOT_EXECUTED even while owned run executes; do not rewrite bound input',runtime='Root owns session4445; not polled by reviewer; producer outputs not inspected yet',formal_increment=0,product_acceptance_increment=0,D_writes=0,product_or_test_execution=0,model_calls=0,evidence_sha256=seen)
with (O/'PREFLIGHT.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='evidence_sha256'},ensure_ascii=False,indent=2))
