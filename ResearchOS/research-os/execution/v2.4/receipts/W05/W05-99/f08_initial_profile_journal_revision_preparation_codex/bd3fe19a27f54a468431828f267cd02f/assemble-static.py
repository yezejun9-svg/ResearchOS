from pathlib import Path
import ast, hashlib, json, difflib, re

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
B=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_queue_absence_revision_preparation_codex/b9a560ed59c24bef9b9e01d2d91c4b84'
R=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_queue_absence_independent_revision_review_codex/1cff95bc559c45d68414e44d5553c7a1'
P=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_implementation_preparation_codex/b6b765563c9640bd8a2b9e54f643352c'
D=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_innocuous_driver_preparation_codex/da3c883ec6684c4487dbe36ff45affe4'
def ref(p):
    raw=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def doc(p): return json.loads(p.read_text(encoding='utf-8'))
def write(name,raw):
    p=OUT/name
    if isinstance(raw,str):raw=raw.encode('utf-8')
    with p.open('xb') as f:f.write(raw)
    return ref(p)
def js(name,value):return write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def verify(row):
    p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
    got=ref(p)
    assert got['sha256']==row['sha256'] and got['bytes']==row['bytes'],row['path']
    return got
assert OUT.name=='bd3fe19a27f54a468431828f267cd02f'
assert ref(B/'client_cancel_finalization.go.proposed.txt')['sha256']=='9d7bbc20cf68e4a9aa46ecd6cd763b7f2a7bcf1b3063baf8e2863fd6e5f7314f'
assert ref(B/'manifest.json')['sha256']=='0d7982363d2b77ea8ac5117dd014bb434e8d580b07d5c413ccb9f8433db4095f'
assert ref(R/'REVIEW.md')['sha256']=='0573a673e294d73322f3bb467c6fd18eba775959a0f6b34f39459b6a7b0e854e'
inputs={}
for row in doc(B/'public-inputs.final.json')['files']+doc(B/'manifest.json')['files']:
    got=verify(row);inputs[got['path']]=got
for p in [B/'manifest.json',B/'public-inputs.final.json',R/'REVIEW.md',R/'source-review.json',R/'handoff.json',R/'manifest.json',D/'handoff.json',D/'modernc-sqlite-innocuous.patch',ROOT/'internal/domain/runtime_model.go',ROOT/'internal/domain/budget.go',ROOT/'internal/domain/runtime_qualification.go',ROOT/'.local/tools/go1.27.1/go/src/internal/filepathlite/path_windows.go']:
    inputs[p.as_posix()]=ref(p)
before=sorted(inputs.values(),key=lambda r:r['path'])
js('inputs.before.json',{'schema':'researchos.public-inputs.v1','capture_stage':'before receipt assembly; sealed prior refs rehashed, no historical first-read claim','files':before})
snap=OUT/'additional-source-snapshots';snap.mkdir(exist_ok=False)
for i,p in enumerate([ROOT/'internal/domain/runtime_model.go',ROOT/'internal/domain/budget.go',ROOT/'internal/domain/runtime_qualification.go',ROOT/'.local/tools/go1.27.1/go/src/internal/filepathlite/path_windows.go']):
    write(f'additional-source-snapshots/{i:02d}-{p.name}',p.read_bytes())
old=(B/'client_cancel_finalization.go.proposed.txt').read_bytes().decode('utf-8')
source=old;changes=[]
def replace(label,before,after):
    global source
    assert source.count(before)==1,(label,source.count(before))
    source=source.replace(before,after,1);changes.append({'label':label,'before':before,'after':after})
nl='\r\n' if '\r\n' in old else '\n'
def fragment(name):return (OUT/name).read_text(encoding='utf-8').replace('\n',nl)
replace('pure URL parser import','\t"math/big"'+nl,'\t"math/big"'+nl+'\t"net/url"'+nl)
start=source.index('func (v *f08ProofValidator) noSessionQueueHistory(')
end=source.index(nl+'func ',start+5)
replace('C01 receipt locator and known producer graph',source[start:end],'func (v *f08ProofValidator)'+fragment('queue-absence-helper.go.proposed.txt').split('func (v *f08ProofValidator)',1)[1].rstrip())
project_old='\tif body["id"]!=id || body["project_id"]!=project || !f08Equal(body["revision"],r["revision"]){return zero,f08Binding}'
project_new='''\t// Service.put stores schema-valid GLOBAL policies under Str(nil)=="".
\t// This exception follows full entity-schema validation above, and never
\t// applies to another entity, a foreign project or a non-GLOBAL policy.
\tprojectMatches:=body["project_id"]==project
\tif project=="" && (kind=="BudgetPolicy" || kind=="RunPolicy") && body["project_id"]==nil && body["scope_type"]=="GLOBAL" && body["scope_id"]=="global" && body["parent_policy_id"]==nil { projectMatches=true }
\tif body["id"]!=id || !projectMatches || !f08Equal(body["revision"],r["revision"]){return zero,f08Binding}'''.replace('\n',nl)
replace('I02 schema-bound GLOBAL storage mapping',project_old,project_new)
needle='func (v *f08ProofValidator) bootstrapAdmission('
replace('C02 pure profile helper group',needle,fragment('profile-predicates.go.proposed.txt')+nl+needle)
needle='\tif plan["runtime_id"]!=runtime.id || !f08Equal(plan["profile_ref"],a["profile_ref"]) || !f08Equal(plan["required_capabilities"],a["requested_capabilities"]){return nil,f08Binding}'
replace('C02 invoke complete captured profile subset',needle,needle+nl+'\tif e=f08FrozenQualificationProfile(p,runtime.body,task.body,plan,a["profile_ref"].(map[string]any),profile.body);e!=nil{return nil,e}')
old_comment='''\t// OPEN: sandbox/build/permission/timeout/output/model qualification predicates
\t// are not fully implemented. Retained labels and hashes cannot authorize
\t// an initial origin. Preserve the checked extraction above, then fail closed.'''.replace('\n',nl)
new_comment='''\t// Captured dispatch/model/profile predicates are implemented above. OPEN:
\t// the source34 vector contains no current authorRoot/OWNER/project grant,
\t// runtimeExecutorAllowed grant or captured effective-state/clock authority.
\t// Plan permission labels cannot prove those original producer checks.
\t// This is a profile component result, never complete qualification authority.'''.replace('\n',nl)
replace('C02 explicit remaining authority gap',old_comment,new_comment)
inverse=source
for change in reversed(changes):
    assert inverse.count(change['after'])==1,change['label']
    inverse=inverse.replace(change['after'],change['before'],1)
