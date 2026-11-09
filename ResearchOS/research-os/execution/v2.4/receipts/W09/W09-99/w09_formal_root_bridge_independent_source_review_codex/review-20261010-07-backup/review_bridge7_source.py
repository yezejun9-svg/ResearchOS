"""Non-author finite BR7 Source delta review. No bridge stage is invoked."""
import ast
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-07'
S = ROOT / 'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
REVIEWER = '/root/backup_regression_resources'
REVIEWER_THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUTHOR = '/root/full_w09_source_review'
HDF_REF = {'path': str(SOURCE / 'HDF.json'), 'sha256': '1da577805839fb3f96f20bb5282020d7f909e466278aa1df3713f758d977d06c', 'bytes': 13966}
MF_REF = {'path': str(SOURCE / 'MF.json'), 'sha256': '8a61ed6cd3d846201fa832e305cb0d002690605c3ca80c867d113ba6283cefd3', 'bytes': 6388}
AUTHOR_AUDIT = {'path': str(S / 'w09.bridge07-source-author.actual-audit.root.json'), 'sha256': '9ecae0f5038058aafd5d18e85d3acb2c871a9d7802e98e21bbdee1514932a1f7', 'bytes': 1112}
GUARD_REF = {'path': str(GUARD), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
PYTHON_REF = {'path': 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', 'sha256': 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b', 'bytes': 106328}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def reference(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw)}

def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)

def checked(ref):
    raw = Path(ref['path']).read_bytes()
    if digest(raw) != ref['sha256'] or len(raw) != ref['bytes']:
        raise ValueError('fixed input pin mismatch: ' + ref['path'])
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable review member already exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return reference(path)

