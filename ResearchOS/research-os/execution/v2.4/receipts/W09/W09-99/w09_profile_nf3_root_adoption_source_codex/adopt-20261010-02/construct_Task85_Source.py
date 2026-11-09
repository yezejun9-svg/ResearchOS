"""Task85 finite Source preparation. No registrar stage, issuer or product call."""
import ast, base64, copy, difflib, hashlib, json, types
from pathlib import Path

Q = Path(__file__).resolve().parent
BASE = Q.parent / 'adopt-20261010-01'
AUTHOR = 'codex:/root/backup_regression_resources'
OLD_AUTHOR = 'codex:/root/native_temp_independent_review'
THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'
R = Path('D:/作品集/ResearchOS/research-os')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
def pin(path):
    path = Path(path); raw = path.read_bytes()
    return dict(path=str(path), sha256=sha(raw), bytes=len(raw))
def save_raw(name, raw):
    path = Q / name; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle: handle.write(raw)
    return pin(path)
def save(name, value): return save_raw(name, encoded(value))
def exact(ref):
    assert type(ref) is dict and set(ref) == {'path','sha256','bytes'}
    assert pin(ref['path']) == ref
    return Path(ref['path']).read_bytes()

def edit_source(raw, changes):
    edits = []
    for old, new, role in changes:
        assert raw.count(old) == 1, role
        start = raw.index(old)
        edits.append(dict(base_start=start, base_end=start+len(old), old=old, new=new, role=role))
    edits.sort(key=lambda row: row['base_start'])
    output = bytearray(); cursor = 0
    for row in edits:
        assert cursor <= row['base_start']
        output.extend(raw[cursor:row['base_start']]); row['candidate_start'] = len(output)
        output.extend(row['new']); row['candidate_end'] = len(output); cursor = row['base_end']
    output.extend(raw[cursor:]); candidate = bytes(output)
    restored = candidate
    for row in reversed(edits):
        assert restored[row['candidate_start']:row['candidate_end']] == row['new']
        restored = restored[:row['candidate_start']] + row['old'] + restored[row['candidate_end']:]
    assert restored == raw
    public = [dict(**{k:v for k,v in row.items() if k not in ('old','new')},
        base_bytes_b64=base64.b64encode(row['old']).decode('ascii'),
        candidate_bytes_b64=base64.b64encode(row['new']).decode('ascii')) for row in edits]
    return candidate, public

def load(raw, name, path):
    module = types.ModuleType(name); module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module

