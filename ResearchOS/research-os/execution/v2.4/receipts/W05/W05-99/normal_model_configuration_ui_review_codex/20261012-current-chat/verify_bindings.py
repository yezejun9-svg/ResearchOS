import pathlib,json,hashlib,subprocess
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-20261012'
SOURCE=ROOT/'execution/v2.4/receipts/W05/W05-99/normal_model_configuration_ui_codex/20261012-current-chat'
checks=[]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
ck('frozen_SHA256SUMS',sha(SOURCE/'SHA256SUMS.txt')=='1de570facb8c2fba2fcdd38c545596774b4754334beefb7b1bd15e3e78a3de43')
for line in (SOURCE/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
 h,n=line.split('  ',1);ck('receipt:'+n,sha(SOURCE/n)==h)
ck('candidate_HEAD',subprocess.check_output(['git','-C',str(WT),'rev-parse','HEAD'],text=True).strip()=='c12847d7ee7b37a15d875929738fe84fd7ba6964')
descriptor=load(SOURCE/'validator-descriptor.json')
tree=WT/'.local/w05-validator-final'
for key in ['compile_invocation_ref','full_input_manifest_ref','compiler_generated_importcfg_archives_ref']:
 r=descriptor[key];ck(key,sha(r['path'])==r['sha256'] and pathlib.Path(r['path']).stat().st_size==r['bytes'])
inputs=load(descriptor['full_input_manifest_ref']['path'])
ck('build_input_digest',hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()==descriptor['build_input_digest'])
for i in inputs:ck('input:'+i['path'],pathlib.Path(i['path']).is_file() and sha(i['path'])==i['sha256'])
archives=load(descriptor['compiler_generated_importcfg_archives_ref']['path'])
for typ,rows in archives.items():
 for i in rows:ck('compiler_'+typ+':'+i['path'],pathlib.Path(i['path']).is_file() and sha(i['path'])==i['sha256'])
for i in descriptor['exact_module_source_inventory']:
 ck('desktop_resource:'+i['path'],sha(tree/'apps/desktop'/i['path'])==i['sha256']==sha(WT/'apps/desktop'/i['path']))
for i in descriptor['compiled_React_asset_inventory']:ck('React_asset:'+i['path'],sha(tree/'apps/web/dist'/i['path'])==i['sha256'])
ck('validator_binary',sha(tree/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')==descriptor['binary_sha256'])
for i in descriptor['tools']:ck('tool:'+i['name'],sha(i['path'])==i['sha256'])
report={'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'model_calls':0}
(OUT/'bindings.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'passed':report['passed'],'failed':[c['check'] for c in checks if not c['passed']]}))
