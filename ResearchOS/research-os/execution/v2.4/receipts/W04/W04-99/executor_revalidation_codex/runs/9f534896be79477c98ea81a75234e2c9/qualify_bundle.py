from pathlib import Path
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;HERE=OUT.parents[1];ROOT=HERE.parents[5]
MAIN=Path('D:/作品集/ResearchOS/research-os');OLD=HERE.with_name('executor_codex')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(name,data):
 with (OUT/name).open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
locked=json.loads((ROOT/'execution/toolchains/locked.json').read_text(encoding='utf-8'))
python=locked['tools']['python']['path']
assignment=MAIN/'execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/actor_assignment.json'
env=dict(os.environ,RESEARCHOS_W04_ACTOR_ASSIGNMENT=str(assignment),PYTHONDONTWRITEBYTECODE='1')
before=inventory(OLD);save('protected-old-tree-before.json',before)
sources=[HERE/n for n in ('collect.py','bridge.py','test_bridge.py','parent_driver.py','evidence_module.py','expected.json','frozen_inputs/commands-v24-r37.json','frozen_inputs/legacy_entries.json','test_collect.py')]
save('candidate-source-before.json',[ref(p) for p in sources])
def run(argv,stem):
 start=datetime.now(timezone.utc).isoformat();result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
 for name,value in [('stdout',result.stdout),('stderr',result.stderr)]:
  with (OUT/(stem+'.'+name)).open('xb') as f:f.write(value)
 save(stem+'.invocation.json',{'actualargv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'measurement_mode':'SYNTHETIC_NOT_PRODUCT','stdout_ref':ref(OUT/(stem+'.stdout')),'stderr_ref':ref(OUT/(stem+'.stderr'))})
 return result.returncode
codes={}
codes['prepare']=run([python,'-B','-X','utf8',str(HERE/'collect.py'),'--package-input',str(OLD/'frozen_inputs/package'),'--executor-id','codex:/root/sources_parent_impl','--verifier-id','codex:/root/w05_merge_review','--root-id','codex:/root','--actor-assignment',str(assignment),'--prepare-only'],'prepare')
codes['collector_controls']=run([python,'-B','-X','utf8',str(HERE/'test_collect.py'),'-v'],'collector-controls')
codes['bridge_controls']=run([python,'-B','-X','utf8',str(HERE/'test_bridge.py'),'-v'],'bridge-controls')
for name in ('python','go'):
 tool=locked['tools'][name];assert sha(Path(tool['path']))==tool['sha256']
 codes[name+'_version']=run([tool['path'],*tool['version_argv']],name+'-version')
 assert (OUT/(name+'-version.stdout')).read_text(encoding='utf-8').strip()==tool['version_output']
after=inventory(OLD);save('protected-old-tree-after.json',after);assert before==after
save('candidate-source-after.json',[ref(p) for p in sources])
assert json.loads((OUT/'candidate-source-before.json').read_text(encoding='utf-8'))==json.loads((OUT/'candidate-source-after.json').read_text(encoding='utf-8'))
source_manifest=[]
for p in sources:
 name=p.relative_to(HERE).as_posix();original=OLD/name
 source_manifest.append({'candidate':ref(p),'original':ref(original) if original.is_file() else None,'byte_identical':original.is_file() and p.read_bytes()==original.read_bytes()})
package_old=inventory(OLD/'frozen_inputs/package');package_new=inventory(HERE/'frozen_inputs/package');assert package_old==package_new and len(package_new)==148
save('source-manifest.json',{'sources':source_manifest,'package_files':package_new,'package_manifest_entries':147,'total_with_manifest':148,'old_tree_unchanged_file_count':len(before)})
prefix=(MAIN/'execution/v2.4/formal_case_index.py').read_bytes()[:51719]
assert hashlib.sha256(prefix).hexdigest()=='92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1'
save('qualification.json',{'status':'TOOLING_SOURCE_READY' if not any(codes.values()) else 'TOOLING_TEST_FAILURE','classification':'SYNTHETIC_NOT_PRODUCT','actual_exit_codes':codes,'candidate_source_manifest_ref':ref(OUT/'source-manifest.json'),'actor_assignment_ref':ref(assignment),'formal_prefix_unchanged':True,'protected_old_tree_unchanged':True,'current_collection_executed':False,'product_assertions_executed':0,'formal_acceptance_delta':0,'shared_registry_changed':False})
print(json.dumps({'qualification_ref':ref(OUT/'qualification.json'),'codes':codes},ensure_ascii=False))
sys.exit(1 if any(codes.values()) else 0)
