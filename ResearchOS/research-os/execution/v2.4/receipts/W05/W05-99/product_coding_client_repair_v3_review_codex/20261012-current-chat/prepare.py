from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parent; ROOT=O.parents[6]
A=O.parents[1]/'product_coding_client_repair_v3_codex/20261012-current-chat'
C=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v3-20261012')
B=C/'.local/builds/product-coding-client-repair-v3-20261012';APP=B/'apps/desktop'
OLD=O.parents[1]/'product_coding_client_repair_v2_review_codex/20261012-current-chat'
BASE='b20c816ec346c1dad1534b18b02abbb4f47c4628';CANDIDATE='2fda8155d457784c22655be553af87b8f3b114f2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
checks=[]
def check(kind,p,expected,size=None):
 actual=sha(p) if p.is_file() else None
 checks.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
check('author-manifest',A/'manifest.json','7cab3b1e93d114b8a3a9e8fbcc61d8a26d9581e1a318ea081a24dec2637340ff')
m=read(A/'manifest.json');binding=read(A/'c-build-binding.json');bundle=read(A/'source-bundle.json')
for name,key in [('source-bundle.json','source_bundle_sha256'),('c-build-binding.json','c_build_binding_sha256'),('README.md','readme_sha256'),('review-handoff.md','review_handoff_sha256')]:check(name,A/name,m[key])
rows=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted((A/'raw').rglob('*')) if p.is_file()]
assert len(rows)==m['raw_files'] and sum(x['bytes'] for x in rows)==m['raw_bytes']
raw_rows=[[p.relative_to(A/'raw').as_posix(),p.stat().st_size,sha(p)] for p in sorted((p for p in (A/'raw').rglob('*') if p.is_file()),key=lambda p:p.relative_to(A/'raw').as_posix())]
raw_census_calculated=hashlib.sha256(json.dumps(raw_rows,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
assert raw_census_calculated==m['raw_census_sha256']
raw_census_pending=dict(expected=m['raw_census_sha256'],actual=raw_census_calculated,status='VERIFIED_WITH_AUTHOR_FORMULA')
for row in rows:check('author-raw',A/row['path'],row['sha256'],row['bytes'])
check('old-b20-report',OLD/'independent-review.json','730de4165869889202133f4419f0a738c2e317265d65acd9f13c3856382904c6')
check('old-b20-manifest',OLD/'receipt_manifest.json','39930f2639c332a336f55bde33ccdcc3fba481e025a992769f0d75b1a0d0127b')
for row in read(OLD/'receipt_manifest.json')['files']:check('old-b20-member',OLD/row['path'],row['sha256'],row['bytes'])
scope=O.parents[1]/'product_coding_client_repair_v3_scope_assessment_codex/20261012-current-chat/scope-repair-assessment.json'
check('scope-assessment',scope,'24c62cbac9e9ba0f412a029454c7875e349c19c9469628da53c95b5f144a0b8b')
check('registered-scope',O.parents[1]/'resume_cp398_codex/20261012-current-chat/continuation-cp431/coding-client-v3-scope.json',bundle['scope_sha256'])
check('formula-locator',A/'formula-locator.json','f2760ad8a6c7d6ab14a7371930c366cc3150ff7b0e36927c00df781fb0b09765')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()==CANDIDATE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C).strip()
changed=subprocess.check_output(['git','diff','--name-only',BASE,CANDIDATE],cwd=C,text=True).splitlines()
assert len(changed)==4 and set(changed)<=set(read(scope)['allowed_paths'])
for row in bundle['source_files']:
 raw=subprocess.check_output(['git','show',CANDIDATE+':'+row['path']],cwd=C)
 assert hashlib.sha256(raw).hexdigest()==row['sha256']
 check('registered-source',C/row['path'],row['sha256'],row['bytes'])
 p=O/'source'/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 if (B/row['path']).is_file():check('bound-source',B/row['path'],row['sha256'],row['bytes'])
descriptor=APP/'resources/client-wire/descriptor.json';d=read(descriptor)
check('descriptor',descriptor,binding['descriptor_sha256'])
check('validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',d['binary_sha256'],d['binary_bytes'])
for row in d['exact_module_source_inventory']:check('bound-module',APP/row['path'],row['sha256'])
for row in d['compiled_React_asset_inventory']:check('compiled-react',B/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in d['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
ref=d['full_input_manifest_ref'];inputs=Path(ref['path']);check('full-input-manifest',inputs,ref['sha256'],ref['bytes'])
for row in read(inputs):check('build-input',Path(row['path']),row['sha256'],row['bytes'])
assert len(read(inputs))==6439 and d['build_input_digest']==m['build_input_digest']
check('build-result',Path(binding['build_logs'])/'result.json',binding['build_result_sha256'])
for test in binding['tests']+[binding['diagnostic_only']]:
 p=A/'raw'/(test['name']+'.invocation.json');check('author-invocation',p,test['invocation_sha256']);inv=read(p)
 for suffix in ['stdout','stderr']:check('author-test-output',A/'raw'/(test['name']+'.'+suffix),inv[suffix+'_sha256'])
 assert inv['exit']==test['exit']
(O/'bound-descriptor.json').write_bytes(descriptor.read_bytes());(O/'candidate.diff').write_bytes(subprocess.check_output(['git','diff',BASE,CANDIDATE],cwd=C))
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(x['passed'] for x in checks),failures=[x for x in checks if not x['passed']],raw_census_pending=raw_census_pending,author_files=len(rows),author_raw_bytes=m['raw_bytes'],full_build_inputs=6439,registered_paths=8,changed_paths=4,build_input_digest=d['build_input_digest'],all_checks=checks)
(O/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'}));assert not result['failures']
s=(OLD/'fixture.mjs').read_text(encoding='utf-8').replace('coding-client-v2-20261012','coding-client-v3-20261012').replace('product-coding-client-repair-v2-20261012','product-coding-client-repair-v3-20261012')
s=s.replace('let selected=context,seq=0,prepared=null,committed=false,hold=false;','let selected=context,seq=0,prepared=null,committed=false,hold=false,generation=0;')
s=s.replace('observeProcess:identity','observeProcess:identity,codingResourceGeneration:()=>generation')
s=s.replace('setContext:value=>','setGeneration:value=>{generation=value;},setContext:value=>')
s=s.replace("frozen_checks:[{id:'value-check',package:'./calc',test_pattern:'^TestValue$',source_count:3,source_bytes:123,source_manifest_hash:hash,toolchain_hash:hash,build_hash:hash,vendor_hash:''}]", "frozen_checks:frame.coding.checks.map(c=>({id:c.id,package:c.package,test_pattern:c.test_pattern,source_count:3,source_bytes:123,source_manifest_hash:hash,toolchain_hash:hash,build_hash:hash,vendor_hash:''}))")
if (O/'fixture.mjs').exists():assert (O/'fixture.mjs').read_text(encoding='utf-8')==s
(O/'fixture.mjs').write_text(s,encoding='utf-8')

