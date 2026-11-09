"""Independent public-input readiness review; never invokes operation caller."""
import ast,hashlib,json,os,subprocess,sys,difflib
from pathlib import Path
E=Path(__file__).parent
P=E.parent.parent.parent/'native25_actual_root_codex/20261014-current-chat'
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(Path(p).resolve()),sha256='sha256:'+hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def write(n,v):
 with (E/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=True,indent=2)
cfgpath=P/'positive-replay-02/controller.public.config.json';cfg=read(cfgpath)
assert ref(cfgpath)['sha256']=='sha256:021ee123c2b05facd7fca0c4e945792eb75271cad720c1a4dcb81c458d2fa0e6'
assert ref(cfgpath)['bytes']==1155681
caller=P/'positive-replay-02/root_concrete_operation.py';template=P/'root_concrete_operation_v2.template.py'
assert ref(caller)['sha256']==ref(template)['sha256']=='sha256:5e469c5bbe6534a9c9c51f36b9775a56df7dbbbff46ea69bd4e5ba2964efaffa'
old=read(P/'positive-replay-01/controller.public.config.v2.json')
def mapped(v):
 if isinstance(v,str):return v.replace('positive-replay-01','positive-replay-02')
 if isinstance(v,list):return [mapped(x) for x in v]
 if isinstance(v,dict):return {k:mapped(x) for k,x in v.items()}
 return v
nonfrozen_delta={k:{'old':old.get(k),'new':v} for k,v in cfg.items() if k!='FrozenInputs' and mapped(old.get(k))!=v}
assert set(nonfrozen_delta)=={'HarnessConfig'}
oldhc=read(old['HarnessConfig']['path']);newhc=read(cfg['HarnessConfig']['path'])
assert mapped(oldhc)==newhc
pins={str(Path(v['path'])).casefold():v for v in cfg['FrozenInputs']}
oldpins={str(Path(mapped(v['path']))).casefold():mapped(v) for v in old['FrozenInputs']}
added=[v for k,v in pins.items() if k not in oldpins];removed=[v for k,v in oldpins.items() if k not in pins]
changed=[{'old':oldpins[k],'new':v} for k,v in pins.items() if k in oldpins and oldpins[k]!=v]
assert len(pins)==4375 and len(added)==3 and len(removed)==1 and len(changed)==1
assert {Path(v['path']).name for v in added}=={'prepare_positive02.py','root_concrete_operation.py','root_concrete_operation_v2.template.py'}
assert Path(removed[0]['path']).name=='prepare_positive.py'
assert Path(changed[0]['new']['path']).name=='harness.public.config.json'
for v in cfg['FrozenInputs']:assert ref(v['path'])==v
src=caller.read_text(encoding='utf8');tree=ast.parse(src)
signbranch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="sys.argv[1] == 'sign'")
assert len(signbranch.body)==5
checks=ast.Module(body=signbranch.body[1:3],type_ignores=[])
cases=[]
for label,path,expected in [('forward','C:/public-fixture/path.txt',True),('backslash',r'C:\public-fixture\path.txt',True),('relative','public-fixture/path.txt',False),('drive-relative','C:public-fixture/path.txt',False),('unc',r'\\public-server\public-share\path.txt',False),('device',r'\\?\C:\public-fixture\path.txt',False)]:
 scope={'os':os,'Path':Path,'runtime_private':path}
 try:exec(compile(checks,'public-only-path-check','exec'),scope);accepted=True
 except ValueError:accepted=False
 assert accepted==expected
 cases.append({'case':label,'accepted':accepted,'normalized_public_path':scope['runtime_private']})
probe=(E.parent/'execution-readiness/context_probe_v2.py').read_text(encoding='utf8').replace('positive-replay-01/controller.public.config.v2.json','positive-replay-02/controller.public.config.json').replace('f21d508263674ca57672fddf2db897e78ffd06b355a6512acc47738b46f2c7fc','021ee123c2b05facd7fca0c4e945792eb75271cad720c1a4dcb81c458d2fa0e6')
with (E/'context_probe_case02.py').open('x',encoding='utf8') as f:f.write(probe)
contexts=[]
for name,extra in [('fresh',[]),('after-real-readonly-child',['--reviewer-imports'])]:
 args=[sys.executable,'-B','-X','utf8',str(E/'context_probe_case02.py'),*extra]
 result=subprocess.run(args,capture_output=True)
 (E/(name+'.stdout.raw.json')).write_bytes(result.stdout);(E/(name+'.stderr.raw.txt')).write_bytes(result.stderr)
 context=json.loads(result.stdout);assert result.returncode==0 and context['context_result']=='PASS' and not context['missing_runtime_paths']
 contexts.append({'label':name,'argv':args,'exit_code':result.returncode,'result':context})
diff=''.join(difflib.unified_diff((P/'prepare_positive.py').read_text(encoding='utf8').splitlines(True),(P/'prepare_positive02.py').read_text(encoding='utf8').splitlines(True),fromfile='prepare_positive.py',tofile='prepare_positive02.py'))
(E/'prepare.diff.txt').write_text(diff,encoding='utf8')
write('review-result.json',{'state':'PUBLIC_READINESS_CASE02_PASS','config_ref':ref(cfgpath),'caller_ref':ref(caller),'template_ref':ref(template),'prepare_ref':ref(P/'prepare_positive02.py'),'verified_pins':len(pins),'nonfrozen_delta':nonfrozen_delta,'frozen_added':added,'frozen_removed':removed,'frozen_changed':changed,'harness_namespace_only_change':True,'synthetic_path_checks':cases,'contexts':contexts,'scope':'All inputs public. Exact normalization statements executed only with invented public paths. Caller never invoked; no private contents, keys, DPAPI, signing, publishing, fixture release, product DB or Root approval. Existing native anti-reparse predicate and hold unchanged. No Native PASS.','formal_increment':0,'formal_cases_accepted':0,'formal_cases_total':42,'parents_open':22})
print(json.dumps({'state':'PUBLIC_READINESS_CASE02_PASS','verified_pins':len(pins),'report':ref(E/'review-result.json')}))
