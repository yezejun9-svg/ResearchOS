from pathlib import Path
import hashlib,json,os,re,subprocess,sys
R=Path(__file__).resolve().parent
A=R.parents[1]/'product-v1-public-health-author'
WT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-public-health-20261104')
NODE=Path('C:/nvm4w/nodejs/node.exe');TREE=R/'source'
PINS={'final/source-manifest.json':'7acb771adfea2bb466afbdac0f6a2808cfac5a6b1d327bee69c17a9581ba74f0','final/FROZEN.json':'ae9bb895eb7a51f6949d6e66bd856fdceee26e840b5bf1d4d87861df959c4dcc','final/summary.json':'2fe72c5b1fc2fbcd7bb15afd5df2489806c296502339592ab01d259b0f44ca20','final/diagnostics.json':'c8e9b0f5b06fda68b32abef7a26fd315c65d5badf375d704b7a397c1767394ab','EVIDENCE_MANIFEST.json':'93a5e83db70c0e711d861505fc00636353a3b5b35b4617724dcef5ec19b61b8e'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
 p=R/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def prepare():
 for name,pin in PINS.items():assert sha(A/name)==pin,name
 m=json.loads((A/'final/source-manifest.json').read_bytes());assert len(m['source_sha256'])==2 and m['construction_frozen'] and not m['source_modification_permitted']
 assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
 for rel,pin in m['source_sha256'].items():assert sha(A/'final/source'/rel)==pin and sha(WT/rel)==pin,rel
 ev=json.loads((A/'EVIDENCE_MANIFEST.json').read_bytes())
 for row in ev['files']:assert sha(A/row['path'])==row['sha256'],row['path']
 im=json.loads((A/'checks-02-c-overlay/input-manifest.json').read_bytes());assert len(im['files'])==43
 files={}
 for row in im['files']:
  rel=row['path'];p=A/'checks-02-c-overlay/source'/rel;assert sha(p)==row['sha256'],rel
  q=TREE/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());files[rel]={'sha256':sha(q),'bytes':q.stat().st_size,'origin':row['origin']}
 for rel,pin in m['source_sha256'].items():assert sha(TREE/rel)==pin,rel
 for name in PINS:
  target=R/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/name).read_bytes())
 for name in ['checks-01/pure-tests.stdout.raw','checks-01/pure-tests.stderr.raw','checks-01/results.json','checks-02-c-overlay/input-manifest.json']:
  target=R/'author'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((A/name).read_bytes())
 old=(R.parents[1]/'product-v1-assistant-home-independent-qa-20261104/run-01/source/apps/desktop/main/lib/ipc.js').read_text(encoding='utf-8')
 new=(TREE/'apps/desktop/main/lib/ipc.js').read_text(encoding='utf-8')
 a=new.index('  let req;\n',new.index('async function callCore('));b=new.index('  const reply = await deps.transport',a)
 oa=old.index('  const principal = host.principalFor',old.index('async function callCore('));ob=old.index('  const reply = await deps.transport',oa)
 assert new[:a]+old[oa:ob]+new[b:]==old,'Unexpected delta beyond public health request selection'
 save('inputs.json',{'source_sha256':m['source_sha256'],'source_manifest_sha256':PINS['final/source-manifest.json'],'freeze_sha256':PINS['final/FROZEN.json'],'metadata_pins':PINS,'base_head':m['base_head'],'files':files,'author_evidence_files':len(ev['files']),'node_sha256':sha(NODE),'only_production_delta_public_health_request_selection':True,'formal_increment':0})
 print(json.dumps({'prepared':True,'exact2':True,'public_dependency_files':43,'source_delta_limited':True}))
def check():
 i=json.loads((R/'inputs.json').read_bytes())
 for rel,v in i['files'].items():assert sha(TREE/rel)==v['sha256'],rel
 return i
def run(name,args):
 check();assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
 env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(NODE.parent)
 save(name+'.command.json',{'argv':[str(NODE)]+args,'cwd':str(TREE),'environment':env,'controller_sha256':sha(Path(__file__)),'node_sha256':sha(NODE),'classification':'PURE_ACTUAL_IPC_ENSURECORE_MEMORY_FS_HTTP_ONLY_NO_REAL_SOCKET_GUI_NATIVE_MODEL_DB_AUTH'})
 with (R/(name+'.stdout.raw')).open('xb') as out,(R/(name+'.stderr.raw')).open('xb') as err:code=subprocess.run([str(NODE)]+args,cwd=TREE,env=env,stdout=out,stderr=err,timeout=60).returncode
 text=(R/(name+'.stdout.raw')).read_text(encoding='utf-8');counts={k:int(m.group(1)) for k in ['tests','pass','fail','skipped'] if(m:=re.search(r'^# '+k+r' (\d+)$',text,re.M))}
 check();save(name+'.result.json',{'exit_code':code,'tap_summary':counts,'stdout_sha256':sha(R/(name+'.stdout.raw')),'stderr_sha256':sha(R/(name+'.stderr.raw')),'formal_increment':0});print(json.dumps({'phase':name,'exit_code':code,'counts':counts}));return code
def readback():
 i=check()
 for rel,pin in i['source_sha256'].items():assert sha(WT/rel)==pin and sha(A/'final/source'/rel)==pin,rel
 save('no-drift.json',{'source_sha256':i['source_sha256'],'C_author_and_live_exact2_match':True,'C_dependency_inputs_unchanged':True,'formal_increment':0});print(json.dumps({'no_drift':True,'sha256':sha(R/'no-drift.json')}))
if __name__=='__main__':
 p=sys.argv[1]
 if p=='prepare':prepare()
 elif p=='required':sys.exit(run('required-tests',['--test','--test-reporter=tap','tests/ui/desktop/public-health-bridge.test.mjs','tests/ui/desktop/assistant-startup.test.mjs','tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs']))
 elif p=='independent':sys.exit(run('independent-tests',['--test','--test-reporter=tap',str(R/'independent.test.mjs')]))
 elif p=='syntax':sys.exit(run('ipc-syntax',['--check',str(TREE/'apps/desktop/main/lib/ipc.js')]))
 elif p=='readback':readback()
