from pathlib import Path
import ast, difflib, hashlib, json, re

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / 'f08_proof_evaluator_implementation_preparation_codex' / 'b6b765563c9640bd8a2b9e54f643352c'
REVIEW = HERE.parents[1] / 'f08_proof_evaluator_independent_source_review_codex' / '0a0cb85df5dc4e6981dea5fd6a316971'
def ref(path):
    raw = path.read_bytes()
    return {'path':path.as_posix(), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def put(name, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    with (HERE/name).open('xb') as f: f.write(data)
    return ref(HERE/name)
def check(r):
    p=Path(r['path']); a=ref(p)
    assert a['sha256']==r['sha256'] and a['bytes']==r['bytes'], ('input drift',r['path'])
    return a

source=BASE/'client_cancel_finalization.go.proposed.txt'
assert ref(source)['sha256']=='b50de13c860fa05ec402db413d71c3804601293a57d3096a3a2c135feaf39dd3'
assert ref(REVIEW/'REVIEW.md')['sha256']=='477d96f4e8fefc64f43edea348557d1df13c0a1698c444e9218c0a7cb511cc86'
base_manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
inputs=[check(r) for r in base_manifest['files']]
assert len(inputs)==117
inputs += [ref(BASE/'manifest.json')]
inputs += [ref(REVIEW/name) for name in ['handoff.json','REVIEW.md','source-review.json','next-function-group.json','mode-review.json','failure-origins.json']]
put('inputs.before.json', {'files':inputs,'base_manifest_members':117,'actual_target_calls':0})
old=source.read_bytes().decode('utf-8'); nl='\r\n' if '\r\n' in old else '\n'
helper=(HERE/'queue-absence-helper.go.proposed.txt').read_text(encoding='utf-8').replace('\n',nl)
test_add=(HERE/'queue-absence-tests.go.proposed.txt').read_text(encoding='utf-8')
new=old
marker='func (v *f08ProofValidator) queueAdmission('
assert new.count(marker)==1
new=new.replace(marker,helper+nl+marker,1)
old_a='if len(sessions)==0{if len(fences)!=0{return nil,f08Binding};return q,nil}'
new_a='if len(sessions)==0{if e:=v.noSessionQueueHistory(s,project,task);e!=nil{return nil,e};return q,nil}'
assert new.count(old_a)==1; new=new.replace(old_a,new_a,1)
old_b='if before["variant"]=="NO_SESSION"{'+nl+'\t\tif !f08Equal(q,before){return nil,f08Binding}'
new_b='if before["variant"]=="NO_SESSION"{'+nl+'\t\tif e=v.noSessionQueueHistory(s,project,task);e!=nil{return nil,e}'+nl+'\t\tif !f08Equal(q,before){return nil,f08Binding}'
assert new.count(old_b)==1;new=new.replace(old_b,new_b,1)
old_c='\treturn []f08Version{runtime,profile,context},nil'
new_c='\t// OPEN: sandbox/build/permission/timeout/output/model qualification predicates'+nl+'\t// are not fully implemented. Retained labels and hashes cannot authorize'+nl+'\t// an initial origin. Preserve the checked extraction above, then fail closed.'+nl+'\treturn nil,f08QualificationProfileGap'
assert new.count(old_c)==1;new=new.replace(old_c,new_c,1)
constant='const f08QualificationProfileGap=f08Error("F08_INITIAL_QUALIFICATION_PROFILE_PROOF_INCOMPLETE")'+nl
anchor='const f08NativeProofGap=f08Error("F08_NATIVE_PROOF_IMPLEMENTATION_INCOMPLETE")'+nl
assert new.count(anchor)==1;new=new.replace(anchor,anchor+constant,1)
# Inverse narrow-edit audit: every byte outside one new helper, two callsites,
# one explicit qualification refusal and its fixed error must be original.
inverse=new.replace(helper+nl+marker,marker,1).replace(new_a,old_a,1).replace(new_b,old_b,1).replace(new_c,old_c,1).replace(constant,'',1)
assert inverse.encode('utf-8')==source.read_bytes()
source_ref=put('client_cancel_finalization.go.proposed.txt',new.encode('utf-8'))
test_base=BASE/'client_cancel_finalization_test.v2.go.proposed.txt'
test_raw=test_base.read_bytes();tests=test_raw+nl.encode()+test_add.replace('\n',nl).encode('utf-8')
test_ref=put('client_cancel_finalization_test.go.proposed.txt',tests)
assert tests[:len(test_raw)]==test_raw
patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/internal/domain/client_cancel_finalization.go',tofile='b/internal/domain/client_cancel_finalization.go'))
patch+=''.join(difflib.unified_diff(test_raw.decode().splitlines(True),tests.decode().splitlines(True),fromfile='a/internal/domain/client_cancel_finalization_test.go',tofile='b/internal/domain/client_cancel_finalization_test.go'))
patch_ref=put('narrow-revision.proposed.patch',patch.encode('utf-8'))
put('failure-origin.a1e3bf.json',{'tool_chunk':'a1e3bf','actual_outer_exit':1,'actual_native_python_exit':1,'exit_bridge':'PowerShell command ended exit $LASTEXITCODE; Python traceback KeyError Problem','cause':'Metadata schema selection assumed $defs.Problem existed. Changed later input filters actual schema entries; failed input not retried.','raw_tool_result':'conversation chunk a1e3bf; no separate native stream artifact','product_calls':0,'counter_reset':False})
selectors=['positive_unrelated_history_false','positive_unrelated_history_true','positive_unrelated_receipt_not_current_pointer']
selectors+=['cross_task_generation_'+s for s in ['ENQUEUED','SENDING','SDK_ACCEPTED','UNKNOWN','CONSUMED','DROP_REQUESTED','DROPPED']]
selectors+=re.findall(r'\{"([a-z_]+)",func\(rows \[\]any\)',test_add)
selectors+=['receipt_only_task_A_correct_raw_hash']
assert len(selectors)==24, selectors
roster_ref=put('future-selectors.json',{'status':'NOT_RUN','new_top_selectors':1,'new_leaf_proposals':len(selectors),'selectors':['TestF08NoSessionAbsenceFullTypedSources/'+s for s in selectors],'old_tests_prefix_unchanged':ref(test_base),'command_template':['PINNED_GO','test','./internal/domain','-run','^TestF08NoSessionAbsenceFullTypedSources$','-count=1'],'execution_authorized':False,'compilation_dependency':'Separately reviewed explicit modernc FunctionImpl.Innocuous patch/fork/pin and a source write lease are required. No current driver build supports this proposed field.'})
open_rows=[
 {'id':'C01','state':'IMPLEMENTED_PROPOSAL_NOT_COMPILED','details':'Shared pure absence graph checks both NO_SESSION callsites; every Task queue history state refuses, receipt association requires matching original fence/Session/command and strict raw hash. Unrelated valid CANCEL_FENCE Task history has positive proposed controls.'},
 {'id':'C02_I01','state':'OPEN_FIXED_REFUSAL','details':'bootstrapAdmission retains component extraction but now unconditionally returns F08_INITIAL_QUALIFICATION_PROFILE_PROOF_INCOMPLETE at its former success exit. No initial origin derives successfully from this subset.'},
 {'id':'I02_FULL_MODE_CHAIN','state':'OPEN_NOT_IMPLEMENTED_NOT_RUN','details':'New source-vector fixtures validate complete frozen Task/Goal schemas and tuple storage shapes, but are absence-component fixtures, not complete R1 recursive target graph or mode0/materialization/mode1/mode5 journal success. Original request/private-header/response/ACK-to-COMPLETED full-source positive fixtures remain required.'},
 {'id':'UNRELATED_OTHER_RECEIPT_KINDS','state':'OPEN_FIXED_REFUSAL','details':'Unclassified SDK/stream receipt kinds refuse with F08_NATIVE_PROOF_IMPLEMENTATION_INCOMPLETE; this conservative limitation may block otherwise legal unrelated history until its exact original association evaluator exists. No blank exemption by kind/body label.'},
 {'id':'RETAINED_REAL_SESSION_EMPTY_FENCE','state':'UNCHANGED_NOT_RUN','details':'Non-NO_SESSION branch byte-for-byte retained; original fence/noRun/noExecution restrictions unchanged.'},
 {'id':'R1_R2_REMAINING','state':'UNCHANGED_OPEN','details':'R1 code unchanged, no new qualification. Nonempty native SDK/effects/budget/carry/prior epoch and historical final source remain OPEN; mode3 unbound; later admission.operation producer patch uninstalled.'},
 {'id':'DEPENDENCY_SQL24','state':'PROHIBITED','details':'No driver patch, SQL24, Main adoption, compilation, migration, UDF execution or Source acceptance authorized.'}
]
coverage_ref=put('coverage-and-open-matrix.json',{'rows':open_rows,'all_tests':'NOT_RUN','product_acceptance':False})
put('static-audit.json',{'kind':'METADATA_TEXT_AND_INVERSE_DIFF_ONLY','source_base':ref(source),'new_source':source_ref,'old_source_inverse_byte_equal':True,'old_tests_prefix_byte_equal':True,'new_helper_count':new.count('func (v *f08ProofValidator) noSessionQueueHistory('),'helper_calls':new.count('v.noSessionQueueHistory(s,project,task)'),'initial_former_success_removed':old_c not in new,'new_test_top_count':1,'new_proposed_leaves':24,'Go_AST_or_compile':False,'execution_calls':{'Go':0,'gofmt':0,'SQL':0,'HTTP':0,'SDK':0,'model':0},'adoption_forbidden':True})
after=[check(r) for r in inputs]
put('inputs.after.json',{'files':after,'drift':[],'old_117_manifest_unchanged':True})
print(json.dumps({'source':source_ref,'tests':test_ref,'patch':patch_ref,'coverage':coverage_ref,'selectors':roster_ref,'input_refs':len(inputs)},ensure_ascii=False))
