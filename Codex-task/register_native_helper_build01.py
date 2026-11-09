import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');D=HERE/'product-v1-native-helper-build01';CONTROL=HERE/'product-v1-owned-verification-20261104';ID='product-v1-native-helper-build-01';OUT=HERE/'product-v1-native-helper-build01-registration'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists() and not (CONTROL/'runs'/ID).exists();assert sha(D/'MANIFEST.json')=='f232b86b8871df92a7fdfe621e6934324603d280daa744249e4756318e54b7bd';assert sha(D/'scope.template.json')=='8e1ee357a61d82b36e0e640a717a4c774bfe9cfa4e08be44a3c3722c11004718'
s=read(D/'scope.template.json');assert s['authorization']=='TEMPLATE_NOT_AUTHORIZATION' and s['purpose']=='build' and s['controller_sha256']=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert s['argv']==['build','-trimpath','-buildvcs=false','-o',str(D/'buildout/qualification-helper.exe'),'./cmd/researchos-qualification-helper'];assert Path(s['cwd'])==D/'source' and not (D/'buildout/qualification-helper.exe').exists()
for row in s['inputs']:assert sha(Path(row['path']))==row['sha256']
for ref in ['internal/qualificationprobe/plan.go','cmd/researchos-qualification-helper/main_windows.go','go.mod','go.sum']:assert sha(D/'source'/ref)==sha(ROOT/ref),ref
assert s['timeout_seconds']==600 and s['process_limit']==48 and s['memory_mib']==6144 and s['max_raw_bytes']==8388608
for key in ('GOENV','GOPROXY','GOSUMDB','GOWORK'):assert s['env'][key]=='off'
assert s['env']['GOTOOLCHAIN']=='local' and s['env']['CGO_ENABLED']=='0'
s.update(scope_id=ID,authorization='ROOT_REVIEWED_EXACT_COMMAND');s['inputs'] += [dict(path=str(p),sha256=sha(p)) for p in [D/'MANIFEST.json',D/'scope.template.json',Path(__file__)]]
OUT.mkdir();sp=CONTROL/'scopes'/(ID+'.json');assert not sp.exists();sp.write_bytes((json.dumps(s,indent=2)+'\n').encode('utf8'));reg=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_sha256=sha(sp),scope_path=str(sp),selected_source='HELPER_ONLY_TWO_PRODUCTION_FILES_AND_MODULE_INPUTS_MATCH_CURRENT_MAIN_AND_REVIEWED_B3',source_head_at_registration=read(ROOT/'execution/v2.4/checkpoint.json')['current_Main_HEAD'],helper_execution=False,native_calls=0,model_tasks=0,formal_increment=0,product_increment=0);(OUT/'REGISTRATION.json').write_bytes((json.dumps(reg,indent=2)+'\n').encode('utf8'));print(json.dumps(reg))
