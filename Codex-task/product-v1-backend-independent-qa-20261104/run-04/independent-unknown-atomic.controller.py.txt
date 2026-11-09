from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
WT=ROOT/'.local/worktrees/product-v1-backend-20261104'
AUTHOR=HERE.parent/'product-v1-backend-author'
RUN=HERE/'run-04'
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
MOD=HERE.parent/'cp586-continuation/production-binding-review/run-01/private/gopath/pkg/mod'
PINS={
 'final-04/source-manifest.json':'ecc1e5574588d9de6ac450259eb363e5e2bea1fb1b7e716e3e9014c0ca287572',
 'final-04/freeze.json':'712fa19353787bd4357d52179f931972c14a3a60a60346b737cc92d3f60f1167',
 'final-04/summary.json':'85db44d9b933bb760c4f05c73f6a4f2989573ac6708b5d55a73182fc1f8e3d35',
 'diagnostics-04.json':'31fca56d81984a1eeba0baeabd2789b2cef08f173b190550c89e46039415ed09'}
EXTRAS={'adapters/runtime/independent_harness_boundary_test.go':'independent_driver_final_test.go',
        'internal/domain/independent_harness_authority_test.go':'independent_domain_test.go',
        'internal/api/independent_harness_transport_test.go':'independent_api_test.go',
        'internal/domain/independent_unknown_atomic_test.go':'independent_atomic_test.go'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
 p=RUN/name
 assert not p.exists(),'Never overwrite evidence '+str(p)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def prepare():
 assert not RUN.exists(),'Inspect existing run before retry'
 for name,pin in PINS.items():assert sha(AUTHOR/name)==pin,name
 m=json.loads((AUTHOR/'final-04/source-manifest.json').read_bytes())
 sc=json.loads((HERE/'prepared-inputs/scope.json').read_bytes())
 assert len(m['pins'])==18 and set(x['path'] for x in m['pins'])==set(sc['production_paths']+sc['test_paths'])
 assert m['author_stopped_source_changes'] and m['interface_sha256']=='046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
 assert sha(GO)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
 assert MOD.is_dir()
 RUN.mkdir();source={};replace={}
 for item in m['pins']:
  p=AUTHOR/'final-04/source'/item['path']
  assert sha(p)==item['sha256'] and sha(WT/item['path'])==item['sha256'],item['path']
  target=RUN/'frozen-source'/item['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
  source[item['path']]={'sha256':sha(target),'bytes':target.stat().st_size}
  replace[str(WT/item['path'])]=str(target)
 for name in PINS:
  target=RUN/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((AUTHOR/name).read_bytes())
 extras={}
 for virtual,local in EXTRAS.items():
  target=RUN/'independent-tests'/local;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((HERE/local).read_bytes())
  replace[str(WT/virtual)]=str(target);extras[virtual]={'sha256':sha(target),'path':str(target)}
 save('overlay.json',{'Replace':replace})
 save('inputs.json',{'source_sha256':{name:pin['sha256'] for name,pin in source.items()},'source':source,'extras':extras,'author_pins':PINS,'interface_sha256':m['interface_sha256'],'controller_sha256':sha(__file__),'go':str(GO),'go_sha256':sha(GO),'module_inputs':str(MOD),'base_head':m['base_head'],'go_mod_sha256':sha(WT/'go.mod'),'go_sum_sha256':sha(WT/'go.sum'),'source_mode':'EXACT18_C_OVERLAY_WITH_READONLY_NECESSARY_BASELINE_DEPENDENCIES','full_base_archive':'REJECTED_NOT_EXECUTED_NOT_RETRIED','formal_increment':0})
 print(json.dumps({'prepared':True,'source_count':18,'extra_files':len(EXTRAS),'inputs_sha256':sha(RUN/'inputs.json')}))

def check_frozen():
 inputs=json.loads((RUN/'inputs.json').read_bytes())
 for name,pin in inputs['source'].items():assert sha(RUN/'frozen-source'/name)==pin['sha256'],name
 for name,pin in inputs['extras'].items():assert sha(pin['path'])==pin['sha256'],name
 assert sha(WT/'go.mod')==inputs['go_mod_sha256'] and sha(WT/'go.sum')==inputs['go_sum_sha256']
 if (RUN/'fixture-correction.json').exists():
  correction=json.loads((RUN/'fixture-correction.json').read_bytes())
  for item in correction['changes']:assert sha(item['path'])==item['sha256']
  assert sha(RUN/'overlay-corrected.json')==correction['overlay_sha256']

def run(phase,args):
 check_frozen()
 for rel in ['private/tmp','private/profile','private/appdata','private/localappdata','private/gopath']:(RUN/rel).mkdir(parents=True,exist_ok=True)
 cache=HERE/'run-01/private/cache';assert cache.is_dir()
 env={key:os.environ[key] for key in ['SystemRoot','WINDIR','COMSPEC'] if key in os.environ}
 env.update({'PATH':str(GO.parent)+os.pathsep+str(Path(env['SystemRoot'])/'System32'),
  'USERPROFILE':str(RUN/'private/profile'),'APPDATA':str(RUN/'private/appdata'),'LOCALAPPDATA':str(RUN/'private/localappdata'),
  'TEMP':str(RUN/'private/tmp'),'TMP':str(RUN/'private/tmp'),'GOTMPDIR':str(RUN/'private/tmp'),'GOCACHE':str(cache),'GOPATH':str(RUN/'private/gopath'),'GOMODCACHE':str(MOD),
  'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','CGO_ENABLED':'0','GOTELEMETRY':'off','GOVCS':'*:off','GOFLAGS':'-mod=readonly'})
 cmd=[str(GO)]+args
 selected_overlay=Path(next(arg[len('-overlay='):] for arg in args if arg.startswith('-overlay=')))
 controller_copy=RUN/(phase+'.controller.py.txt'); assert not controller_copy.exists(); controller_copy.write_bytes(Path(__file__).read_bytes())
 save(phase+'.command.json',{'argv':cmd,'cwd':str(WT),'environment':env,'controller_sha256':sha(__file__),'overlay_sha256':sha(selected_overlay),'source_mode':'EXACT18_C_OVERLAY','execution_class':'FRESH_DB_RECORDER_OWNED_FAKE_GO_EXE_WINDOWS_JOB_NO_REAL_CODEX_MODEL_OLD_DB_GUI','formal_increment':0})
 save(phase+'.started.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 with (RUN/(phase+'.stdout.raw')).open('wb') as out,(RUN/(phase+'.stderr.raw')).open('wb') as err:
  child=subprocess.Popen(cmd,cwd=WT,env=env,stdout=out,stderr=err);code=child.wait()
 counts={'run':0,'pass':0,'fail':0,'skip':0,'top_pass':0,'sub_pass':0};roster=[]
 for line in (RUN/(phase+'.stdout.raw')).read_bytes().splitlines():
  try:item=json.loads(line)
  except (ValueError,UnicodeError):continue
  action=item.get('Action');name=item.get('Test')
  if name and action in counts:counts[action]+=1
  if name and action in ['pass','fail','skip']:
   roster.append({'package':item.get('Package'),'test':name,'action':action})
   if action=='pass':counts['sub_pass' if '/' in name else 'top_pass']+=1
 check_frozen()
 save(phase+'.result.json',{'exit_code':code,'counts':counts,'roster':roster,'stdout_sha256':sha(RUN/(phase+'.stdout.raw')),'stderr_sha256':sha(RUN/(phase+'.stderr.raw')),'formal_increment':0})
 print(json.dumps({'phase':phase,'exit_code':code,'counts':counts}));return code

if __name__=='__main__':
 command=sys.argv[1]
 common=['test','-json','-count=1','-vet=off','-timeout=150s','-p=1','-parallel=1','-overlay='+str(RUN/'overlay.json')]
 if command=='prepare':prepare()
 elif command=='focused':sys.exit(run('independent-focused',common+['-run','^(TestHarness|TestCodexHarness)','./internal/domain','./internal/api','./internal/host','./adapters/runtime']))
 elif command=='independent':sys.exit(run('independent-counterexamples',common+['-run','^TestIndependentHarness','./internal/domain','./internal/api','./adapters/runtime']))
 elif command=='corrected':sys.exit(run('independent-counterexamples-corrected',[('-overlay='+str(RUN/'overlay-corrected.json')) if arg.startswith('-overlay=') else arg for arg in common]+['-run','^TestIndependentHarness','./internal/domain','./internal/api','./adapters/runtime']))
 elif command=='atomic':sys.exit(run('independent-unknown-atomic',common+['-run','^TestIndependentHarnessUnknownTerminalAtomic$','./internal/domain']))
 elif command=='compat':sys.exit(run('independent-mu-parser-compat',common+['-run','^TestW05(Protocol|TransientReconnect)','./adapters/runtime']))
 elif command=='vet':sys.exit(run('independent-vet',['vet','-p=1','-overlay='+str(RUN/'overlay.json'),'./internal/domain','./internal/api','./internal/host','./adapters/runtime','./apps/control']))
 else:raise SystemExit('unknown phase')
