from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parent;A=R.parent/'product-v1-source-context-author-20261104'
REPO=Path('D:/作品集/ResearchOS/research-os');WT=REPO/'.local/worktrees/product-v1-source-context-20261104'
GO=REPO/'.local/tools/go1.27.1/go/bin/go.exe'
MOD=R.parent/'cp586-continuation/production-binding-review/run-01/private/gopath/pkg/mod'
CACHE=R.parent/'product-v1-backend-independent-qa-20261104/run-01/private/cache'
PINS={'final/source-manifest.json':'c4c643b5848304241b9d714b3d2860465c1a45892cda12d2b4fba6060d5cba8f','final/freeze.json':'3b4ea667463cbedc1d794d7b46c572d0f10a641eaa397589d2c65a7697c9473e','final/summary.json':'657f783951cde8996d8ab7042b37e43b953a8559eb352dc7fd20e73ae750a0a8','diagnostics.json':'04911cb32fb7a2e1ed666651e21baffed5f94daabbf08462ee553d07381d8bc4','final/EVIDENCE-MANIFEST.json':'358a0cf4f6ecbcbc62227be12d96a91a29630d18bc36c0cc5b0cf9355ad7323f'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
 p=R/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def prepare():
 for name,pin in PINS.items():assert sha(A/name)==pin,name
 m=json.loads((A/'final/source-manifest.json').read_bytes());assert m['source_count']==3 and m['author_stopped_source_changes']
 assert sha(GO)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490';assert MOD.is_dir() and CACHE.is_dir()
 source={};replace={}
 for row in m['pins']:
  rel=row['path'];pin=row['sha256'];assert sha(A/'final/source'/rel)==pin and sha(WT/rel)==pin,rel
  target=R/'source'/rel;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/'final/source'/rel).read_bytes());source[rel]=pin;replace[str(WT/rel)]=str(target)
 replace[str(WT/'adapters/runtime/independent_source_context_test.go')]=str(R/'independent_test.go')
 for name in PINS:
  target=R/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/name).read_bytes())
 for name in ['attempt-01/test.jsonl','attempt-01/test.result.json','attempt-02/test.jsonl','attempt-02/test.result.json','attempt-03/command.json']:
  target=R/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/name).read_bytes())
 save('overlay.json',{'Replace':replace});save('inputs.json',{'source_sha256':source,'base_head':m['base_head'],'author_pins':PINS,'go':str(GO),'go_sha256':sha(GO),'go_mod_sha256':sha(WT/'go.mod'),'go_sum_sha256':sha(WT/'go.sum'),'module_input_root':str(MOD),'own_reused_build_cache':str(CACHE),'own_test_sha256':sha(R/'independent_test.go'),'formal_increment':0})
 print(json.dumps({'prepared':True,'exact3':True,'C_snapshot_overlay':True}))
def check():
 i=json.loads((R/'inputs.json').read_bytes())
 for rel,pin in i['source_sha256'].items():assert sha(R/'source'/rel)==pin,rel
 assert sha(R/'independent_test.go')==i['own_test_sha256']
 assert sha(WT/'go.mod')==i['go_mod_sha256'] and sha(WT/'go.sum')==i['go_sum_sha256'];return i
def run(name,args):
 check()
 for sub in ['tmp','profile','appdata','localappdata','gopath']:(R/'private'/sub).mkdir(parents=True,exist_ok=True)
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC'] if k in os.environ}
 env.update({'PATH':str(GO.parent)+os.pathsep+str(Path(env['SystemRoot'])/'System32'),'USERPROFILE':str(R/'private/profile'),'HOME':str(R/'private/profile'),'APPDATA':str(R/'private/appdata'),'LOCALAPPDATA':str(R/'private/localappdata'),'TEMP':str(R/'private/tmp'),'TMP':str(R/'private/tmp'),'GOTMPDIR':str(R/'private/tmp'),'GOCACHE':str(CACHE),'GOMODCACHE':str(MOD),'GOPATH':str(R/'private/gopath'),'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOENV':'off','GOWORK':'off','CGO_ENABLED':'0','GOTELEMETRY':'off','GOVCS':'*:off','GOFLAGS':'-mod=readonly','GOMAXPROCS':'2'})
 cmd=[str(GO)]+args
 save(name+'.command.json',{'argv':cmd,'cwd':str(WT),'environment':env,'controller_sha256':sha(Path(__file__)),'overlay_sha256':sha(R/'overlay.json'),'class':'FROZEN_EXACT3_OVERLAY_ACTUAL_OWNED_GO_FAKE_PROCESS_FRESH_DB_NO_REAL_CODEX_MODEL_AUTH_OLD_DB'})
 with (R/(name+'.stdout.raw')).open('xb') as out,(R/(name+'.stderr.raw')).open('xb') as err:code=subprocess.run(cmd,cwd=WT,env=env,stdout=out,stderr=err,timeout=170).returncode
 counts={key:0 for key in ['run','pass','fail','skip']};roster=[]
 for line in (R/(name+'.stdout.raw')).read_bytes().splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if v.get('Test') and v.get('Action') in counts:counts[v['Action']]+=1
  if v.get('Test') and v.get('Action') in ['pass','fail','skip']:roster.append({'package':v.get('Package'),'test':v['Test'],'action':v['Action']})
 check();save(name+'.result.json',{'exit_code':code,'counts':counts,'roster':roster,'stdout_sha256':sha(R/(name+'.stdout.raw')),'stderr_sha256':sha(R/(name+'.stderr.raw')),'formal_increment':0});print(json.dumps({'phase':name,'exit_code':code,'counts':counts}));return code
def readback():
 i=check()
 for rel,pin in i['source_sha256'].items():assert sha(WT/rel)==pin and sha(A/'final/source'/rel)==pin,rel
 save('no-drift.json',{'source_sha256':i['source_sha256'],'C_author_and_current_exact3_match':True,'go_module_inputs_unchanged':True,'formal_increment':0});print(json.dumps({'no_drift':True,'sha256':sha(R/'no-drift.json')}))
if __name__=='__main__':
 p=sys.argv[1]
 if p=='prepare':prepare()
 elif p=='focused':sys.exit(run('focused',['test','-json','-mod=readonly','-p=1','-parallel=1','-count=1','-vet=off','-timeout=135s','-overlay='+str(R/'overlay.json'),'-run','^(TestCodexHarness(ExecutionSourceContext|ExecutionInputBudget|FixedArguments|NativeLifecycle)$|TestHarness(CoordinatorFakeChain|UnknownTransitionAtomic)$|TestIndependentSourceContext(Prelaunch|ActualStdin)$)','./adapters/runtime','./internal/domain']))
 elif p=='vet':sys.exit(run('vet',['vet','-mod=readonly','-p=1','-overlay='+str(R/'overlay.json'),'./adapters/runtime','./internal/domain']))
 elif p=='readback':readback()
