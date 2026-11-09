"""Public-only path predicate reproduction; never loads signing code or a key."""
import hashlib,json,subprocess
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/schema24-to25-native-20261014'
C=R/'execution/v2.4/receipts/W17/W17-03/native25_test_compilation_codex/20261014-current-chat'
def ref(p):
 b=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (E/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
s=(W/'internal/recoveryauthority/native_windows.go').read_text()
start=s.index('func plainPath(path string) error {');end=s.index('\n}',start)+2
function=s[start:end]
assert 'a!=filepath.Clean(path)' in function and '!strings.EqualFold(real,path)' in function
source='''package main
import("encoding/json";"errors";"os";"path/filepath";"strings")
'''+function+'''
func main(){
 p:=os.Args[1]
 native:=filepath.Clean(p)
 forward:=strings.ReplaceAll(native,`\\`,"/")
 out:=[]map[string]any{}
 for _,v:=range []struct{name,path string}{{"backslash",native},{"forward_slash",forward},{"cleaned_forward_slash",filepath.Clean(forward)}}{
  real,evalerr:=filepath.EvalSymlinks(v.path)
  verdict:=plainPath(v.path)
  record:=map[string]any{"case":v.name,"path":v.path,"clean":filepath.Clean(v.path),"eval_symlinks":real,"accepted":verdict==nil,"file_contents_read":false}
  if evalerr!=nil {record["eval_error"]=evalerr.Error()}
  if verdict!=nil {record["error"]=verdict.Error()}
  out=append(out,record)
 }
 json.NewEncoder(os.Stdout).Encode(out)
}
'''
(E/'plainpath_probe.go').write_text(source,encoding='utf8')
(E/'public-path.txt').write_text('PUBLIC NONSECRET PATH FIXTURE ONLY\n',encoding='utf8')
temp=E/'go-temp';temp.mkdir(exist_ok=False)
inv=json.loads((C/'test-binary-compile.invocation.json').read_bytes());env=inv['public_environment']
for k in ['TEMP','TMP','GOTMPDIR']:env[k]=str(temp)
args=[inv['argv'][0],'run',str(E/'plainpath_probe.go'),str(E/'public-path.txt')]
p=subprocess.run(args,cwd=W,env=env,capture_output=True,timeout=60)
(E/'path-probe.stdout.raw.json').write_bytes(p.stdout);(E/'path-probe.stderr.raw.txt').write_bytes(p.stderr)
save('path-probe.invocation.json',{'argv':args,'cwd':str(W),'public_environment':env,'actual_native_exit':p.returncode,'source_ref':ref(W/'internal/recoveryauthority/native_windows.go'),'extracted_function_sha256':hashlib.sha256(function.encode()).hexdigest(),'probe_source_ref':ref(E/'plainpath_probe.go'),'private_resource_access':False,'contents_read_by_predicate':False,'signing_code_linked':False})
assert p.returncode==0
out=json.loads(p.stdout);assert out[0]['accepted'] and out[2]['accepted'] and out[1]['error']=='AUTHORITY_REPARSE_PATH'
assert not list(temp.iterdir());temp.rmdir()
save('path-diagnosis.json',{'state':'PUBLIC_PATH_FORMAT_REJECTION_REPRODUCED','exact_production_function_copied':True,'cases':out,'scope':'Only existing public test-file path metadata. No key contents, DPAPI, signer, grant or actual case operation.','inference':'If Root supplied the reported forward-slash absolute resource path, this exact plainPath predicate deterministically rejects before hold opens the resource or readPurposeKey reads bytes. The discarded signer stderr cannot independently prove this was the only cause of the recorded exit 1.','formal_increment':0})
print(json.dumps({'state':'PUBLIC_PATH_FORMAT_REJECTION_REPRODUCED','cases':[{'case':v['case'],'accepted':v['accepted'],'error':v.get('error')} for v in out]}))
