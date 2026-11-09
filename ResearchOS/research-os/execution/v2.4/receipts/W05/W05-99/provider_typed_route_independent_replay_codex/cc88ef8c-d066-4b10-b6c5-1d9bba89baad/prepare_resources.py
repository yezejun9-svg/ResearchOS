import pathlib,json,hashlib,subprocess,os
M=pathlib.Path('D:/作品集/ResearchOS/research-os');H=pathlib.Path(__file__).resolve().parent;OLD=H.parent/'632e634c-2f7f-47c3-b63a-b7073a9e1ccb';A=M/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-closure-and-test-tls-r291/compiler_resource_amendment.json';AUTHOR=M/'.local/worktrees/codex-w0599-provider-binding'
def ref(p):p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,o):
 with (H/n).open('x',encoding='utf-8') as f:json.dump(o,f,indent=2,ensure_ascii=False);f.write('\n')
assert ref(A)['sha256']=='9ffb57f86c59fc8aa725971516e1daf0cc2a13c7b9e84a2317c3f73154d275cf';a=json.loads(A.read_text(encoding='utf-8'));env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1';export=json.loads((OLD/'export.json').read_text(encoding='utf-8'));new=[]
for item in a['exact_public_compile_exports']:
 args=['git','-C',str(AUTHOR),'cat-file','blob',item['git_blob']];raw=subprocess.check_output(args,env=env);assert hashlib.sha256(raw).hexdigest()==item['sha256'];dst=M/item['destination'];dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(raw)
 r={'relative':item['path'],'git_blob':item['git_blob'],**ref(dst)};export['files'].append(r);new.append({'invocation':args,'exit':0,'destination':r})
write('export.json',export);write('resource-export.json',{'amendment':ref(A),'exports':new,'executed_functions':0});(H/'inputs').mkdir();inputs=json.loads((OLD/'original7.before.json').read_text(encoding='utf-8'))
for e in inputs:
 src=pathlib.Path(e['original']['path']);assert ref(src)==e['original'];dst=H/'inputs'/(e['id']+'.sqlite');dst.write_bytes(src.read_bytes());e['copy']=ref(dst)
write('original7.before.json',inputs);(H/'synthetic_workspace_evidence.txt').write_bytes((OLD/'synthetic_workspace_evidence.txt').read_bytes());write('amendment-ref.json',ref(A))
p=OLD/'independent_provider_public_boundary_windows_test.go';assert ref(p)['sha256']=='c300fb61dd2855bea5ba2f9bce329dcabc53662d4bb30169a59846d187105676';(H/p.name).write_bytes(p.read_bytes())
driver=(OLD/'driver.py').read_text(encoding='utf-8').replace('cache-r290','cache-r291');(H/'driver.py').write_text(driver,encoding='utf-8',newline='\n');write('prepare-progress.json',{'exports':10,'overlay_byte_equal':ref(H/p.name),'controls':0,'old3preparation_failures_retained':True})
print(json.dumps({'new':str(H),'exports':10}))
