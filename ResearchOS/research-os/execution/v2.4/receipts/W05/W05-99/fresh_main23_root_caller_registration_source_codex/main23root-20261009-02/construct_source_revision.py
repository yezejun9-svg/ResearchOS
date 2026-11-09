import sys
sys.dont_write_bytecode=True
import ast
import difflib
import importlib.util
import json
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prep_io',Q/'read_inputs.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)

def main():
    raw=(Q/'inputs/base-main23_root.source.py').read_bytes()
    source=raw.decode('utf-8');tree=ast.parse(source)
    normalized=source.replace('\r\n','\n')
    old_functions={node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,ast.FunctionDef)}
    helper=(Q/'capture_runtime_helpers.pyfrag').read_text(encoding='utf-8')
    root_capture=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='validate_root_capture')
    lines=normalized.splitlines(True)
    old_capture=''.join(lines[root_capture.lineno-1:root_capture.end_lineno])
    replacements=[
        ('AUTHOR = "codex:/root/native_temp_independent_review"','CALLER_AUTHOR = "codex:/root/backup_regression_resources"\nBUILDER_AUTHOR = "codex:/root/native_temp_independent_review"\nAUTHOR = CALLER_AUTHOR'),
        (old_capture,helper.rstrip()+'\n'),
        ('validate_root_capture(capture, raw, [request[x] for x in ("review_hdf_ref", "review_mf_ref", "review_decision_ref")])','validate_root_capture(capture, raw, [request[x] for x in ("review_hdf_ref", "review_mf_ref", "review_decision_ref")], "SOURCE_REVIEW_WITNESS", reviewer)'),
        ('    refs += doc(source["source_inputs_ref"])["references"]','    peer_ref = capture["peer_delivery_binding_ref"]\n    refs += [peer_ref, doc(peer_ref)["original_capture_ref"]]\n    refs += doc(source["source_inputs_ref"])["references"]'),
        ('validate_root_capture(live_capture, checked(live_capture["original_capture_ref"]), q["before_canonical_refs"])','validate_root_capture(live_capture, checked(live_capture["original_capture_ref"]), q["before_canonical_refs"], "POSTREVIEW_CURRENT_FOUR")'),
        ('validate_root_capture(capture, checked(capture["original_capture_ref"]), [facts_ref] + current["requested_refs"])','validate_root_capture(capture, checked(capture["original_capture_ref"]), [facts_ref] + current["requested_refs"], "ACTIVATION_FACTS_CURRENT_FOUR")'),
        ('qualification.get("schema") == "researchos.root-main23-qualified-runtime.v1"','qualification.get("schema") == "researchos.root-main23-qualified-runtime.v2"'),
        ('qualification.get("review_author") not in (None, "", ROOT, AUTHOR)','qualification.get("review_author") not in (None, "", ROOT, CALLER_AUTHOR, BUILDER_AUTHOR)'),
        ('    locked = doc(contract["toolchain_lock_ref"]); python = pin(sys.executable)','    review_refs = runtime_review_chain(qualification_ref, qualification, contract)\n    locked = doc(contract["toolchain_lock_ref"]); python = pin(sys.executable)'),
        ('return [qualification_ref, qualification["review_decision_ref"], contract["toolchain_lock_ref"]] + qualification["resource_refs"]','return [qualification_ref, contract["toolchain_lock_ref"]] + review_refs + qualification["resource_refs"]'),
        ('need(source_author == AUTHOR and same_ref(contract_ref, scope["builder_contract_ref"])','need(source_author == BUILDER_AUTHOR and same_ref(contract_ref, scope["builder_contract_ref"])'),
    ]
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validate_builder_chain')
    builder_before=''.join(lines[node.lineno-1:node.end_lineno])
    builder_after=re.sub(r'\bAUTHOR\b','BUILDER_AUTHOR',builder_before)
    replacements.insert(1,(builder_before,builder_after))
    actual=[]
    for before,after in replacements:
        text=source.replace('\r\n','\n')
        assert text.count(before)==1,'exact replacement: '+before[:90]
        start=text.index(before);positions=[0];offset=0
        while offset<len(source):
            offset+=2 if source[offset:offset+2]=='\r\n' else 1
            positions.append(offset)
        lo,hi=positions[start],positions[start+len(before)]
        original=source[lo:hi];ending='\r\n' if '\r\n' in original else '\n'
        revised=after.replace('\n',ending)
        actual.append({'before':original,'after':revised,'start':lo})
        source=source[:lo]+revised+source[hi:]
    inverse=source
    for item in reversed(actual):
        start=item['start'];end=start+len(item['after'])
        assert inverse[start:end]==item['after']
        inverse=inverse[:start]+item['before']+inverse[end:]
    assert inverse.encode('utf-8')==raw
    candidate=source.encode('utf-8');after_tree=ast.parse(source)
    new_functions={node.name:ast.dump(node,include_attributes=False) for node in after_tree.body if isinstance(node,ast.FunctionDef)}
    changed={'validate_builder_chain','validate_root_capture','own_review','future_request','runtime_closure','register'}
    unchanged=sorted(set(old_functions)-changed)
    assert all(old_functions[name]==new_functions[name] for name in unchanged)
    original_controls=(Q/'inputs/base-source_controls.py').read_text(encoding='utf-8')
    controls=original_controls
    old_pre='case("current-pre371-canon-rejected", lambda: m.current_four(before, revisions), "POST_PUBLIC371_ROOT_CANON_REQUIRED")'
    new_pre='''# Preserve the pre371 rejection with a synthetic legacy fixture now that actual Canon is 371.
legacy_canon = list(m.CANON)
legacy_checked = m.checked
legacy_documents = copy.deepcopy(documents)
legacy_documents[0]["revision"] = 370; legacy_documents[1]["revision"] = 174
legacy_refs = copy.deepcopy(before)
legacy_map = {m.canonical(ref["path"]): m.encoded(value) for ref,value in zip(legacy_refs,legacy_documents)}
m.checked = lambda ref: legacy_map[m.canonical(ref["path"])]
try:
    case("current-pre371-canon-rejected", lambda: m.current_four(legacy_refs, dict(revisions, checkpoint=370, path_ownership=174)), "POST_PUBLIC371_ROOT_CANON_REQUIRED")
finally: m.checked = legacy_checked'''
    assert controls.count(old_pre)==1
    controls=controls.replace(old_pre,new_pre,1)
    old_released='lambda: live.require_registered(original, original, m.AUTHOR), "ROOT_RESOURCE_CLOSURE_RELEASED"'
    new_released='lambda: live.require_registered(original, original, m.BUILDER_AUTHOR), "ROOT_RESOURCE_CLOSURE_RELEASED"'
    assert controls.count(old_released)==1;controls=controls.replace(old_released,new_released,1)
    names=lambda code:[node.args[0].value for node in ast.walk(ast.parse(code)) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='case' and node.args and isinstance(node.args[0],ast.Constant)]
    assert names(original_controls)==names(controls) and len(names(controls))==22
    lib.save('main23_root.source.py',candidate)
    lib.save('source_controls.py',controls.encode('utf-8'))
    lib.save('caller.diff',''.join(difflib.unified_diff(raw.decode('utf-8').splitlines(True),source.splitlines(True),fromfile='v1/main23_root.source.py',tofile='v2/main23_root.source.py')).encode('utf-8'))
    lib.save('controls.diff',''.join(difflib.unified_diff(original_controls.splitlines(True),controls.splitlines(True),fromfile='v1/source_controls.py',tofile='v2/source_controls.py')).encode('utf-8'))
    lib.savejson('exact-inverse.json',{'schema':'researchos.main23-root-v2-exact-inverse.v1','original_ref':lib.pin(lib.BASE/'main23_root.source.py',raw),'candidate_ref':lib.pin(Q/'main23_root.source.py',candidate),'patches':actual,'inverse_original_bytes_equal':True})
    lib.savejson('static-verification.json',{'schema':'researchos.main23-root-v2-static-verification.v1','source_author':'codex:/root/backup_regression_resources','v1_caller_author':'codex:/root/native_temp_independent_review','unchanged_builder_author':'codex:/root/native_temp_independent_review','AST_pass':True,'inverse_exact_bytes':True,'original_functions':len(old_functions),'changed_original_functions':sorted(changed),'unchanged_original_functions':unchanged,'new_functions':sorted(set(new_functions)-set(old_functions)),'original_22_control_names_preserved':names(controls),'original_22_assertions_preserved':True,'control_fixture_deltas':['pre371 historical revision predicate is synthetic now that actual Canon is371','released-builder-runtime case uses explicit truthful BUILDER_AUTHOR'],'TP_transform_AST_unchanged':old_functions['projection']==new_functions['projection'],'Scope_job_phases_schema_private_native_policy_unchanged':True,'Main_writes':0,'Canon_writes':0,'Native_Go_SQLite_model_runs':0,'actual_future_qualification_ref':None,'actual_future_request_ref':None,'authority':'NONE'})
    print(json.dumps({'candidate_ref':lib.pin(Q/'main23_root.source.py',candidate),'preserved_controls':22,'unchanged_functions':len(unchanged),'new_functions':len(set(new_functions)-set(old_functions)),'authority':'NONE'},ensure_ascii=False))

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
