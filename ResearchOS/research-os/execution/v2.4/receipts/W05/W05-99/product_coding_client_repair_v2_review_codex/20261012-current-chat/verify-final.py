from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'product_coding_client_repair_v2_codex/20261012-current-chat'
DWT=ROOT/'.local/worktrees/w05-product-coding-client-repair-v2-20261012'
CWT=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v2-20261012')
BUILD=CWT/'.local/builds/product-coding-client-repair-v2-20261012';APP=BUILD/'apps/desktop'
CANDIDATE='b20c816ec346c1dad1534b18b02abbb4f47c4628'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
checks=[]
def check(kind,p,expected,size=None):
 actual=sha(p) if p.is_file() else None
 checks.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
check('manifest',AUTHOR/'manifest.json','44379f527ddaf8935888c64470489c36820470e7ab8a6e3d5047b9dcb41c694a')
m=read(AUTHOR/'manifest.json')
for name,key in [('source-bundle.json','source_bundle_sha256'),('c-build-binding.json','c_build_binding_sha256'),('README.md','readme_sha256')]:check(name,AUTHOR/name,m[key])
census={'entries':[{'path':p.relative_to(AUTHOR).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((AUTHOR/'raw').rglob('*')) if p.is_file() and not p.relative_to(AUTHOR/'raw').as_posix().startswith('c-bound-all-desktop')]}
assert len(census['entries'])==63
assert hashlib.sha256(''.join(f"{r['path']}\t{r['sha256']}\t{r['bytes']}\n" for r in census['entries']).encode()).hexdigest()==m['raw_census_sha256']
for row in census['entries']:check('author-raw',AUTHOR/row['path'],row['sha256'],row['bytes'])
b=read(AUTHOR/'source-bundle.json')
for wt in [DWT,CWT]:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip()==CANDIDATE
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=wt).strip()
 for row in b['source_files']:
  check('registered-source',wt/row['path'],row['sha256'],row['bytes'])
  raw=subprocess.check_output(['git','show',CANDIDATE+':'+row['path']],cwd=wt)
  assert hashlib.sha256(raw).hexdigest()==row['sha256']
descriptor=APP/'resources/client-wire/descriptor.json';d=read(descriptor)
check('descriptor',descriptor,m['binary_sha256'] if False else read(AUTHOR/'c-build-binding.json')['descriptor_sha256'])
check('validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',d['binary_sha256'],d['binary_bytes'])
for row in d['exact_module_source_inventory']:check('bound-module',APP/row['path'],row['sha256'])
for row in d['compiled_React_asset_inventory']:check('compiled-react',BUILD/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in d['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
ref=d['full_input_manifest_ref'];inputs=Path(ref['path']);check('full-input-manifest',inputs,ref['sha256'],ref['bytes'])
for row in read(inputs):check('build-input',Path(row['path']),row['sha256'],row['bytes'])
assert len(read(inputs))==6439 and d['build_input_digest']==m['build_input_digest']
check('build-result',CWT/'.local/builds/product-coding-client-repair-v2-20261012-logs/result.json',read(AUTHOR/'c-build-binding.json')['build_result_sha256'])
(OUT/'bound-descriptor.json').write_bytes(descriptor.read_bytes())
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(x['passed'] for x in checks),failures=[x for x in checks if not x['passed']],author_files=len(census['entries']),full_build_inputs=6439,registered_paths=8,build_input_digest=d['build_input_digest'],all_checks=checks)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'}));assert not result['failures']

