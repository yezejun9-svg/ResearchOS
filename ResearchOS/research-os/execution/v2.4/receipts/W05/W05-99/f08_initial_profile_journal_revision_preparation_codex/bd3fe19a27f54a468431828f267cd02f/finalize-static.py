from pathlib import Path
import ast,json,hashlib,difflib,re
O=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
B=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_queue_absence_revision_preparation_codex/b9a560ed59c24bef9b9e01d2d91c4b84'
def ref(p):
    raw=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,value):
    raw=value.encode('utf-8') if isinstance(value,str) else value
    with (O/name).open('xb') as f:f.write(raw)
    return ref(O/name)
def js(name,value):return put(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def doc(p):return json.loads(p.read_text(encoding='utf-8'))
old=(O/'client_cancel_finalization.go.proposed.txt').read_bytes().decode('utf-8')
assert ref(O/'client_cancel_finalization.go.proposed.txt')['sha256']=='7b6137cdda6a8aa5d74cebe2346a354f5b25620f17edf8588cd62af65b0974c2'
guard=(O/'endpoint-purity-guard.go.proposed.txt').read_text(encoding='utf-8')
nl='\r\n' if '\r\n' in old else '\n';guard=guard.replace('\n',nl)
needle='func f08FrozenModelProfile('
assert old.count(needle)==1
source=old.replace(needle,guard+nl+needle,1)
needle='endpoint,e:=f08String(c["endpoint"]);if e!=nil{return e};u,e:=url.Parse(endpoint)'
after='endpoint,e:=f08String(c["endpoint"]);if e!=nil{return e};if e=f08PureEndpointPrecondition(endpoint);e!=nil{return e};u,e:=url.Parse(endpoint)'
assert source.count(needle)==1;source=source.replace(needle,after,1)
assert source.replace(after,needle,1).replace(guard+nl,'',1)==old
sr=put('client_cancel_finalization.v2.go.proposed.txt',source)
base=(B/'client_cancel_finalization.go.proposed.txt').read_bytes().decode('utf-8')
put('client_cancel_finalization.v2.go.proposed.patch',''.join(difflib.unified_diff(base.splitlines(True),source.splitlines(True),fromfile='b9/internal/domain/client_cancel_finalization.go',tofile='proposed/internal/domain/client_cancel_finalization.go')))
prior_tests=(O/'client_cancel_finalization_test.go.proposed.txt').read_bytes().decode('utf-8')
addition='''
func TestF08EndpointEnvironmentBranchesRemainOpen(t *testing.T){
 for _,endpoint:=range []string{"https://fixture.invalid/v1/chat/completions","https://fixture.invalid:443/v1/chat/completions","https://a:80,b:81/path","https://[::1]/path"}{t.Run(endpoint,func(t *testing.T){
  p:=f08PureProfileFixture();c:=p["model_config"].(map[string]any);c["endpoint"]=endpoint;p["model_qualification"].(map[string]any)["model_config_hash"]=Hash(c)
  e:=f08FrozenModelProfile(p);open:=strings.Contains(endpoint,"a:80")||strings.Contains(endpoint,"[::1]");if open&&e!=f08ProfileEndpointGlobalGap{t.Fatal("environment-dependent URL branch not refused",e)};if !open&&e!=nil{t.Fatal("ordinary pure host rejected",e)}
 })}
}
'''.replace('\n',nl)
tr=put('client_cancel_finalization_test.v2.go.proposed.txt',prior_tests+addition)
base_tests=(B/'client_cancel_finalization_test.go.proposed.txt').read_bytes().decode('utf-8')
put('client_cancel_finalization_test.v2.go.proposed.patch',''.join(difflib.unified_diff(base_tests.splitlines(True),(prior_tests+addition).splitlines(True),fromfile='b9/internal/domain/client_cancel_finalization_test.go',tofile='proposed/internal/domain/client_cancel_finalization_test.go')))
urlpath=ROOT/'.local/tools/go1.27.1/go/src/net/url/url.go'
ur=ref(urlpath);put('additional-source-snapshots/04-url.go',urlpath.read_bytes());assert ref(urlpath)==ur
rows=doc(O/'inputs.before.json')['files']+[ur]
for r in rows:assert ref(Path(r['path']))==r
js('public-inputs.final.json',{'schema':'researchos.public-inputs.v1','files':rows,'prior160_rehashed':True,'url_added_after_explicit_inventory':True,'drift_count':0,'historical_first_read_claim':False})
# Text lexical balance only. This is not Go parsing, type checking or testing.
def balance(text):
    i=0;stack=[];state='code';pairs={')':'(',']':'[','}':'{'}
    while i<len(text):
        c=text[i];n=text[i:i+2]
        if state=='line':
            if c=='\n':state='code'
        elif state=='block':
            if n=='*/':state='code';i+=1
        elif state in ('"',"'"):
            if c=='\\':i+=1
            elif c==state:state='code'
        elif state=='`':
            if c=='`':state='code'
        elif n=='//':state='line';i+=1
        elif n=='/*':state='block';i+=1
        elif c in ('"',"'",'`'):state=c
        elif c in '([{':stack.append(c)
        elif c in ')]}':assert stack and stack.pop()==pairs[c],('delimiter',i)
        i+=1
    assert not stack and state in ('code','line'),(stack,state)
balance(source);balance(prior_tests+addition)
ast.parse(Path(__file__).read_text(encoding='utf-8'))
js('final-static-audit.json',{'schema':'researchos.f08-final-static-audit.v1','source_ref':sr,'test_ref':tr,'base_ref':ref(B/'client_cancel_finalization.go.proposed.txt'),'development_ref':ref(O/'client_cancel_finalization.go.proposed.txt'),'v2_inverse_exact_development':True,'development_inverse_exact_b9':doc(O/'static-source-audit.json')['source_inverse_exact_b9'],'lexical_delimiters_balanced':True,'go_parser_used':False,'go_compiled':False,'tests_executed':0,'SQL24_adoption_allowed':False,'url_source_ref':ur,'public_input_count':len(rows),'input_drift_count':0,'new_source_functions':['f08WindowsLocalOutput','f08PureEndpointPrecondition','f08FrozenModelProfile','f08FrozenDispatchProfile','f08FrozenQualificationProfile'],'changed_existing_functions':['version','noSessionQueueHistory','bootstrapAdmission'],'mode3_native_ordinary_history_unchanged':True})
print(json.dumps({'source_ref':sr,'tests_ref':tr,'input_count':len(rows),'drift':0,'target_calls':0},ensure_ascii=False))
