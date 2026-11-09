import sys
sys.dont_write_bytecode = True
import json, hashlib, difflib, pathlib, datetime, traceback

OWN = pathlib.Path(__file__).resolve().parent
ROOT = OWN.parent.parent
BASE = ROOT / 'f08_initial_profile_journal_revision_preparation_codex/bd3fe19a27f54a468431828f267cd02f'
REVIEW = ROOT / 'f08_initial_profile_journal_independent_source_review_codex/c9d3ae02dc1048138094771b6cb809e9'

def digest(raw): return hashlib.sha256(raw).hexdigest()
def ref(path):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': digest(raw), 'bytes': len(raw)}
def write(name, value):
    path = OWN / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)
def read_json(path): return json.loads(pathlib.Path(path).read_bytes())
def replace_once(raw, old, new):
    old, new = old.encode('utf-8'), new.encode('utf-8')
    if raw.count(old) != 1: raise ValueError('exact edit preimage is not unique')
    return raw.replace(old, new, 1)
def patch(name, old, new, oldname, newname):
    raw = ''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True), new.decode('utf-8').splitlines(keepends=True), fromfile=oldname, tofile=newname)).encode('utf-8')
    (OWN/name).write_bytes(raw)
    return ref(OWN/name)

def main():
    lease = write('ownership.json', {'actor': 'codex:/root/f08_fence_semantics_impl_v3', 'namespace': OWN.as_posix(), 'scope': 'additive preparation only; C01-R2 pure helper and associated fixtures', 'not_alone': True, 'other_agent_edits_not_reverted': True, 'root_sole_integrator_CAS': True, 'writes_outside_namespace': 0, 'canonical_Main_Git_cache_old_package_writes': 0, 'user_v2_4_overrides_old_project_v2_0': True, 'goal22_and_final42_accepted': False})
    failed = write('failure-origin.17042a.json', {'schema': 'researchos.tool-failure-origin.v1', 'actor': 'codex:/root/f08_fence_semantics_impl_v3', 'origin': '17042a', 'first_cause': 'read-only Get-Content used absent cwd/AGENTS.md; actual project rule file is research-os/AGENTS.md', 'command': "Get-Content -LiteralPath 'D:\\作品集\\ResearchOS\\AGENTS.md' -Raw", 'observed_tool_exit': 1, 'observed_native_exit': None, 'native_program_started': False, 'output': "Get-Content: \r\nLine |\r\n   2 |  Get-Content -LiteralPath 'D:\\作品集\\ResearchOS\\AGENTS.md' -Raw\r\n     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n     | Cannot find path 'D:\\作品集\\ResearchOS\\AGENTS.md' because it does not exist.\r\n", 'same_failed_input_retried': False, 'root_classification_required': True, 'canonical_counter_written': False})
    handoff = read_json(BASE/'handoff.json')
    review = read_json(REVIEW/'handoff.json')
    pins = [(BASE/'handoff.json', 'b8832c59a594a4fd43fdfe8a04b9fabba46a953f2005411cbf04359e442ce415'), (BASE/'manifest.json', '18b7a6dd2e33d6586c374d55f47dea1b93a05c100f3f9c366df0f0ad710a38f1'), (REVIEW/'handoff.json', '023773107dd3ffae99da19507438387697606ef75c9b7665f3bcfc572159fa87'), (REVIEW/'manifest.json', '54d6878c0368667cc5a4c2ffc9d938a7e69bcf154888d74e25e0b5c6669c0082')]
    for p,h in pins:
        if ref(p)['sha256'] != h: raise ValueError('input pin drift: '+p.as_posix())
    minref = review['minimum_fix_ref']
    if minref['sha256'] != '3356e5e85d20f77fb4154c96b14406af011deb3d2262b92bc23c3dfe3f3b4564': raise ValueError('minimum proposal pin drift')
    minimum = read_json(minref['path'])
    inputs = {}
    for manifest in [BASE/'manifest.json', REVIEW/'manifest.json']:
        data = read_json(manifest)
        for expected in data['files']:
            actual = ref(expected['path'])
            if actual != expected: raise ValueError('manifest mismatch: '+expected['path'])
            inputs[actual['path']] = actual
        r = ref(manifest); inputs[r['path']] = r
    # ROOT is receipts/W05/W05-99; derive the project from the actual folder names.
    project = next(p for p in ROOT.parents if p.name == 'research-os')
    r = ref(project/'AGENTS.md'); inputs[r['path']] = r
    before = write('inputs.before.json', {'files': list(inputs.values()), 'count': len(inputs), 'no_candidate_execution': True})
    source_path = pathlib.Path(handoff['source_ref']['path'])
    test_path = pathlib.Path(handoff['test_ref']['path'])
    source, tests = source_path.read_bytes(), test_path.read_bytes()
    if ref(source_path) != handoff['source_ref'] or ref(test_path) != handoff['test_ref']: raise ValueError('source/test reference mismatch')
    (OWN/'inputs').mkdir(exist_ok=True)
    (OWN/'inputs/source.v2.txt').write_bytes(source)
    (OWN/'inputs/tests.v2.txt').write_bytes(tests)
    (OWN/'inputs/minimum-fix-proposal.json').write_bytes(pathlib.Path(minref['path']).read_bytes())
    src_old = '\t\trs:=s.selectRows("receipts",[]int{1,2,3},[]any{q[1],q[6],q[2]})\n\t\tswitch q[14] {\n\t\tcase "ENQUEUED":\n\t\t\tif q[16]!=nil || len(rs)!=0 || !f08Equal(q[15],f08Number(1)){return f08Binding}\n\t\tcase "DROPPED":\n\t\t\tif _,e=f08String(q[16]);e!=nil{return e}\n\t\t\tif len(rs)!=1 || rs[0][0]!=q[16] || rs[0][4]!="CANCEL_FENCE" || f[4]!="CANCEL_FENCED" || !f08Equal(q[15],f08Number(2)){return f08Binding}\n\t\t\tsealed,e:=f08Integer(f[6],n);if e!=nil || sealed<n || sealed>accepted{return f08Binding}\n\t\tdefault: return f08NativeProofGap\n\t\t}'
    src_new = '\t\trs:=s.selectRows("receipts",[]int{1,2,3},[]any{q[1],q[6],q[2]})\n\t\t// Frozen SQL22 starts revision1; every accepted command increments it.\n\t\t// Subtraction after the lower bound avoids overflowing accepted+1/+2.\n\t\tsealed,e:=f08Integer(f[6],0);if e!=nil || sealed>accepted{return f08Binding}\n\t\trevision,e:=f08Integer(f[13],accepted);if e!=nil || revision-accepted<1{return f08Binding}\n\t\t// Restore and unimplemented sealing/SDK histories retain typed OPEN.\n\t\tif !f08Equal(f[12],f08Number(0)){return f08NativeProofGap}\n\t\tswitch q[14] {\n\t\tcase "ENQUEUED":\n\t\t\tif f[4]=="CANCEL_FENCED"{return f08Binding}\n\t\t\tif f[4]!="OPEN"{return f08NativeProofGap}\n\t\t\tif sealed>=n || q[16]!=nil || len(rs)!=0 || !f08Equal(q[15],f08Number(1)){return f08Binding}\n\t\tcase "DROPPED":\n\t\t\tif _,e=f08String(q[16]);e!=nil{return e}\n\t\t\tif len(rs)!=1 || rs[0][0]!=q[16] || rs[0][4]!="CANCEL_FENCE" || f[4]!="CANCEL_FENCED" || !f08Equal(q[15],f08Number(2)) || revision-accepted<2{return f08Binding}\n\t\t\tif sealed<n{return f08NativeProofGap}\n\t\tdefault: return f08NativeProofGap\n\t\t}'
    out_source = replace_once(source, src_old, src_new)
    fixture_old = '[]any{"fences",[]any{"p","B","session-B","generation-B","CANCEL_FENCED",f08Number(1),f08Number(1),nil,nil,nil,nil,nil,f08Number(0),f08Number(2)}}'
    fixture_new = fixture_old.replace('f08Number(0),f08Number(2)', 'f08Number(0),f08Number(3)')
    out_tests = replace_once(tests, fixture_old, fixture_new)
    out_tests = replace_once(out_tests, 'fence[13]=f08Number(1);kept:=[]any{}', 'fence[13]=f08Number(2);kept:=[]any{}')
    extra = '''
// C01-R2 pure producer-graph fixture proposal. All cases remain NOT_RUN.
// Only unrelated Task B contributes retained history; Task A has NO_SESSION.
func f08AbsenceEnqueuedFixture(t *testing.T) []any {
\tt.Helper();rows:=f08AbsenceFixture(t,true);q:=f08AbsenceRow(rows,"queue");q[14]="ENQUEUED";q[15]=f08Number(1);q[16]=nil
\tf:=f08AbsenceRow(rows,"fences");f[4]="OPEN";f[6]=f08Number(0);f[13]=f08Number(2)
\tkept:=[]any{};for _,x:=range rows{if x.([]any)[0]!="receipts"{kept=append(kept,x)}};return kept
}
func TestF08NoSessionFenceProducerBounds(t *testing.T) {
\tv:=f08AbsenceValidator(t)
\tfor _,enqueued:=range []bool{true,false}{t.Run(fmt.Sprintf("known_producer_enqueued_%v",enqueued),func(t *testing.T){
\t\trows:=f08AbsenceFixture(t,true);if enqueued{rows=f08AbsenceEnqueuedFixture(t)};f:=f08AbsenceRow(rows,"fences")
\t\twantRevision:=f08Number(3);if enqueued{wantRevision=f08Number(2)};if !f08Equal(f[13],wantRevision){t.Fatal("fixture does not include actual producer increments")}
\t\ts:=f08AbsenceDecode(t,rows);q,e:=v.queueAdmission(s,"p","A");if e!=nil||q["variant"]!="NO_SESSION"{t.Fatal(q,e)}
\t\tfinal,e:=v.emptyQueueFinal(s,"p","A",q);if e!=nil||!f08EmptyArray(final["entry_refs"])||!f08EmptyArray(final["receipt_refs"]){t.Fatal(final,e)}
\t})}
\tcases:=[]struct{name string;enqueued bool;index int;value any;want error}{
\t\t{"ENQUEUED_CLOSED_CANCEL_FENCE",true,4,"CANCEL_FENCED",f08Binding},
\t\t{"ENQUEUED_SEALED_FENCE",true,4,"SEALED",f08NativeProofGap},
\t\t{"ENQUEUED_SEALED_SEQUENCE",true,6,f08Number(1),f08Binding},
\t\t{"ENQUEUED_RESTORE_OPEN",true,12,f08Number(1),f08NativeProofGap},
\t\t{"ENQUEUED_FENCE_REVISION_BEFORE_ACCEPTANCE",true,13,f08Number(1),f08Binding},
\t\t{"DROPPED_FENCE_REVISION_BEFORE_CANCEL",false,13,f08Number(2),f08Binding},
\t}
\tfor _,tc:=range cases{t.Run(tc.name,func(t *testing.T){
\t\trows:=f08AbsenceFixture(t,true);if tc.enqueued{rows=f08AbsenceEnqueuedFixture(t)}
\t\t// Establish a valid baseline for both entrypoints before one fact changes.
\t\tvalid:=f08AbsenceDecode(t,rows);original,e:=v.queueAdmission(valid,"p","A");if e!=nil{t.Fatal("invalid baseline",e)};if _,e=v.emptyQueueFinal(valid,"p","A",original);e!=nil{t.Fatal("invalid final baseline",e)}
\t\tq:=f08AbsenceRow(rows,"queue");queueBefore:=append([]any{},q...);f:=f08AbsenceRow(rows,"fences");fenceBefore:=append([]any{},f...);f[tc.index]=tc.value
\t\tif !f08Equal(queueBefore,q){t.Fatal("queue/content/hash/locator changed")};changed:=0;for i:=range f{if !f08Equal(fenceBefore[i],f[i]){changed++;if i!=tc.index{t.Fatal("unexpected fence mutation")}}};if changed!=1{t.Fatal("control must change exactly one fence fact")}
\t\ts:=f08AbsenceDecode(t,rows);if _,e=v.queueAdmission(s,"p","A");e!=tc.want{t.Fatal("admission did not refuse with expected typed reason",e)};if _,e=v.emptyQueueFinal(s,"p","A",original);e!=tc.want{t.Fatal("final did not refuse with expected typed reason",e)}
\t})}
}
'''
    out_tests += extra.encode('utf-8')
    srcname, testname = 'client_cancel_finalization.v3.go.proposed.txt', 'client_cancel_finalization_test.v3.go.proposed.txt'
    (OWN/srcname).write_bytes(out_source); (OWN/testname).write_bytes(out_tests)
    source_patch = patch('source.v2-to-v3.patch', source, out_source, source_path.name, srcname)
    test_patch = patch('tests.v2-to-v3.patch', tests, out_tests, test_path.name, testname)
    source_inverse_patch = patch('source.v3-to-v2.patch', out_source, source, srcname, source_path.name)
    test_inverse_patch = patch('tests.v3-to-v2.patch', out_tests, tests, testname, test_path.name)
    inverse_source = replace_once(out_source, src_new, src_old)
    inverse_tests = out_tests[:-len(extra.encode('utf-8'))]
    inverse_tests = replace_once(inverse_tests, 'fence[13]=f08Number(2);kept:=[]any{}', 'fence[13]=f08Number(1);kept:=[]any{}')
    inverse_tests = replace_once(inverse_tests, fixture_new, fixture_old)
    if inverse_source != source or inverse_tests != tests: raise ValueError('wholebyte inverse mismatch')
    inverse = write('wholebyte-inverse-evidence.json', {'schema': 'researchos.wholebyte-inverse.v1', 'kind': 'metadata byte comparison only; no proposed Go executed', 'source': {'original': ref(source_path), 'v3': ref(OWN/srcname), 'reconstructed_sha256': digest(inverse_source), 'reconstructed_bytes': len(inverse_source), 'wholebyte_equal': inverse_source==source}, 'tests': {'original': ref(test_path), 'v3': ref(OWN/testname), 'reconstructed_sha256': digest(inverse_tests), 'reconstructed_bytes': len(inverse_tests), 'wholebyte_equal': inverse_tests==tests}, 'inverse_operations': [{'target': 'source', 'old_utf8': src_new, 'new_utf8': src_old}, {'target': 'tests', 'remove_exact_tail_utf8': extra}, {'target': 'tests', 'old_utf8': 'fence[13]=f08Number(2);kept:=[]any{}', 'new_utf8': 'fence[13]=f08Number(1);kept:=[]any{}'}, {'target': 'tests', 'old_utf8': fixture_new, 'new_utf8': fixture_old}]})
    roster = read_json(handoff['future_roster_ref']['path'])
    additions = [{'top':'TestF08NoSessionFenceProducerBounds','subtest_label':'known_producer_enqueued_'+v,'state':'NOT_RUN','expected_leaf_records':1} for v in ['true','false']]
    additions += [{'top':'TestF08NoSessionFenceProducerBounds','subtest_label':c['id'],'state':'NOT_RUN','expected_leaf_records':1} for c in minimum['proposed_not_run_controls']]
    selectors = write('future-selectors.v3.json', {'schema':'researchos.f08-v3-future-roster.v1','inherited_roster_ref':handoff['future_roster_ref'],'inherited_new_scenarios':49,'inherited_affected_old_scenarios':24,'inherited_all_NOT_RUN':True,'additional_declared_scenarios':len(additions),'total_new_declared_scenarios':49+len(additions),'additional_cases':additions,'inherited_cases':roster['cases'],'existing_affected_regression':roster['existing_affected_regression'],'all_state':'NOT_RUN','candidate_execution_authorized':False})
    scope = write('scope-and-open.json', {'finding_id':'C01-R2','changed_source_functions':['(*f08ProofValidator).noSessionQueueHistory'],'direct_entrypoints_affected':['(*f08ProofValidator).queueAdmission','(*f08ProofValidator).emptyQueueFinal'],'unchanged_source_outside_exact_helper_replacement':True,'changed_existing_fixtures':['f08AbsenceFixture DROPPED fence revision2 -> 3','known_enqueued_without_receipt fence revision1 -> 2'],'new_fixture_helper':'f08AbsenceEnqueuedFixture','new_test_top':'TestF08NoSessionFenceProducerBounds','new_controls':minimum['proposed_not_run_controls'],'revision_logic':'birth1 + accepted_through enqueues; supported CANCEL_FENCE adds >=1. Bound checked by revision-accepted after revision>=accepted, avoiding int64 overflow.','ENQUEUED':'OPEN, restore0, 0<=sealed<sequence<=accepted, revision>=accepted+1, queue revision1/pointerNULL/no receipts','DROPPED':'existing CANCEL_FENCE exact receipt/revision2/current locator unchanged; restore0; revision>=accepted+2; sealed>=sequence required for supported finalized subset','typed_OPEN':['SEALED ENQUEUED history','restore history','unfinalized DROPPED sealed<sequence','unknown SDK successor and native/ordinary history'],'new_witness_fields':[],'SQL_schema_changes':0,'global_profile_initial_url_windows_I02_sections_unchanged':True,'inherited_open_gates':minimum['retained_validation_gates'],'all_49_new_plus_24_affected_NOT_RUN':True,'additional_8_NOT_RUN':True,'candidate_AST_Go_compile_gofmt_SQL_SDK_Node_HTTP_model_runs':0,'SQL24_adoption_allowed':False,'callbacks_complete':False,'native_authority_granted':False,'source_acceptance':False,'formal_acceptance':False,'final42':False,'driver_adopted':False,'inherited_coverage_ref':handoff['coverage_ref'],'inherited_I02_sequence_ref':handoff['sequence_ref'],'inherited_profile_purity_ref':handoff['profile_purity_ref'],'fresh_non_author_full_source_test_review_required':True})
    afterrows = [ref(p) for p in inputs]
    if afterrows != list(inputs.values()): raise ValueError('input drift after preparation')
    after = write('inputs.after.json', {'files':afterrows,'count':len(afterrows),'drift_count':0,'original_manifests_unchanged':True})
    result = {'schema':'researchos.f08-fence-semantics-revision-handoff.v1','actor':'codex:/root/f08_fence_semantics_impl_v3','status':'PREPARATION_SOURCE_WRITTEN_NOT_COMPILED_NOT_RUN','source_writer':'STOPPED','ownership_ref':lease,'base_handoff_ref':ref(BASE/'handoff.json'),'base_manifest_ref':ref(BASE/'manifest.json'),'independent_review_handoff_ref':ref(REVIEW/'handoff.json'),'independent_review_manifest_ref':ref(REVIEW/'manifest.json'),'minimum_fix_ref':minref,'base_source_ref':handoff['source_ref'],'base_test_ref':handoff['test_ref'],'source_ref':ref(OWN/srcname),'test_ref':ref(OWN/testname),'source_patch_ref':source_patch,'test_patch_ref':test_patch,'source_inverse_patch_ref':source_inverse_patch,'test_inverse_patch_ref':test_inverse_patch,'wholebyte_inverse_ref':inverse,'scope_and_open_ref':scope,'future_roster_ref':selectors,'input_before_ref':before,'input_after_ref':after,'input_count':len(inputs),'input_drift_count':0,'new_failure_origin_ref':failed,'new_nonzero_origin_count':1,'failure_counter_written':False,'source_Main_module_Git_cache_canonical_old_package_writes':0,'candidate_execution':False,'actual_Go_AST_compile_gofmt_SQL_SDK_Node_HTTP_model_runs':0,'all_inherited49_and_affected24_state':'NOT_RUN','additional_proposed_scenarios':8,'all_additional_scenarios_state':'NOT_RUN','source_acceptance':False,'formal_acceptance':False,'SQL24_adoption_allowed':False,'driver_adopted':False,'native_authority_granted':False,'three_callbacks_complete':False,'final42':False,'root_sole_integrator_CAS':True,'required_next_step':'F08 non-author full frozen source/test review; Root controls subsequent grants','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    h = write('handoff.json', result)
    print(json.dumps({'handoff_ref':h,'source_ref':result['source_ref'],'test_ref':result['test_ref'],'failure_origin_ref':failed,'input_count':len(inputs),'state':'STOPPED_NOT_RUN'}, ensure_ascii=False))

try:
    main()
except Exception:
    trace = traceback.format_exc()
    (OWN/'prepare_v3.failed.trace.txt').write_text(trace, encoding='utf-8')
    print(trace, file=sys.stderr)
    raise
