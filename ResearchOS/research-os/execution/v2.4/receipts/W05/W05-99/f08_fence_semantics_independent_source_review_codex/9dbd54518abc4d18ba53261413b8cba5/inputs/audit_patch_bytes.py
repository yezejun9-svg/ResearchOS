import sys
sys.dont_write_bytecode = True
import pathlib, hashlib, json, re
OWN=pathlib.Path(__file__).resolve().parent
def ref(path):
    raw=path.read_bytes();return {'path':path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def apply(raw,patch):
    original=raw.decode('utf-8').splitlines(keepends=True)
    lines=patch.decode('utf-8').splitlines(keepends=True)
    output=[];cursor=0;index=2;hunks=0
    while index<len(lines):
        m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',lines[index])
        if m is None:raise ValueError('invalid unified hunk header')
        start=int(m[1])-1;old_count=int(m[2] or 1);new_count=int(m[4] or 1)
        if start<cursor:raise ValueError('overlapping hunk')
        output.extend(original[cursor:start]);cursor=start;index+=1;removed=0;added=0
        while index<len(lines) and not lines[index].startswith('@@ '):
            line=lines[index];kind=line[0];payload=line[1:]
            if kind in ' -':
                if cursor>=len(original) or original[cursor]!=payload:raise ValueError('patch preimage mismatch')
                cursor+=1;removed+=1
            if kind in ' +':output.append(payload);added+=1
            if kind not in ' +-':raise ValueError('unsupported unified diff line')
            index+=1
        if removed!=old_count or added!=new_count:raise ValueError('hunk length mismatch')
        hunks+=1
    output.extend(original[cursor:]);return ''.join(output).encode('utf-8'),hunks
records=[]
for kind,base_name,new_name,prefix in [('source','source.v2.txt','client_cancel_finalization.v3.go.proposed.txt','source'),('tests','tests.v2.txt','client_cancel_finalization_test.v3.go.proposed.txt','tests')]:
    base=OWN/'inputs'/base_name;new=OWN/new_name
    forward=OWN/(prefix+'.v2-to-v3.patch');inverse=OWN/(prefix+'.v3-to-v2.patch')
    rebuilt,hunks=apply(base.read_bytes(),forward.read_bytes());rolled,reverse_hunks=apply(new.read_bytes(),inverse.read_bytes())
    if rebuilt!=new.read_bytes() or rolled!=base.read_bytes():raise ValueError('patch wholebyte equality mismatch')
    records.append({'kind':kind,'base_ref':ref(base),'v3_ref':ref(new),'forward_patch_ref':ref(forward),'inverse_patch_ref':ref(inverse),'forward_hunks':hunks,'inverse_hunks':reverse_hunks,'forward_wholebyte_equal':True,'inverse_wholebyte_equal':True})
roster=json.loads((OWN/'future-selectors.v3.json').read_bytes())
if len(roster['inherited_cases'])!=49 or len(roster['additional_cases'])!=8:raise ValueError('scenario roster drift')
audit={'schema':'researchos.f08-v3-static-byte-audit.v1','method':'strict unified diff text reconstruction and wholebyte comparison only','records':records,'inherited49_plus_affected24_NOT_RUN':True,'additional8_NOT_RUN':True,'changed_production_function_count':1,'new_witness_fields':0,'candidate_Go_AST_compile_gofmt_SQL_SDK_Node_HTTP_model_runs':0,'source_acceptance':False,'formal_acceptance':False,'SQL24_adoption_allowed':False}
(OWN/'static-byte-audit.json').write_bytes((json.dumps(audit,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
scope_path=OWN/'scope-and-open.json';scope=json.loads(scope_path.read_bytes())
scope['unchanged_callers_with_changed_outcome']=[{'function':'(*f08ProofValidator).admitted','when':'current=true; queueAdmission for task member'}, {'function':'(*f08ProofValidator).finalGroup','when':'current final validation; emptyQueueFinal for task member'}]
scope['static_scope_limit']='one helper diff; caller functions and callback dispatch unchanged; no compiled/transitive runtime closure assertion'
scope_path.write_bytes((json.dumps(scope,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
handoff_path=OWN/'handoff.json';handoff=json.loads(handoff_path.read_bytes());handoff['static_byte_audit_ref']=ref(OWN/'static-byte-audit.json');handoff['scope_and_open_ref']=ref(scope_path)
handoff_path.write_bytes((json.dumps(handoff,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'static_byte_audit_ref':ref(OWN/'static-byte-audit.json'),'source_hunks':records[0]['forward_hunks'],'test_hunks':records[1]['forward_hunks'],'source_test_forward_and_inverse_wholebyte_equal':True,'candidate_execution':False},ensure_ascii=False))
