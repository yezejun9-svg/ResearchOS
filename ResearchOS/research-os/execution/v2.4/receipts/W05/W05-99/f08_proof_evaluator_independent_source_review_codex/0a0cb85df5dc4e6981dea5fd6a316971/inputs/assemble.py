"""Receipt-only source assembly and hash inventory. Never imports Go or SQLite."""
from pathlib import Path
import ast, difflib, hashlib, json, re

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes()
    return {'path':p.as_posix(),'sha256':sha(b),'bytes':len(b)}
def write(name,b):
    p=HERE/name
    if isinstance(b,str): b=b.encode('utf-8')
    with p.open('xb') as f: f.write(b)
    return ref(p)
def dump(name,obj):return write(name,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def once(s,a,b):
    if s.count(a)!=1:raise ValueError(('one exact assembly anchor required',a[:64],s.count(a)))
    return s.replace(a,b,1)

extra=[]
for rel in ['internal/domain/client_protocol_journal.go','internal/domain/durability_session.go','internal/domain/durability.go','internal/domain/artifact_uses.go','internal/domain/artifact_uses_proof.go','internal/domain/orchestration_dependencies.go','adapters/runtime/bridge_windows.go','ops/experiment_sandbox/async_windows.go']:
    p=ROOT/rel;b=p.read_bytes();target=HERE/'snapshots'/('final-extra-'+p.name)
    with target.open('xb') as f:f.write(b)
    extra.append({'original':ref(p),'snapshot':ref(target),'timing':'hash snapshot captured after first public source text read; not claimed as a pre-first-read measurement'})
dump('final-additional-inputs.before.json',extra)

base=(HERE/'snapshots/047-client_cancel_finalization.go.proposed.txt').read_text(encoding='utf-8')
source=once(base,'// The full source-derived authority evaluator (proof modes 0..8) is explicitly\n// unfinished and always returns F08_SOURCE_EVALUATOR_NOT_IMPLEMENTED. Installing\n// this candidate with SQL24 would block legitimate F08 writes. It is NOT ready\n// for integration, qualification, migration, or use as completion evidence.',
'''// Source-derived subset implementations are appended below. Native settlement,
// ordinary qualified admission, complete historical backup and later-epoch
// authority are explicitly OPEN. This is not a complete modes0..8 evaluator.
// Installing it with SQL24 would still block legitimate operations. No build,
// SQL execution, migration, runtime qualification or source acceptance exists.''')
source=once(source,'\t"strings"\n','\t"strings"\n\t"sort"\n\t"strconv"\n\t"time"\n')
source=once(source,'\t"modernc.org/sqlite"','\t"github.com/santhosh-tekuri/jsonschema/v6"\n\t"modernc.org/sqlite"')
source=once(source,'\treturn [3]f08Scalar{','\tvalidator, err := f08NewProofValidator(doc, e)\n\tif err != nil { return zero, err }\n\treturn [3]f08Scalar{')
start='\t\t\t\tif err := f08ProofFrame(mode, input); err != nil { return nil, err }\n\t\t\t\t// No success/derived document is emitted from structural checks.\n\t\t\t\t// Missing R1/R2/source authority logic is visible, never a TODO\n\t\t\t\t// returning true or an arbitrary caller-supplied digest oracle.\n\t\t\t\treturn nil, f08Unimplemented'
source=once(source,start,'\t\t\t\treturn validator.evaluate(mode, input)')
fragments=['registry','sources-r1','groups','admission','dispatch','origin-r2','effects','final','journal-control','later-epoch','evaluator']
for name in fragments:source+='\n\n'+(HERE/(name+'.go.proposed.txt')).read_text(encoding='utf-8')
sourceRef=write('client_cancel_finalization.go.proposed.txt',source)
write('client_cancel_finalization.go.delta.patch',''.join(difflib.unified_diff(base.splitlines(True),source.splitlines(True),fromfile='previous-6ed/client_cancel_finalization.go.proposed.txt',tofile='proposed/internal/domain/client_cancel_finalization.go')))

testBase=(HERE/'snapshots/048-client_cancel_finalization_test.go.proposed.txt').read_text(encoding='utf-8')
tests=once(testBase,'\t"encoding/json"','\t"encoding/json"\n\t"encoding/hex"')
tests=once(tests,'f08TestRequireError(t,f.functions[2],f08Unimplemented,mode,input)','f08TestRequireError(t,f.functions[2],"",mode,input) // malformed one-column tuple must still refuse; no all-error stub expectation')
tests=once(tests,'f08TestRequireError(t,f.functions[2],f08Mode,int64(3),','f08TestRequireError(t,f.functions[2],f08Unwired,int64(3),')
component=(HERE/'proof-components_test.go.proposed.txt').read_text(encoding='utf-8')
first=component.index('func f08ProofTestHex')
tests+='\n\n'+component[first:]
testRef=write('client_cancel_finalization_test.go.proposed.txt',tests)
write('client_cancel_finalization_test.go.delta.patch',''.join(difflib.unified_diff(testBase.splitlines(True),tests.splitlines(True),fromfile='previous-6ed/client_cancel_finalization_test.go.proposed.txt',tofile='proposed/internal/domain/client_cancel_finalization_test.go')))

admission=(HERE/'snapshots/009-runtime_admission.go').read_text(encoding='utf-8')
needle='\treturn Object{"mode": runtime["measurement_mode"], "runtime_id": runtime["id"], "runtime_ref": Ref(runtime, "RuntimeRegistration"), "profile_ref": profileRef'
changed=once(admission,needle,'\treturn Object{"operation": operation, "mode": runtime["measurement_mode"], "runtime_id": runtime["id"], "runtime_ref": Ref(runtime, "RuntimeRegistration"), "profile_ref": profileRef')
patchRef=write('runtime_admission.operation.proposed.patch',''.join(difflib.unified_diff(admission.splitlines(True),changed.splitlines(True),fromfile='a/internal/domain/runtime_admission.go',tofile='b/internal/domain/runtime_admission.go')))
dump('operation-producer-scope.json',{'authorized':False,'applied':False,'source_ref':json.loads((HERE/'snapshot-map.json').read_text(encoding='utf-8'))[9]['original'],'function':'(*Service).currentRuntimeAdmission','line':377,'change':'add existing parameter operation to the returned admission object only; no enum mapping, default or caller replacement','patch_ref':patchRef,'actual_checkpoint_resume_caller':'internal/domain/durability.go:362','actual_replacement_caller':'internal/domain/resources.go:178','additional_review_required':['all admission strict-key/hash consumers and runtime replay comparisons','historical original manifests remain immutable, no backfill','new original-bound operation changes manifest hash and requires exact-source qualification/revalidation','this patch alone DOES NOT implement later native/ledger/dependency closure'],'compile_or_apply':False})

privateDefs=set(re.findall(r'(?m)^func (?:\([^\n]*?\) )?(f08\w+)\(',source))
privateCalls=set(re.findall(r'\b(f08\w+)\(',source))
declaredTypes=set(re.findall(r'(?m)^type (f08\w+)\b',source))
unknown=sorted(privateCalls-privateDefs-declaredTypes)
methods=re.findall(r'(?m)^func\s*\(v \*f08ProofValidator\)\s*(\w+)\(',source)
locators={name:[i for i,line in enumerate(source.splitlines(),1) if re.match(r'^func\b.*\b'+re.escape(name)+r'\(',line)] for name in sorted(privateDefs|set(methods))}
literalSelectors=[]
active=None
for line in component.splitlines():
    m=re.match(r'^func (Test\w+)\(',line)
    if m:active=m.group(1)
    for sub in re.findall(r't\.Run\("([^"\n]+)"',line):literalSelectors.append(active+'/'+sub)
for state in ['PREPARED','STARTED','UNKNOWN']:literalSelectors.append('TestF08ProofDispatchUnknownMonotone/'+state+'_to_UNKNOWN')
literalSelectors=sorted(set(literalSelectors))
dump('future-pure-selectors.json',{'status':'NOT_COMPILED_NOT_RUN','authorized_execution':False,'new_top_selectors':re.findall(r'(?m)^func (Test\w+)\(',component),'new_expanded_leaf_selectors':literalSelectors,'new_expanded_leaf_count':len(literalSelectors),'base12top':re.findall(r'(?m)^func (Test\w+)\(',testBase),'limits':'new29 component leaves only; old proposal controls preserved except explicit removed all-unimplemented error expectation; not full F08 causal coverage','source_ref':testRef})
dump('static-text-check.json',{'kind':'TEXT_ONLY_NOT_GO_AST_NOT_COMPILE','source_ref':sourceRef,'test_ref':testRef,'private_function_count':len(privateDefs),'validator_method_count':len(set(methods)),'unresolved_private_call_names':unknown,'function_locators':locators,'metadata_script_python_ast':'checked separately before execution','target_execution_count':0,'production_source_writes':0})
print(json.dumps({'source':sourceRef,'tests':testRef,'new_leaf_selectors':len(literalSelectors),'unresolved_private_names':unknown},ensure_ascii=False))
