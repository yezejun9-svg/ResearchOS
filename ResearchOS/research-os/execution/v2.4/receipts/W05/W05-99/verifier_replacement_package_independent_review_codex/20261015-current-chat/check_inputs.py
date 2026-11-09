import pathlib,json,hashlib
E=pathlib.Path(__file__).resolve().parent
A=E.parents[1]/'verifier_replacement_package_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
before=read(A/'compiler-module-inputs.before.json');after=read(A/'compiler-module-inputs.after.json')
assert len(before)==len(after)==2294
assert [dict((k,v) for k,v in x.items() if k!='current_sha256') for x in after]==before
for b,a in zip(before,after):
 p=pathlib.Path(b['path']);raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert digest==b['sha256']==a['current_sha256'] and len(raw)==b['bytes'],str(p)
native=read(E/'02-native-package-probes.json');assert native['native_exit']==0
rows=[json.loads(x) for x in (E/'02-native-package-probes.stdout').read_text(encoding='utf-8').splitlines()]
passes=[r['Test'] for r in rows if r.get('Test') and r.get('Action')=='pass']
assert len(passes)==7 and not [r for r in rows if r.get('Action') in ['fail','skip']]
for label in ['03-packaged-control-early-reject','04-packaged-verifier-no-pipes']:
 r=read(E/(label+'.json'));assert r['native_exit']==2
assert read(E/'03-packaged-control-early-reject.stdout')['error_code']=='REPLACEMENT_ARGUMENTS'
tmp=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\tmp\vr-package-independent-20261015')
assert not list(tmp.iterdir()),'isolated temporary directory has unexpected retained files'
with (E/'05-input-and-result-check.json').open('x',encoding='utf-8') as f:json.dump({'compiler_module_inputs_checked':2294,'drift':[],'native_probe_pass':passes,'native_probe_fail':0,'native_probe_skip':0,'bounded_negative_process_expected_exit':2,'isolated_temp_empty':True,'formal_increment':0},f,ensure_ascii=False,indent=2)
print('2294 compiler/module inputs current hashes agree;7 probe passes;2 expected exit2; isolated temp empty')
