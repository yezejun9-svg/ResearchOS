import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
ap=argparse.ArgumentParser();ap.add_argument('--id',required=True);ap.add_argument('--scope-ref',required=True);ap.add_argument('--pattern',required=True);ap.add_argument('--package',action='append',required=True);ap.add_argument('--overlay');ap.add_argument('--extra-input',action='append',default=[]);a=ap.parse_args();assert re.fullmatch('[a-z0-9-]{10,100}',a.id) and len(a.pattern)<2048 and all(re.fullmatch(r'\./[A-Za-z0-9_/-]+',p) for p in a.package)
lease=ROOT/a.scope_ref;s=read(lease);wt=Path(s['worktree']);assert wt.is_relative_to(ROOT/'.local/worktrees') and not (CONTROL/'runs'/a.id).exists();out=HERE/(a.id+'-registration');assert not out.exists()
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';assert sha(go)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490';assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
files=[wt/p for p in s['production_paths']+s['test_paths']]+[wt/'go.mod',wt/'go.sum',lease,Path(__file__)]+[ROOT/p for p in s.get('contract_pins',{})]+[Path(p) for p in a.extra_input]
for p,h in s.get('contract_pins',{}).items():assert sha(ROOT/p)==h
args=['test','-v','-count=1','-run',a.pattern]
if a.overlay:
 ov=Path(a.overlay);assert ov.is_relative_to(HERE);files.append(ov);replace=read(ov)['Replace']
 for old,new in replace.items():
  assert Path(old).is_relative_to(wt) and new;target=Path(new);assert target.is_relative_to(ROOT/'.local/worktrees') or target.is_relative_to(HERE);files.append(target)
 args+=['-overlay',str(ov)]
args+=a.package;files=list({str(p.resolve()).lower():p for p in files}.values());out.mkdir();cache=out/'gocache';tmp=out/'gotmp';cache.mkdir();tmp.mkdir()
scope=dict(schema='researchos.owned-windows-run/1',scope_id=a.id,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(go),executable_sha256=sha(go),argv=args,cwd=str(wt),timeout_seconds=600,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=48,memory_mib=6144,max_raw_bytes=8*1024*1024,env=dict(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOWORK='off',CGO_ENABLED='0',GOMODCACHE=str(ROOT/'.local/tools/gopath/pkg/mod'),GOCACHE=str(cache),GOTMPDIR=str(tmp)),inputs=[dict(path=str(p),sha256=sha(p)) for p in files])
sp=CONTROL/'scopes'/f'{a.id}.json';put(sp,scope);reg=dict(status='REGISTERED_NOT_EXECUTED',scope_id=a.id,scope_path=str(sp),scope_sha256=sha(sp),source_scope_ref=a.scope_ref,source_scope_sha256=sha(lease),model_tasks=0,native_invocations=0,fixture_only=True,automatic_retry=0,formal_increment=0,product_increment=0);put(out/'REGISTRATION.json',reg)
print(json.dumps(reg))
