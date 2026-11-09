import sys
sys.dont_write_bytecode = True
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

Q = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('finite_read_guard', Q / 'read_inputs.py')
util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)

def main():
    guard = util.Guard()
    closed = False
    try:
        discovered = json.loads((Q / 'input-discovery.json').read_text(encoding='utf-8'))
        for key in ('Main_formal_profile', 'Main_formal_case_index', 'Main_router', 'CM39', 'frozen_plan', 'frozen_acceptance', 'frozen_goal'):
            ref = discovered['current_before'][key]['original_ref']
            guard.read(ref['path'], ref)
        base = (Q / 'inputs/formal_profile_w09.before.py').read_bytes()
        index = (Q / 'inputs/formal_case_index.before.py').read_bytes()
        assert len(index) == 71844 and hashlib.sha256(index[:51719]).hexdigest() == '92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1'
        text = base.decode('utf-8')
        fragment = (Q / 'v5_helpers.pyfrag').read_text(encoding='utf-8')
        patches = [
            ('def _vector(api, reader, context):', fragment.rstrip() + '\n\n\ndef _vector(api, reader, context):'),
            ('tool = _doc(api, reader, tool_ref, SOURCE_PREFIX)', 'tool = _native_tool_doc(api, reader, tool_ref)'),
            ('def _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources):', 'def _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources, role_registry):'),
            ('        api.require(receipt.get("selectors") == {"task_id": "W09", "check_id": check, "case_id": case}', '        historical = _historical_registry(api, reader, row, receipt, registry, pinned.get(registry_path))\n        api.require(receipt.get("selectors") == {"task_id": "W09", "check_id": check, "case_id": case}'),
            ('and receipt.get("registered_command_revision") == pinned.get(registry_path)', 'and (historical or receipt.get("registered_command_revision") == pinned.get(registry_path))'),
            ('            api.require(pinned.get(reader.ref(ref)) == ref["sha256"], "DISPATCH_INPUT_UNPINNED", ident)', '            _dispatcher_input(api, reader, ref, pinned, historical, ident)'),
            ('                                                       producer_sources)\n        source_pins =', '                                                       producer_sources)\n        actual_mode = _doc(api, reader, row["mode_decision_ref"], SOURCE_PREFIX)\n        _route_execution_actor(api, reader, row, receipt, actual_mode, role_registry)\n        source_pins ='),
            ('def _independent(api, reader, owner, roots, context, outputs, global_rows):', 'def _independent(api, reader, owner, roots, context, outputs, global_rows, role_registry):'),
            ('    executor, reviewer = context["executor_id"], api.text(review.get("reviewer_id"), "reviewer")\n    api.require(len({executor.casefold(), reviewer.casefold(), "codex:/root"}) == 3\n                and review.get("executor_id") == executor\n                and issuance.get("actor") == "codex:/root"\n                and issuance.get("executor_id") == executor\n                and issuance.get("reviewer_id") == reviewer,\n                "INDEPENDENT_ACTOR", "W09")', '    reviewer = _independent_roles(api, role_registry, context, review, issuance, owner)'),
            ('    pinned = _vector(api, reader, context)\n    plan =', '    pinned = _vector(api, reader, context)\n    reader.w09_audit_ranges = []\n    role_registry = _role_registry(api, reader, context)\n    role_ref = context["role_policy"]["registry_ref"]\n    role_path = reader.ref({name: role_ref[name] for name in ("path", "sha256")}, ROOT_CAPTURE_PREFIX)\n    api.require(pinned.get(role_path) == role_ref["sha256"], "ROLE_POLICY_UNPINNED", "current input vector")\n    plan ='),
            ('    reader.w09_audit_ranges = []\n    outputs, facts = _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources)', '    outputs, facts = _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources, role_registry)'),
            ('    _independent(api, reader, owner, roots, context, outputs, global_rows)', '    _independent(api, reader, owner, roots, context, outputs, global_rows, role_registry)'),
        ]
        actual_patches = []
        for before, after in patches:
            normalized = text.replace('\r\n', '\n')
            assert normalized.count(before) == 1, 'exact replacement cardinality: ' + before[:90]
            start = normalized.index(before)
            positions = [0]
            i = 0
            while i < len(text):
                i += 2 if text[i:i+2] == '\r\n' else 1
                positions.append(i)
            lo, hi = positions[start], positions[start + len(before)]
            original_span = text[lo:hi]
            ending = '\r\n' if '\r\n' in original_span else '\n'
            revised_span = after.replace('\n', ending)
            actual_patches.append((original_span, revised_span))
            text = text[:lo] + revised_span + text[hi:]
        candidate = text.encode('utf-8')
        inverse = text
        for before, after in reversed(actual_patches):
            assert inverse.count(after) == 1
            inverse = inverse.replace(after, before, 1)
        assert inverse.encode('utf-8') == base
        original_ast, revised_ast = ast.parse(base.decode('utf-8')), ast.parse(text)
        ast.parse(index.decode('utf-8'))
        changed = {'_native', '_dispatches', '_independent', 'verify_owner'}
        nodes = lambda tree: {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, ast.FunctionDef)}
        old, new = nodes(original_ast), nodes(revised_ast)
        unchanged = sorted(set(old) - changed)
        assert all(old[name] == new[name] for name in unchanged)
        namespace = {'__name__': 'source_only_v5', '__file__': str(Q / 'candidate-root/execution/v2.4/formal_profile_w09.py')}
        exec(compile(revised_ast, namespace['__file__'], 'exec'), namespace)
        archive = json.loads((Q / 'inputs/commands.CM39.before.json').read_text(encoding='utf-8'))
        proposed = json.loads(json.dumps(archive))
        proposed.update(revision=40, updated_by='codex:/root', updated_at='PENDING_ROOT_ACTUAL_ISSUANCE', revision_note='SOURCE_PROPOSAL_ONLY: W09-G01/W09-G02 and two A06 router bindings; Root adoption pending')
        proposed['commands'] = namespace['_cm40_commands'](archive)
        assert len(proposed['commands']) == len(archive['commands'])
        unchanged_commands = sorted(k for k in archive['commands'] if k not in {'test.retrieval', 'test.security'})
        assert all(proposed['commands'][k] == archive['commands'][k] for k in unchanged_commands)
        registry_raw = (json.dumps(proposed, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        members = [util.save('candidate-root/execution/v2.4/formal_profile_w09.py', candidate), util.save('candidate-root/execution/v2.4/commands.json', registry_raw), util.save('formal_profile_w09.after.py', candidate), util.save('formal_case_index.before.py', index), util.save('formal_case_index.after.py', index), util.save('commands.after.json', registry_raw), util.save('source_controls_v4.py', (Q / 'inputs/source_controls_v4.py').read_bytes())]
        diff = ''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True), candidate.decode('utf-8').splitlines(True), fromfile='Main/execution/v2.4/formal_profile_w09.py', tofile='SOURCE_PROPOSAL/execution/v2.4/formal_profile_w09.py'))
        registry_diff = ''.join(difflib.unified_diff((Q / 'inputs/commands.CM39.before.json').read_text(encoding='utf-8').splitlines(True), registry_raw.decode('utf-8').splitlines(True), fromfile='Main/CM39/commands.json', tofile='SOURCE_PROPOSAL/CM40/commands.json'))
        util.save('profile.diff', diff.encode('utf-8'))
        util.save('commands.diff', registry_diff.encode('utf-8'))
        util.savejson('exact-inverse.json', {'schema': 'researchos.w09-source-exact-inverse.v1', 'base_ref': discovered['current_before']['Main_formal_profile']['original_ref'], 'candidate_ref': members[0], 'patches': [{'before':a,'after':b} for a,b in actual_patches], 'inverse_to_original_bytes': True, 'index_byte_delta': 0, 'w07_prefix_bytes': 51719, 'w07_prefix_sha256': hashlib.sha256(index[:51719]).hexdigest()})
        report = {'schema':'researchos.w09-v5-source-static.v1', 'authority':'NONE', 'execution':'PYTHON_SOURCE_ONLY_NO_NATIVE', 'original_functions':len(old),'added_functions':sorted(set(new)-set(old)), 'changed_original_functions':sorted(changed), 'unchanged_original_functions':unchanged, 'unchanged_function_ASTs':True, 'base_line_endings':{'CRLF':base.count(b'\r\n'),'bare_LF':base.count(b'\n')-base.count(b'\r\n')}, 'index_before_after_bytes_equal':True, 'W04_W07_index_rules_unchanged':True, 'outer_schemas_unchanged':namespace['SCHEMAS'], 'formal_routes_unchanged':namespace['ROUTES'], 'formal_assertion_ids_unchanged':namespace['IDS'], 'CM39_revision':39, 'CM40_proposal_revision':40, 'unchanged_commands':unchanged_commands, 'command_count_before':len(archive['commands']), 'command_count_after':len(proposed['commands']), 'root_current_main_writes':0, 'canonical_writes':0, 'Go_Native_dispatcher_model_SQLite_executions':0, 'members':members}
        util.savejson('static-verification.json', report)
        guard_result=guard.close();closed=True
        guard_ref=util.savejson('construction-source-guard.closed.json', guard_result)
        print(json.dumps({'candidate_members':members,'guard_ref':guard_ref,'unchanged_functions':len(unchanged),'added_functions':len(set(new)-set(old)), 'CM40_proposal':'NOT_ADOPTED'},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:
                stream.close()

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:
        traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code))
    raise SystemExit(code)