assert inverse==old
source_ref=write('client_cancel_finalization.go.proposed.txt',source)
js('source-hunks.inverse.json',{'schema':'researchos.text-hunks.v1','base_ref':ref(B/'client_cancel_finalization.go.proposed.txt'),'candidate_ref':source_ref,'inverse_exact':True,'hunks':changes})
write('client_cancel_finalization.go.proposed.patch',''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile='b9/internal/domain/client_cancel_finalization.go',tofile='proposed/internal/domain/client_cancel_finalization.go')))
oldtests=(B/'client_cancel_finalization_test.go.proposed.txt').read_bytes().decode('utf-8')
tests=oldtests.replace('\t"fmt"'+nl,'\t"fmt"'+nl+'\t"sort"'+nl,1)
line=next(x for x in tests.splitlines(True) if 't.Run("positive_unrelated_receipt_not_current_pointer"' in x)
replacement='\tt.Run("negative_unrelated_receipt_missing_current_pointer",func(t *testing.T){rows:=f08AbsenceFixture(t,true);f08AbsenceRow(rows,"queue")[16]=nil;s:=f08AbsenceDecode(t,rows);if _,e:=v.queueAdmission(s,"p","A");e==nil{t.Fatal("known producer current pointer omitted")};before,e:=v.queueAdmission(f08AbsenceDecode(t,f08AbsenceFixture(t,false)),"p","A");if e!=nil{t.Fatal(e)};if _,e=v.emptyQueueFinal(s,"p","A",before);e==nil{t.Fatal("final accepted missing producer pointer")}})'+nl
assert tests.count(line)==1;tests=tests.replace(line,replacement,1)
# Old single-fact cases no longer pre-remove a valid current pointer, which
# would otherwise mask their intended mutation behind the new pointer guard.
needle='rows:=f08AbsenceFixture(t,true);f08AbsenceRow(rows,"queue")[16]=nil;tc.mutate(rows)'
assert tests.count(needle)==1;tests=tests.replace(needle,'rows:=f08AbsenceFixture(t,true);tc.mutate(rows)',1)
test_prefix=tests
tests+=nl+fragment('profile-and-locator-tests.go.proposed.txt')+nl+fragment('journal-full-fixtures.go.proposed.txt')
inverse_test=test_prefix.replace('\t"fmt"'+nl+'\t"sort"'+nl,'\t"fmt"'+nl,1).replace(replacement,line,1).replace('rows:=f08AbsenceFixture(t,true);tc.mutate(rows)',needle,1)
assert inverse_test==oldtests
test_ref=write('client_cancel_finalization_test.go.proposed.txt',tests)
write('client_cancel_finalization_test.go.proposed.patch',''.join(difflib.unified_diff(oldtests.splitlines(True),tests.splitlines(True),fromfile='b9/internal/domain/client_cancel_finalization_test.go',tofile='proposed/internal/domain/client_cancel_finalization_test.go')))
defs=re.findall(r'^func\s+(?:\([^\n]*?\)\s*)?([A-Za-z_]\w*)\s*\(',source,re.M)
assert len(defs)==len(set(defs)), 'duplicate source function'
olddefs=set(re.findall(r'^func\s+(?:\([^\n]*?\)\s*)?([A-Za-z_]\w*)\s*\(',old,re.M))
newdefs=sorted(set(defs)-olddefs)
tests_top=re.findall(r'^func\s+(Test\w+)\(',tests,re.M)
assert len(tests_top)==len(set(tests_top))
def registry(text):
    start=text.index('func f08SourceRules()')
    return text[start:text.index(nl+'}'+nl,start)+len(nl+'}'+nl)]
assert registry(source)==registry(old) and len(registry(old))>1000
js('static-source-audit.json',{'schema':'researchos.f08-static-text-audit.v1','source_ref':source_ref,'test_ref':test_ref,'source_inverse_exact_b9':True,'test_inverse_exact_b9':True,'source_hunk_count':len(changes),'new_source_functions':newdefs,'duplicate_functions':False,'go_ast_parsed':False,'go_compile':'NOT_RUN','gofmt':'NOT_RUN','tests':'NOT_RUN','sql':'NOT_RUN','source_registry34_preserved':True,'test_top_function_inventory':tests_top,'limitations':['Text function inventory is not a Go parser or type checker.','Pure proposals are not producer execution or SQLite proof.','Initial qualification authority remains explicit refusal after captured profile subset.']})
after=[verify(r) for r in before]
js('inputs.after.json',{'schema':'researchos.public-inputs.v1','files':after,'drift_count':0})
ast.parse(Path(__file__).read_text(encoding='utf-8'))
print(json.dumps({'status':'RECEIPT_TEXT_ASSEMBLED_ONLY','source':source_ref,'tests':test_ref,'inputs':len(before),'drift':0,'target_calls':0},ensure_ascii=False))