def find_refs(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256', 'bytes'}:
            yield value
        else:
            for item in value.values():
                yield from find_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from find_refs(item)

def field_values(value, key):
    if isinstance(value, dict):
        for k, item in value.items():
            if k == key:
                yield item
            else:
                yield from field_values(item, key)
    elif isinstance(value, list):
        for item in value:
            yield from field_values(item, key)

def text_blocks(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from text_blocks(item)
    elif isinstance(value, dict) and isinstance(value.get('text'), str):
        yield value['text']

def assignment(tree, name):
    nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(nodes) != 1:
        raise ValueError('assignment cardinality differs: ' + name)
    return nodes[0]

def trusted_values(tree):
    literal_names = {n: ast.literal_eval(assignment(tree, n).value) for n in ['GUARD', 'TP', 'OWNED']}
    result = {}
    for key, value in zip(assignment(tree, 'TRUSTED').value.keys, assignment(tree, 'TRUSTED').value.values):
        if isinstance(key, ast.Name):
            if key.id not in literal_names:
                raise ValueError('unobserved TRUSTED key expression')
            decoded_key = literal_names[key.id]
        else:
            decoded_key = ast.literal_eval(key)
        result[decoded_key] = ast.literal_eval(value)
    return result

def main():
    handoff = decode(checked(HDF_REF))
    manifest = decode(checked(MF_REF))
    author_audit = decode(checked(AUTHOR_AUDIT))
    guard_raw = checked(GUARD_REF)
    refs = [HDF_REF, MF_REF, AUTHOR_AUDIT, author_audit['original_capture_ref'], GUARD_REF, PYTHON_REF]
    refs += manifest['members']
    refs += [handoff[key] for key in ['base_hdf_ref', 'base_mf_ref', 'base_source_ref', 'accepted_BR6_review_hdf_ref', 'accepted_BR6_review_mf_ref', 'accepted_BR6_review_decision_ref', 'Main_root_adoption_closed_ref', 'Main_independent_accepted_review_ref', 'Main_required_ref']]
    base_hdf = decode(checked(handoff['base_hdf_ref']))
    refs += [base_hdf['consumer_launcher_ref'], base_hdf['root_calling_contract_ref']]
    spec = importlib.util.spec_from_file_location('br7_independent_source_guard', GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    unique = {}
    for ref in refs:
        key = module._canonical(ref['path'])
        if key in unique and unique[key] != ref:
            if unique[key]['sha256'] != ref['sha256'] or unique[key]['bytes'] != ref['bytes']:
                raise ValueError('conflicting physical Source pins')
        unique[key] = ref
    refs = list(unique.values())
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    controls = []
    closure = None
    facts = {}
    try:
        guard.acquire(refs)
        get = lambda ref: guard.get_buffer(ref['path'])
        old = get(handoff['base_source_ref'])
        new = get(handoff['source_ref'])
        old_tree, new_tree = ast.parse(old.decode('utf-8')), ast.parse(new.decode('utf-8'))
        old_gen = ast.literal_eval(assignment(old_tree, 'BRIDGE_GENERATION').value)
        new_gen = ast.literal_eval(assignment(new_tree, 'BRIDGE_GENERATION').value)
        old_trusted, new_trusted = trusted_values(old_tree), trusted_values(new_tree)
        profile_key = 'execution/v2.4/formal_profile_w09.py'
        if old_gen != 'bridge-20261010-06' or new_gen != 'bridge-20261010-07':
            raise ValueError('actual new generation differs')
        restored = new.replace(b'BRIDGE_GENERATION = "bridge-20261010-07"', b'BRIDGE_GENERATION = "bridge-20261010-06"', 1)
        new_pin = ('("' + new_trusted[profile_key][0] + '", ' + str(new_trusted[profile_key][1]) + ')').encode('ascii')
        old_pin = ('("' + old_trusted[profile_key][0] + '", ' + str(old_trusted[profile_key][1]) + ')').encode('ascii')
        if new.count(new_pin) != 1:
            raise ValueError('Main pin span is not unique')
        restored = restored.replace(new_pin, old_pin, 1)
        if restored != old:
            raise ValueError('full Source inverse differs')
        normalized = copy.deepcopy(new_tree)
        assignment(normalized, 'BRIDGE_GENERATION').value = copy.deepcopy(assignment(old_tree, 'BRIDGE_GENERATION').value)
        assignment(normalized, 'TRUSTED').value = copy.deepcopy(assignment(old_tree, 'TRUSTED').value)
        if ast.dump(normalized, include_attributes=False) != ast.dump(old_tree, include_attributes=False):
            raise ValueError('Source delta exceeds two assignments')
        expected_trusted = dict(old_trusted, **{profile_key: new_trusted[profile_key]})
        if expected_trusted != new_trusted:
            raise ValueError('other TRUSTED bindings changed')
        compile(new.decode('utf-8'), handoff['source_ref']['path'], 'exec')
        controls.append({'id': 'EXACT_TWO_BINDING_INVERSE_AND_ALL_BUSINESS_AST_IDENTITY', 'passed': True, 'restored_sha256': digest(restored)})

        source_module = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'module')
        pin_need = source_module.body[2].value
        pin_expr = ast.Expression(copy.deepcopy(pin_need.args[0]))
        pin_code = compile(ast.fix_missing_locations(pin_expr), '<Source-only trusted pin predicate>', 'eval')
        predicate = lambda pin: eval(pin_code, {'__builtins__': {}}, {'ref': {'sha256': pin[0], 'bytes': pin[1]}, 'TRUSTED': new_trusted, 'relative': profile_key})
        if not predicate(new_trusted[profile_key]) or predicate(old_trusted[profile_key]) or predicate((new_trusted[profile_key][0], old_trusted[profile_key][1])):
            raise ValueError('actual trusted predicate accepts stale Main')
        adoption = decode(get(handoff['Main_root_adoption_closed_ref']))
        current_main = get(handoff['Main_required_ref'])
        if (digest(current_main), len(current_main)) != new_trusted[profile_key] or adoption['target_after_ref'] != handoff['Main_required_ref'] or adoption['Main_integrated'] is not True:
            raise ValueError('new TRUSTED Main lacks actual adopted binding')
        controls.append({'id': 'ACTUAL_NEW_MAIN_PIN_ACCEPT_OLD_SHA_OR_BYTES_REJECT', 'passed': True, 'synthetic_predicate_only': True})

        proposal_function = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'proposal_archive_refs')
        proposal_need = next(n.value for n in proposal_function.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'need')
        code = compile(ast.fix_missing_locations(ast.Expression(copy.deepcopy(proposal_need.args[0]))), '<Source-only proposal identity predicate>', 'eval')
        req = {'bridge_source_ref': handoff['source_ref'], 'source_review_ref': {'synthetic': 'SOURCE_CONTROL_NOT_A_ROOT_WITNESS'}}
        proposal = {'schema': 'researchos.w09-bridge-proposal.v1', 'generation': new_gen, 'source_ref': req['bridge_source_ref'], 'source_review_ref': req['source_review_ref']}
        pred = lambda p: eval(code, {'__builtins__': {}}, {'proposal': p, 'req': req, 'BRIDGE_GENERATION': new_gen})
        if not pred(proposal) or pred(dict(proposal, generation=old_gen)) or pred(dict(proposal, source_ref=handoff['base_source_ref'])):
            raise ValueError('proposal generation/source predicate weakened')
        controls.append({'id': 'NEW_GENERATION_ACCEPT_OLD_GENERATION_OR_SOURCE_REJECT', 'passed': True, 'synthetic_predicate_only': True})

        if get(handoff['consumer_launcher_ref']) != get(base_hdf['consumer_launcher_ref']):
            raise ValueError('launcher is not byte identical')
        source_review_fn = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_review')
        old_source_review = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_review')
        if ast.dump(source_review_fn, include_attributes=False) != ast.dump(old_source_review, include_attributes=False):
            raise ValueError('Source review interface changed')
        if REVIEWER in {AUTHOR, 'codex:' + AUTHOR, 'codex:/root', '/root'}:
            raise ValueError('reviewer is author or executor')
        controls.append({'id': 'LAUNCHER_BYTE_IDENTITY_AND_STRICT_REVIEW_BINDING_INTERFACE', 'passed': True, 'source_review_lines': [source_review_fn.lineno, source_review_fn.end_lineno], 'required_fields': ['reviewer_id', 'source_ref', 'consumer_launcher_ref', 'source_hdf_ref', 'source_mf_ref']})

        raw = get(author_audit['original_capture_ref'])
        lines = raw.splitlines(keepends=True)
        if len(lines) != 3 or any(not line.endswith(b'\n') for line in lines):
            raise ValueError('actual author capture is not three full LF records')
        if [digest(line) for line in lines] != author_audit['original_line_sha256']:
            raise ValueError('actual author original line SHA differs')
        header, meta, final = [decode(line) for line in lines]
        payload = final['payload']
        if header['type'] != 'session_meta' or header['payload']['id'] != ROOT_THREAD or author_audit['Root_thread_id'] != ROOT_THREAD:
            raise ValueError('actual Root author delivery thread differs')
        if meta['type'] != 'inter_agent_communication_metadata' or final['type'] != 'response_item' or final['ordinal'] != meta['ordinal'] + 1 or final['timestamp'] != meta['timestamp']:
            raise ValueError('actual author adjacency differs')
        if payload['type'] != 'agent_message' or payload['author'] != AUTHOR or payload['recipient'] != '/root' or author_audit['actor_id'] != 'codex:' + AUTHOR:
            raise ValueError('actual author/backend/recipient differs')
        flags = list(field_values(final.get('metadata', {}), 'client_authored')) + list(field_values(payload.get('internal_chat_message_metadata_passthrough', {}), 'client_authored'))
        if not flags or any(flag is not False for flag in flags):
            raise ValueError('actual author message is not backend authored')
        texts = list(text_blocks(payload['content']))
        if len(texts) != 1:
            raise ValueError('actual Final body is not one complete text block')
        body = texts[0]
        envelope = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: ' + AUTHOR + '\nPayload:\n'
        if body.startswith(envelope):
            body = body[len(envelope):]
        delivery = decode(body)
        delivered = list(find_refs(delivery))
        def has_ref(expected):
            return any(module._canonical(item['path']) == module._canonical(expected['path']) and item['sha256'] == expected['sha256'] and item['bytes'] == expected['bytes'] for item in delivered)
        if not all(has_ref(expected) for expected in [HDF_REF, MF_REF, handoff['source_ref']]):
            raise ValueError('actual Source Final does not deliver exact Source refs')
        if author_audit['binding_sha256'] != HDF_REF['sha256']:
            raise ValueError('author Root binding is not exact reviewed HDF')
        controls.append({'id': 'REAL_ROOT_THREE_LF_AUTHOR_FINAL_IDENTITY_AND_TYPED_REFS', 'passed': True, 'meta_ordinal': meta['ordinal'], 'Final_ordinal': final['ordinal'], 'actual_timestamp': final['timestamp'], 'message_id': payload['id']})

        contract = decode(get(handoff['root_calling_contract_ref']))
        old_contract = decode(get(base_hdf['root_calling_contract_ref']))
        for key in ['stages', 'six_routes', 'NF6_C19_policy', 'TEMP_TMP', 'Root_actor', 'Root_thread_id', 'verifier_backend', 'Source_review_binding_fields', 'historical_current4_contract', 'persistent_dependency_snapshots', 'canonical_identity_contract']:
            if contract[key] != old_contract[key]:
                raise ValueError('previous Root contract gate changed: ' + key)
        if contract['generation'] != new_gen or contract['source_ref'] != handoff['source_ref'] or contract['consumer_launcher_ref'] != handoff['consumer_launcher_ref'] or contract['Main_required_ref'] != handoff['Main_required_ref']:
            raise ValueError('new Source calling contract binding differs')
        old_review = decode(get(handoff['accepted_BR6_review_decision_ref']))
        if old_review['decision'] != 'ACCEPTED_SOURCE_ONLY' or old_review['source_ref'] != handoff['base_source_ref'] or old_review['formal_acceptance'] is not False:
            raise ValueError('BR6 accepted lineage differs')
        origin = decode(get(handoff['original1218_origin_ref']))
        if not handoff['original1218_io'] or 1218 not in handoff['new_original_failures']:
            raise ValueError('original1218 lineage removed')
        for key in ['source_guard_ref', 'delta_source_guard_ref', 'seal_source_guard_ref']:
            observation = decode(get(handoff[key]))
            if observation['closed'] is not True or observation['retained_handles_count'] != 0 or observation['errors']:
                raise ValueError('author Source Guard not fully closed')
        controls.append({'id': 'UNCHANGED_DYNAMIC_ROOT_GATES_ACCEPTED_BR6_LINEAGE_AND1218_PRESERVED', 'passed': True, 'prior_controls_replayed': False})
        facts = {'source_ref': handoff['source_ref'], 'consumer_launcher_ref': handoff['consumer_launcher_ref'], 'source_hdf_ref': HDF_REF, 'source_mf_ref': MF_REF, 'root_calling_contract_ref': handoff['root_calling_contract_ref'], 'Main_required_ref': handoff['Main_required_ref'], 'actual_source_author_audit_ref': AUTHOR_AUDIT, 'actual_source_author_raw_ref': author_audit['original_capture_ref'], 'base_accepted_review_ref': handoff['accepted_BR6_review_decision_ref'], 'original1218_refs': {'origin_ref': handoff['original1218_origin_ref'], **handoff['original1218_io']}, 'generation': new_gen, 'inverse_restored_sha256': digest(restored), 'held_input_refs': refs, 'changed_business_functions': [], 'reviewer_id': REVIEWER, 'source_author': AUTHOR, 'Root_executor': '/root'}
    finally:
        closure = guard.close()
        publish('SourceGuard.closed.json', closure)
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('independent Source Guard not fully closed')
    controls.append({'id': 'FINITE_SOURCE_GUARD_FULL_CLOSURE_BEFORE_DECISION', 'passed': True, 'held_count': len(refs), 'closed': True, 'retained_handles_count': 0})
    publish('delta-review-controls.json', {'schema': 'researchos.w09-bridge-nonauthor-delta-controls.v1', 'controls': controls, 'count': len(controls), 'passed': len(controls), 'old_successful_controls_replayed': False, 'all_predicate_mocks': 'SYNTHETIC_SOURCE_ONLY_NO_ROOT_AUTHORITY', 'future_bridge_stages_called': 0})
    publish('review-facts.json', dict(facts, controls_ref=reference(HERE / 'delta-review-controls.json'), source_guard_ref=reference(HERE / 'SourceGuard.closed.json'), reviewer_thread=REVIEWER_THREAD, Root_thread=ROOT_THREAD, created_utc=datetime.now(timezone.utc).isoformat(), execution_grant=False, formal_acceptance=False, Native_Go_SQL_model_TP_Root_stage_calls=0, Main_Canon_Scope_writes=0))
    print(json.dumps({'status': 'INDEPENDENT_BR7_SOURCE_DELTA_CHECKS_PASS_PENDING_SEAL', 'checks': len(controls), 'held_refs': len(refs), 'all_guards_closed': True, 'source_ref': handoff['source_ref'], 'reviewer_id': REVIEWER}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
