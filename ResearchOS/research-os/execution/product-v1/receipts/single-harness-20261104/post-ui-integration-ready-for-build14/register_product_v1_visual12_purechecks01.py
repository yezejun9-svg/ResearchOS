import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';PREP=HERE/'product-v1-native-layout-visual-prepare-12';ID='product-v1-visual12-purechecks-01'
NODE=Path('C:/nvm4w/nodejs/node.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert sha(PREP/'MANIFEST.json')=='6a7c36a9ed8bc690c1bf4c7215fc45a781dbbc71037fd5a93c1f7f85f0080000'
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
review=HERE/'product-v1-native-layout-visual12-independent-review-20261105/review-report.json';assert sha(review)=='facfdfa3505561fd3b1de8e8402979f64e210a94d3b97541279f087ab139895f'
m=json.loads((PREP/'MANIFEST.json').read_bytes());files=[]
for item in m['files']:
 p=PREP/item['path'];assert sha(p)==item['sha256'];files.append(p)
files +=[PREP/'MANIFEST.json',review,Path(__file__)];tests=['revision12-purechecks.mjs','interaction-purechecks.mjs','main-scroll-purechecks.mjs','ancestor-clip-purechecks.mjs']
assert not (CONTROL/'runs'/ID).exists();scope=dict(schema='researchos.owned-windows-run/1',scope_id=ID,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(NODE),executable_sha256=sha(NODE),argv=['--test',*tests],cwd=str(PREP),timeout_seconds=60,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=16,memory_mib=1024,max_raw_bytes=2*1024*1024,env={},inputs=[dict(path=str(p),sha256=sha(p)) for p in files]);sp=CONTROL/'scopes'/(ID+'.json');put(sp,scope)
out=HERE/(ID+'-registration');assert not out.exists();out.mkdir();r=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),purpose='PURE_SOURCE_EXTRACTED_GEOMETRY_NEGATIVE_CHECKS_ONLY',app_browser_core_native_model_started=False,geometry_actually_verified=False,formal_increment=0,product_increment=0);put(out/'REGISTRATION.json',r);print(json.dumps(r))
