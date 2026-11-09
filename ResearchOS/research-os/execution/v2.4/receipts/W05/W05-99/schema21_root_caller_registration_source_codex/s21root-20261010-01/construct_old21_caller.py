from __future__ import annotations
import ast, difflib, hashlib, json, sys
from pathlib import Path
Q=Path(__file__).resolve().parent
B=Q.parent.parent
M4=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
    p=Q/name
    with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    basis=json.loads((Q/'source-inputs.basis.json').read_text(encoding='utf-8'))
    base=Path(basis['M4_caller_ref']['path']).read_bytes()
    assert hashlib.sha256(base).hexdigest()==basis['M4_caller_ref']['sha256']
    source=base.decode('utf-8');deltas=[]
    def replace(old,new,label):
        nonlocal source
        count=source.count(old);assert count>0,(label,count)
        deltas.append(dict(kind='exact_token',label=label,count=count,old=old,new=new));source=source.replace(old,new)
    replace('Main23','old21','display_name')
    replace('MAIN23','OLD21','policy_identifiers')
    replace('main23','old21','scope_and_schema_names')
    replace('FRESH_CURRENT_OLD21_PROGRAMME_BUILD','HISTORICAL_SCHEMA21_PROGRAMME_BUILD','distinct_slice')
    replace('fresh_old21_programme_build','schema21_programme_build','distinct_key')
    replace('ROOT_REGISTERED_PENDING_FRESH_OLD21_BUILD','ROOT_REGISTERED_PENDING_SCHEMA21_BUILD','distinct_state')
    replace('fresh-old21-','old21-build-','output_prefix')
    replace('old21-build-caller-','old21-caller-','caller_prefix')
    replace('old21-build-registration-','old21-registration-','registration_prefix')
    replace('>= 371','>= 373','baseline_CP_lower_bound')
    replace('>= 175','>= 177','baseline_OW_lower_bound')
    replace('POST_PUBLIC371_ROOT_CANON_REQUIRED','ROOT_CURRENT_CANON_REQUIRED','remove_public_lineage_label')
    replace('PHASES = ("prepare", "go-version", "list-declared", "list-export", "build-old21", "inspect-binary")',
            'PHASES = ("prepare", "go-version", "control-declared", "control-export", "control-build", "control-inspect", "backup-declared", "backup-export", "backup-build", "backup-inspect", "complete")','dual_entry_phases')
    # Replace the obsolete fixed Main23 nonauthor-review constants with actual Task66 Source pins.
    start=source.index('BUILDER_REVIEW =');end=source.index('_guard_module = None',start)
    refs=basis['builder_source_refs'];fixed=dict(hdf=basis['builder_source_hdf_ref'],mf=basis['builder_source_mf_ref'],**refs)
    old=source[start:end];new='BUILDER_SOURCE_REFS = '+repr(fixed)+'\n'
    source=source[:start]+new+source[end:];deltas.append(dict(kind='constant_span',old=old,new=new))
    def function(name,new):
        nonlocal source
        tree=ast.parse(source);node=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
        lines=source.splitlines(keepends=True);a=sum(len(x) for x in lines[:node.lineno-1]);b=sum(len(x) for x in lines[:node.end_lineno])
        old=source[a:b];source=source[:a]+new.rstrip()+'\n'+source[b:]
        deltas.append(dict(kind='AST_byte_span',name=name,old=old,new=new.rstrip()+'\n'))
    function('validate_builder_chain',r'''
def validate_builder_chain(review_refs, review, review_mf, decision, source, source_mf, contract):
    need(type(review_refs) is dict and set(review_refs) == {"hdf", "mf", "decision"}, "EXACT_BUILDER_REVIEW_REFS")
    need(review.get("status") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION" and decision.get("verdict") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", "BUILDER_SOURCE_NOT_ACCEPTED")
    reviewer = decision.get("review_author")
    need(type(reviewer) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", reviewer) and reviewer not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR) and reviewer == review.get("review_author") and decision.get("source_author") == review.get("source_author") == BUILDER_AUTHOR and decision.get("independent_non_author") is True, "BUILDER_NONAUTHOR_REQUIRED")
    need(same_ref(review["decision_ref"], review_refs["decision"]) and same_ref(review["manifest_ref"], review_refs["mf"]) and any(same_ref(review_refs["decision"], x) for x in review_mf["members"]), "BUILDER_REVIEW_CHAIN")
    for field, key in (("author_hdf_ref", "hdf"), ("author_mf_ref", "mf")):
        need(same_ref(decision[field], review[field]) and same_ref(decision[field], BUILDER_SOURCE_REFS[key]), "BUILDER_AUTHOR_REF_MISMATCH")
    need(source.get("source_author") == BUILDER_AUTHOR and same_ref(source["manifest_ref"], BUILDER_SOURCE_REFS["mf"]), "BUILDER_SOURCE_AUTHOR")
    for field, decision_field in (("builder_ref", "author_builder_ref"), ("contract_ref", "author_contract_ref"), ("input_manifest_ref", "author_input_manifest_ref")):
        need(same_ref(source[field], decision[decision_field]) and same_ref(source[field], BUILDER_SOURCE_REFS[field]) and any(same_ref(source[field], member) for member in source_mf["members"]), "BUILDER_SOURCE_HDF_CHAIN")
    need(same_ref(source["frozen_source_manifest_ref"], BUILDER_SOURCE_REFS["frozen_source_manifest_ref"]), "FROZEN_SCHEMA21_SOURCE_REQUIRED")
    need(same_ref(contract["builder_ref"], source["builder_ref"]) and same_ref(contract["input_manifest_ref"], source["input_manifest_ref"]) and same_ref(contract["frozen_source_manifest_ref"], source["frozen_source_manifest_ref"]) and contract.get("schema") == "researchos.old21-programme-builder-contract.v2" and contract.get("schema_version") == 21 and contract.get("source_author") == BUILDER_AUTHOR and contract.get("source_commit") == "f6e4a0ed54d697c7214a75743cd1b83dc3685ddb" and contract.get("historical_source_file_count") == 272, "BUILDER_CONTRACT_CHAIN")
    sql = contract["runtime_source_refs"]
    need(sorted(int(Path(k).name[:4]) for k in sql if k.startswith("migrations/sqlite/")) == list(range(1, 22)), "EXACT_SCHEMA21_NUMBERED_SQL")
    need(contract.get("phases") == list(PHASES), "DUAL_CONTROL_BACKUP_PHASE_CONTRACT")
    need(decision.get("formal_programme_qualification") is False and decision.get("candidate_program_ref") is None and decision.get("qualification_ref") is None and decision.get("formal_acceptance") is False and decision.get("execution_grant", False) is False, "SOURCE_REVIEW_NOT_PROGRAMME_QUALIFICATION")
    return True
''')
    function('builder_chain',r'''
def builder_chain(review_refs, witness_ref):
    need(type(review_refs) is dict and set(review_refs) == {"hdf", "mf", "decision"}, "EXACT_BUILDER_REVIEW_REFS")
    review = doc(review_refs["hdf"]); review_mf = manifest(review_refs["mf"]); decision = doc(review_refs["decision"])
    source = doc(BUILDER_SOURCE_REFS["hdf"]); source_mf = manifest(BUILDER_SOURCE_REFS["mf"]); contract = doc(source["contract_ref"])
    validate_builder_chain(review_refs, review, review_mf, decision, source, source_mf, contract)
    witness = doc(witness_ref)
    need(witness.get("schema") == "researchos.root-old21-builder-review-witness.v1" and witness.get("issued_by") == ROOT and witness.get("root_thread_id") == ROOT_THREAD and witness.get("review_author") == decision["review_author"], "ROOT_BUILDER_REVIEW_WITNESS")
    need(type(witness.get("review_refs")) is dict and set(witness["review_refs"]) == set(review_refs) and all(same_ref(witness["review_refs"][k], review_refs[k]) for k in review_refs), "BUILDER_REVIEW_WITNESS_REFS")
    capture = doc(witness["capture_binding_ref"])
    validate_root_capture(capture, checked(capture["original_capture_ref"]), list(review_refs.values()), "BUILDER_SOURCE_REVIEW_WITNESS", decision["review_author"])
    need(when(review["reviewed_utc"]) <= when(capture["tool_result_timestamp"]) <= when(witness["created_utc"]) <= datetime.now(timezone.utc), "BUILDER_REVIEW_WITNESS_TIME_ORDER")
    inputs = doc(source["input_manifest_ref"])
    need(type(inputs.get("items")) is list and inputs["items"], "BUILDER_SOURCE_INPUTS_REQUIRED")
    peer = doc(capture["peer_delivery_binding_ref"])
    refs = list(BUILDER_SOURCE_REFS.values()) + list(review_refs.values()) + source_mf["members"] + review_mf["members"] + [x["ref"] for x in inputs["items"]]
    refs += [witness_ref, witness["capture_binding_ref"], capture["original_capture_ref"], capture["peer_delivery_binding_ref"], peer["original_capture_ref"]]
    refs += [contract[k] for k in ("common_builder_ref", "common_source_review_ref", "base_helper_ref", "source_guard_ref", "owned_job_ref", "toolchain_lock_ref", "go_ref")]
    return {"review": review, "decision": decision, "source": source, "contract": contract, "refs": refs, "review_refs": review_refs}
''')
    function('public371_evidence','def public371_evidence(*args, **kwargs):\n    need(False, "PUBLIC22_SCOPE_CANNOT_AUTHORIZE_OLD21")\n')
    replace('source = own_review(q); builder = builder_chain(); public = public371_evidence(q["public371_registration_ref"], current)',
            'need("public371_registration_ref" not in q, "PUBLIC22_SCOPE_CANNOT_AUTHORIZE_OLD21")\n    source = own_review(q); builder = builder_chain(q["builder_review_refs"], q["builder_review_witness_ref"])','separate_Source_review')
    replace(' + public["refs"]','', 'remove_public_registration_dependency')
    replace('source = own_review(q); builder = builder_chain()', 'source = own_review(q); builder = builder_chain(q["builder_review_refs"], q["builder_review_witness_ref"])','execute_dynamic_builder_review')
    replace('"RUNTIME_QUALIFICATION_ISSUANCE"}', '"RUNTIME_QUALIFICATION_ISSUANCE", "BUILDER_SOURCE_REVIEW_WITNESS", "OLD21_BUILD_PREREQUISITES"}', 'prior_root_capture_operations')
    # Runtime manifest is a separately pinned public resource inventory, reviewed by the real nonauthor.
    replace('peer_binding, received = validate_peer_delivery(qualification["review_hostpair_binding_ref"]',
            'runtime_manifest_ref = qualification["runtime_manifest_ref"]\n    runtime_manifest = doc(runtime_manifest_ref)\n    need(runtime_manifest.get("schema") == "researchos.root-old21-runtime-manifest.v1" and runtime_manifest.get("issued_by") == ROOT and runtime_manifest.get("root_thread_id") == ROOT_THREAD and runtime_manifest.get("source_author") == CALLER_AUTHOR and runtime_manifest.get("builder_source_author") == BUILDER_AUTHOR and runtime_manifest.get("formal_acceptance") is False and runtime_manifest.get("execution_grant") is False and exact_ref_set(runtime_manifest["resource_refs"]) == exact_ref_set(qualification["resource_refs"]) and same_ref(decision["runtime_manifest_ref"], runtime_manifest_ref) and same_ref(review["runtime_manifest_ref"], runtime_manifest_ref), "RUNTIME_MANIFEST_INDEPENDENT_BINDING")\n    for field, expected in (("source_hdf_ref", source_ref), ("source_mf_ref", source_mf_ref), ("caller_ref", qualification["caller_ref"]), ("builder_contract_ref", qualification["builder_contract_ref"]), ("qualification_scope_ref", scope_ref)):\n        need(same_ref(runtime_manifest[field], expected), "RUNTIME_MANIFEST_SOURCE_SCOPE_BINDING")\n    peer_binding, received = validate_peer_delivery(qualification["review_hostpair_binding_ref"]','runtime_manifest_gate')
    replace('refs = [qualification["payload_ref"], qualification["root_issuance_binding_ref"]',
            'refs = [runtime_manifest_ref, qualification["payload_ref"], qualification["root_issuance_binding_ref"]','runtime_manifest_guard')
    insert=r'''
def prebuild_authority(actual, builder, current):
    qualification_ref = actual["runtime_qualification_ref"]
    qualification = doc(qualification_ref)
    need(same_ref(qualification["builder_contract_ref"], builder["source"]["contract_ref"]), "OLD21_QUALIFIED_BUILDER_BINDING")
    binding_ref = actual["prebuild_host_binding_ref"]; binding = doc(binding_ref)
    expected = [actual[k] for k in ("scope_ref", "facts_ref", "registration_result_ref", "runtime_qualification_ref")] + list(builder["review_refs"].values()) + current["physical_refs"]
    validate_root_capture(binding, checked(binding["original_capture_ref"]), expected, "OLD21_BUILD_PREREQUISITES")
    need(when(binding["tool_result_timestamp"]) <= when(actual["created_utc"]) <= datetime.now(timezone.utc), "PREBUILD_PAIR_MUST_ALREADY_BE_COMPLETE")
    return dict(input_manifest_ref=builder["source"]["input_manifest_ref"], source_review_ref=builder["review_refs"]["decision"], resource_qualification_ref=qualification_ref, runtime_manifest_ref=qualification["runtime_manifest_ref"], outer_host_binding_ref=binding_ref, source_author=BUILDER_AUTHOR, reviewer_actor=builder["decision"]["review_author"]), [binding_ref, binding["original_capture_ref"]]

'''
    i=source.index('class LiveScope:');source=source[:i]+insert+source[i:];deltas.append(dict(kind='insert',name='prebuild_authority',new=insert))
    function('LiveScope',r'''
class LiveScope:
    def __init__(self, actual, held, context, resource_binding):
        self.actual = actual; self.held = held; self.context = context; self.resource_binding = copy.deepcopy(resource_binding); self.next_phase = 0

    def require_registered(self, contract_ref, request_ref, source_author):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(source_author == BUILDER_AUTHOR and same_ref(contract_ref, scope["builder_contract_ref"]) and same_ref(request_ref, self.actual["case_request_ref"]), "REGISTERED_BUILDER_MISMATCH")

    def require_resources(self, contract_ref, input_manifest_ref):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(same_ref(contract_ref, scope["builder_contract_ref"]) and same_ref(input_manifest_ref, BUILDER_SOURCE_REFS["input_manifest_ref"]), "RESOURCE_CONTRACT_INPUT_MISMATCH")
        binding = self.resource_binding
        need(set(binding) == {"input_manifest_ref", "source_review_ref", "resource_qualification_ref", "runtime_manifest_ref", "outer_host_binding_ref", "source_author", "reviewer_actor"} and binding["source_author"] == BUILDER_AUTHOR and type(binding["reviewer_actor"]) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", binding["reviewer_actor"]) and binding["reviewer_actor"] not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR), "EXACT_ACTUAL_RESOURCE_AUTHORITY")
        for key in ("input_manifest_ref", "source_review_ref", "resource_qualification_ref", "runtime_manifest_ref", "outer_host_binding_ref"): checked(binding[key])
        need(same_ref(binding["input_manifest_ref"], input_manifest_ref) and same_ref(binding["resource_qualification_ref"], self.actual["runtime_qualification_ref"]) and same_ref(binding["outer_host_binding_ref"], self.actual["prebuild_host_binding_ref"]), "ACTUAL_RESOURCE_BINDING_DRIFT")
        return copy.deepcopy(binding)

    def require_phase(self, phase, request_ref, output_root):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(self.next_phase < len(PHASES) and phase == PHASES[self.next_phase] and same_ref(request_ref, self.actual["case_request_ref"]) and canonical(output_root) == canonical(scope["output_root"]), "BUILD_PHASE_SEQUENCE_OR_SCOPE")
        self.next_phase += 1

    def receipt_context(self):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        live_lease(self.actual)
        return copy.deepcopy(self.context)
''')
    replace('refs += runtime_closure(actual["runtime_qualification_ref"], builder["contract"])',
            'refs += runtime_closure(actual["runtime_qualification_ref"], builder["contract"])\n    resource_binding, prebuild_refs = prebuild_authority(actual, builder, current)\n    refs += prebuild_refs','prior_authority_before_leaf')
    replace('"source_review_ref": q["review_decision_ref"]})',
            '"source_review_ref": builder["review_refs"]["decision"], "caller_source_review_ref": q["review_decision_ref"], "resource_qualification_ref": actual["runtime_qualification_ref"], "runtime_manifest_ref": resource_binding["runtime_manifest_ref"], "prebuild_host_binding_ref": actual["prebuild_host_binding_ref"], "actual_build_hostpair_external_after_return": True}, resource_binding)','real_receipt_context')
    replace('state = leaf.run_registered_build(builder["source"]["contract_ref"], actual["case_request_ref"], live)',
            'state = leaf.run_registered_build(builder["source"]["contract_ref"], actual["case_request_ref"], live)\n        need(live.next_phase == len(PHASES) or bool(state.get("first_failure")), "INCOMPLETE_DUAL_ENTRY_PHASES")','complete_phase_observation')
    replace('actual public371 evidence','old21 Source qualification','module_doc')
    # Byte-span inverse proves every changed byte, including mechanical naming, without substring-order assumptions.
    candidate=source.encode('utf-8');compile(candidate,str(Q/'old21_root.source.py'),'exec')
    matcher=difflib.SequenceMatcher(a=base,b=candidate,autojunk=False);spans=[];rebuilt=bytearray(candidate)
    for tag,a,b,c,d in matcher.get_opcodes():
        if tag!='equal':spans.append(dict(base_start=a,base_end=b,candidate_start=c,candidate_end=d,base_hex=base[a:b].hex(),candidate_hex=candidate[c:d].hex()))
    for row in reversed(spans):rebuilt[row['candidate_start']:row['candidate_end']]=bytes.fromhex(row['base_hex'])
    assert bytes(rebuilt)==base
    p=Q/'old21_root.source.py'
    with p.open('xb') as f:f.write(candidate)
    inverse=save('exact-inverse.json',dict(schema='researchos.old21-caller-exact-inverse.v1',base_ref=basis['M4_caller_ref'],candidate_ref=pin(p),spans=spans,inverse_restores_full_base_SHA=True,deltas=deltas))
    diff=Q/'candidate.diff'
    with diff.open('xb') as f:f.write(''.join(difflib.unified_diff(base.decode('utf-8').splitlines(keepends=True),source.splitlines(keepends=True),fromfile='accepted-M4/main23_root.source.py',tofile='old21_root.source.py')).encode('utf-8'))
    print(json.dumps(dict(caller_ref=pin(p),inverse_ref=inverse,diff_ref=pin(diff),AST_valid=True,product_execution=False),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