def main():
    hraw = (BASE/'HDF.json').read_bytes(); h = json.loads(hraw)
    assert sha(hraw).startswith('fae54fd') and len(hraw) == 5083
    mfraw = exact(h['manifest_ref']); mf = json.loads(mfraw)
    assert h['manifest_ref']['sha256'] == '868655ac82c62186414cc58ce05ed8b82d9f4acd88d5c62fe9dc9fd20e19be0b'
    for key in ('caller_ref','core_ref','main_pair_ref','contract_ref','input_pins_ref','controls_ref'):
        assert h[key] in mf['members']
    inputs = json.loads(exact(h['input_pins_ref']))
    gref = inputs['refs']['guard']; graw = exact(gref)
    gm = load(graw, 'task85_guard', Path(gref['path']))
    guard = gm.SourceReadGuard(total_cap=128*1024*1024)
    source_refs = [pin(BASE/'HDF.json'), h['manifest_ref'], gref,
        *(h[key] for key in ('caller_ref','core_ref','main_pair_ref','contract_ref','input_pins_ref','controls_ref')),
        inputs['refs']['NF_choice'], pin(__file__)]
    rows = []; inverse_rows = []; guarded_summary = None
    def check(name, predicate, kind='FINITE_SOURCE_CONTROL'):
        ok = predicate()
        assert ok is True, name
        rows.append(dict(name=name, passed=True, authority='NONE', kind=kind))
    def rejected(fn):
        try: fn()
        except (ValueError, TypeError, KeyError): return True
        return False
    try:
        guard.acquire(source_refs)
        original = {key: guard.get_buffer(h[key]['path']) for key in ('caller_ref','core_ref','main_pair_ref','contract_ref','input_pins_ref','controls_ref')}
        caller = original['caller_ref']; core = original['core_ref']; pair = original['main_pair_ref']
        predicate = next(line for line in caller.splitlines(keepends=True) if b"'REGULAR_LOCAL_PATH'" in line)
        linebreak = b'\r\n' if predicate.endswith(b'\r\n') else b'\n'
        prefixes = (chr(92)*2+'?'+chr(92), chr(92)*2+'.'+chr(92))
        replacement = ("    require(':' not in value[2:] and not value.startswith(" + repr(prefixes) + "),'REGULAR_LOCAL_PATH')").encode('utf-8') + linebreak
        old_actor = repr(OLD_AUTHOR).encode('utf-8'); new_actor = repr(AUTHOR).encode('utf-8')
        candidate_caller, caller_edits = edit_source(caller, [(predicate,replacement,'ONLY_BUSINESS_PATH_PREFIX_PREDICATE'),(old_actor,new_actor,'TRUTHFUL_CURRENT_SOURCE_AUTHOR')])
        candidate_core, core_edits = edit_source(core, [(old_actor,new_actor,'TRUTHFUL_OWN_REVIEW_AUTHOR_BINDING')])
        for name, raw, cand, edits in (
            ('register_w09_adoption.source.py',caller,candidate_caller,caller_edits),
            ('adoption_core.source.py',core,candidate_core,core_edits),
            ('main_pair_bytes.source.py',pair,pair,[])):
            base_ref = save_raw('base/'+name,raw); candidate_ref = save_raw(name,cand)
            ast.parse(cand); compile(cand,str(Q/name),'exec')
            inverse_rows.append(dict(name=name,original_ref=base_ref,upstream_ref=h[{'register_w09_adoption.source.py':'caller_ref','adoption_core.source.py':'core_ref','main_pair_bytes.source.py':'main_pair_ref'}[name]],candidate_ref=candidate_ref,byte_spans=edits,complete_inverse_sha256=sha(raw),complete_inverse_matches_original=True))
        save_raw('base/root-calling-contract.source.json', original['contract_ref'])
        save_raw('input-pins.json', original['input_pins_ref'])
        reg = load(candidate_caller,'task85_reg',Q/'register_w09_adoption.source.py')
        pure = load(candidate_core,'task85_core',Q/'adoption_core.source.py')
        pairmod = load(pair,'task85_pair',Q/'main_pair_bytes.source.py')
        check('caller_and_core_current_author_Backup',lambda: reg.AUTHOR == pure.AUTHOR == AUTHOR)
        check('main_pair_entire_bytes_unchanged',lambda: pin(Q/'main_pair_bytes.source.py')['sha256'] == h['main_pair_ref']['sha256'])
        check('input_pins_entire_bytes_unchanged',lambda: pin(Q/'input-pins.json')['sha256'] == h['input_pins_ref']['sha256'])
        base_ast = ast.parse(caller); new_ast = ast.parse(candidate_caller)
        bdefs = {node.name:node for node in base_ast.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        ndefs = {node.name:node for node in new_ast.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
        check('every_caller_function_except_path_checked_AST_unchanged',lambda: set(bdefs)==set(ndefs) and all(ast.dump(bdefs[name])==ast.dump(ndefs[name]) for name in bdefs if name!='path_checked'))
        before_path, after_path = bdefs['path_checked'], ndefs['path_checked']
        check('path_checked_all_nodes_except_one_predicate_unchanged',lambda: len(before_path.body)==len(after_path.body) and all(ast.dump(left)==ast.dump(right) for index,(left,right) in enumerate(zip(before_path.body,after_path.body)) if index!=1))
        check('existing_dot_local_directory_positive',lambda: reg.path_checked(str(R/'.local')) == R/'.local')
        choice_raw = guard.get_buffer(inputs['refs']['NF_choice']['path']); choice = json.loads(choice_raw)
        found = []
        def walk(value, label=''):
            if type(value) is dict:
                if {'receipt_root','scratch_root','output_root'} <= set(value): found.append((label,value))
                for key, child in value.items(): walk(child,label+'/'+str(key))
            elif type(value) is list:
                for index, child in enumerate(value): walk(child,label+'/'+str(index))
        walk(choice)
        assert len(found)==3
        actual_paths = []
        for label, value in found:
            p = value['scratch_root']
            check('actual_NF3_scratch_root_positive_'+label,lambda p=p: reg.path_checked(p,True)==Path(p),'PUBLIC_DIRECTORY_METADATA_ONLY')
            actual_paths.append(dict(selector_location=label,receipt_root=value['receipt_root'],scratch_root=p,output_root=value['output_root'],scratch_absent=not Path(p).exists(),Source_only=True))
        bad_paths = {
            'extended_device_prefix': prefixes[0]+'D:'+chr(92)+'x',
            'device_namespace_prefix': prefixes[1]+'D:'+chr(92)+'x',
            'forward_extended_prefix': '//?/D:/x',
            'forward_device_prefix': '//./D:/x',
            'UNC': chr(92)*2+'server'+chr(92)+'share'+chr(92)+'leaf',
            'ADS': str(R/'.local')+chr(92)+'leaf:stream',
            'traversal': str(R/'.local')+chr(92)+'..'+chr(92)+'leaf',
            'relative': '.local/leaf',
            'NUL': str(R/'.local')+'\x00',
            'wrong_type': True,
            'missing_parent': str(Q/'SOURCE_NOT_CREATED_PARENT'/'leaf'),
        }
        for name,value in bad_paths.items(): check('path_reject_'+name,lambda value=value: rejected(lambda: reg.path_checked(value,True)))
        expected = [dict(path=str(path),sha256='a'*64,bytes=1) for path in pairmod.TARGETS]
        check('pure_Main_fixed_pair_value_shape_positive',lambda: pairmod.validate_pair_spec(expected,[b'x',b'y']) is None,'SYNTHETIC_NO_ROOT_AUTHORITY')
        check('pure_Main_swapped_targets_rejected',lambda: rejected(lambda: pairmod.validate_pair_spec(expected[::-1],[b'x',b'y'])))
        check('pure_Main_bool_bytes_rejected',lambda: rejected(lambda: pairmod.validate_pair_spec([{**expected[0],'bytes':True},expected[1]],[b'x',b'y'])))
        fake = dict(path=str(Q/'SYNTHETIC_UNSAVED_REF'),sha256='a'*64,bytes=1)
        binds = {key:dict(fake) for key in ('caller_ref','core_ref','main_pair_ref','contract_ref')}
        decision = dict(schema='researchos.w09-root-adoption-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/SOURCE_SYNTHETIC_REVIEWER'.lower(),source_author_id=AUTHOR,source_handoff_ref=fake,source_manifest_ref=fake,actual_executed=False,formal_acceptance=False,execution_grant=False,**binds)
        check('new_Backup_author_own_review_rejected',lambda: rejected(lambda: pure.validate_own_review({**decision,'actor_id':AUTHOR},fake,fake,binds)))
        check('old_Native_publisher_claim_rejected',lambda: rejected(lambda: pure.validate_own_review({**decision,'source_author_id':OLD_AUTHOR},fake,fake,binds)))
        old_contract = json.loads(original['contract_ref'])
        def rebound(value):
            if type(value) is dict: return {key:rebound(child) for key,child in value.items()}
            if type(value) is list: return [rebound(child) for child in value]
            if type(value) is str:
                return value.replace(str(BASE),str(Q)).replace(BASE.as_posix(),Q.as_posix())
            return value
        contract = rebound(old_contract)
        contract['source_author'] = AUTHOR
        contract['own_independent_source_review_required']['source_author_id'] = AUTHOR
        contract['source_bindings'] = {key:pin(Q/name) for key,name in (('caller_ref','register_w09_adoption.source.py'),('core_ref','adoption_core.source.py'),('main_pair_ref','main_pair_bytes.source.py'))}
        contract['input_pins_ref'] = pin(Q/'input-pins.json')
        contract['revision_provenance'] = dict(base_hdf_ref=pin(BASE/'HDF.json'),base_manifest_ref=h['manifest_ref'],base_contract_ref=h['contract_ref'],original_source_author=OLD_AUTHOR,current_patch_author=AUTHOR,current_source_thread_id=THREAD,original_Source_contribution_retained=True,business_delta='One path predicate: reject extended/device namespace prefixes only at the start; allow ordinary .local components.',identity_delta='Caller/Core AUTHOR constants and Source/contract/HDF self refs now bind truthful Backup author; require fresh non-author review.',old_68_controls_ref=h['controls_ref'],old_68_controls_passed=h['controls_passed'],old_68_controls_rerun=False,actual_AD01_successful_stage_receipts_reused_not_reexecuted=True,original_Root_failure_1109_preserved=True,original_Root_failure_1109_origin='Root-owned, not copied or reconstructed; actual Root origin ref to be supplied by Root.',future_Current4_dynamic=True,future_scope_lease_audits_or_grants_created=False)
        contract['path_checked_contract'] = dict(extended_device_prefixes=prefixes,first_absolute_local_drive_gate_unchanged=True,ADS_UNC_traversal_reparse_physical_alias_gates_unchanged=True,actual_NF3_choice_ref=inputs['refs']['NF_choice'],actual_scratch_root_observations=actual_paths,no_outside_Source_directory_created=True)
        contract_ref = save('root-calling-contract.source.json',contract)
        save('precise-byte-inverse.json',dict(schema='researchos.w09-adoption-path-prefix-byte-inverse.v1',members=inverse_rows,contract_base_ref=h['contract_ref'],contract_candidate_ref=contract_ref,contract_changes='Rebind this package own refs/author and add explicit revision/path Source-only metadata; Root/Counter/TP/runtime schemas unchanged.',actual_inverse_applied_to_Main_or_Canon=False))
        diff = ''.join(difflib.unified_diff(caller.decode('utf-8').splitlines(keepends=True),candidate_caller.decode('utf-8').splitlines(keepends=True),fromfile='AD01/register_w09_adoption.source.py',tofile='AD02/register_w09_adoption.source.py'))
        diff += ''.join(difflib.unified_diff(core.decode('utf-8').splitlines(keepends=True),candidate_core.decode('utf-8').splitlines(keepends=True),fromfile='AD01/adoption_core.source.py',tofile='AD02/adoption_core.source.py'))
        save_raw('minimal-source.diff',diff.encode('utf-8'))
        guarded_summary = dict(source_refs=source_refs,base_hdf_ref=pin(BASE/'HDF.json'),base_manifest_ref=h['manifest_ref'],base_controls_ref=h['controls_ref'],original_failure_refs=h['original_failure_refs'],actual_choice_ref=inputs['refs']['NF_choice'],actual_paths=actual_paths,caller_ref=pin(Q/'register_w09_adoption.source.py'),core_ref=pin(Q/'adoption_core.source.py'),main_pair_ref=pin(Q/'main_pair_bytes.source.py'),contract_ref=contract_ref,input_pins_ref=pin(Q/'input-pins.json'))
    finally:
        closed = guard.close(); close_ref = save('construct.source-guard.closed.json',closed)
        assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    controls_ref = save('delta-source-controls.result.json',dict(schema='researchos.w09-adoption-path-prefix-delta-controls.v1',passed=len(rows),failed=0,checks=rows,guard_ref=close_ref,old_68_controls_rerun=False,old_Q_NF3_suites_rerun=False,runtime_stage_called=False,Root_issuer_called=False,TP_called=False,Main_written=False,Canon_written=False,Go_Native_SQL_model_called=False,formal_acceptance=False,execution_grant=False,synthetic_values_carry_no_Root_review_or_authority=True))
    basis_ref = save('revision-basis.json',guarded_summary)
    print(json.dumps(dict(basis_ref=basis_ref,controls_ref=controls_ref,guard_ref=close_ref,passed=len(rows),failed=0,Source_author=AUTHOR,actual_stages_called=False),ensure_ascii=False))

if __name__ == '__main__':
    try: main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1'); raise
    print('ROOT_PYTHON_EXIT=0')
