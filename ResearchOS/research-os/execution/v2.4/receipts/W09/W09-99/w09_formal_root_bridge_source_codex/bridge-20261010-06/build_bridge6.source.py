"""Prepare Bridge06 Source only; use local Source fixtures, never real Root stages."""
from pathlib import Path
import ast, copy, difflib, json, types, uuid

R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
OLD = D.parent / 'bridge-20261010-05'
RV = W / 'w09_formal_root_bridge_independent_source_review_codex/review-20261010-05-attach'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
GEN = 'bridge-20261010-06'
before_function = '''def canonical_identity(path):
    """Identify the fixed Canon files without reading their historical live bytes."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value
'''
after_function = '''def canonical_identity(path):
    """Use physical()'s resolved identity; literal refs retain their exact spelling."""
    value = Path(path)
    if not value.is_absolute():
        value = ROOT / value
    return value.resolve(strict=True)
'''
checks = []; built = {}; failure = None
input_guard = s.guard(); delta_guard = s.guard()
source_uuid = uuid.uuid4().hex

def write_raw(name, raw):
    with (D / name).open('xb') as stream:
        stream.write(raw)
    return s.pin(D / name)

def check(name, ok, detail=None):
    checks.append(dict(name=name, passed=bool(ok), detail=detail))
    if not ok:
        raise ValueError(name)

def rejection(name, operation, expected):
    observed = None
    try:
        operation()
    except ValueError as exc:
        observed = str(exc)
    check(name, observed == expected, dict(observed=observed, expected=expected))

# Preserve the real nonterminating PowerShell read error before Source construction.
original = s.capture('ac76e0', 0, None, 1190)
s.write('original1190.origin.json', dict(original_ordinal=1190, original_io=original,
    actual_outer_exit=0, actual_python_exit=None, actual_Native_exit=None, actual_Go_exit=None,
    actual_SQL_exit=None, actual_dispatcher_exit=None, actual_model_exit=None, actual_TP_exit=None,
    cause='Get-Content attempted nonexistent decision.json; actual later commands completed and overall exit was zero.',
    failure_is_nonterminating_read_diagnostic=True, original_failure_retained=True,
    successful_findings_and_BR5_read_prefix_retained=True, automatic_retry=False,
    guards_before_original_error=0, product_calls=0))

try:
    oh = json.loads((OLD / 'HDF.json').read_bytes())
    om = json.loads((OLD / 'MF.json').read_bytes())
    rh = json.loads((RV / 'HDF.json').read_bytes())
    rm = json.loads((RV / 'MF.json').read_bytes())
    refs = [s.pin(__file__), s.pin(HELPER), s.pin(OLD / 'HDF.json'), s.pin(OLD / 'MF.json'),
            *om['members'], s.pin(RV / 'HDF.json'), s.pin(RV / 'MF.json'), *rm['members']]
    refs = list({item['path']: item for item in refs}.values())
    input_guard.acquire(refs)
    before = input_guard.get_buffer(oh['source_ref']['path'])
    # Preserve the original byte-level mixture of CRLF and LF.
    old_generation = b'BRIDGE_GENERATION = "bridge-20261010-05"'
    new_generation = b'BRIDGE_GENERATION = "bridge-20261010-06"'
    check('single_generation_and_function_patch_anchors', before.count(old_generation) == 1
          and before.count(before_function.encode()) == 1)
    revised = before.replace(old_generation, new_generation, 1).replace(
        before_function.encode(), after_function.encode(), 1)
    restored = revised.replace(after_function.encode(), before_function.encode(), 1).replace(
        new_generation, old_generation, 1)
    check('complete_BR5_exact_byte_inverse', restored == before)
    old_tree, new_tree = ast.parse(before), ast.parse(revised)
    old_nodes = {x.name: x for x in old_tree.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
    new_nodes = {x.name: x for x in new_tree.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
    changed = [key for key in old_nodes if ast.dump(old_nodes[key], include_attributes=False)
               != ast.dump(new_nodes[key], include_attributes=False)]
    check('only_canonical_identity_business_function_changed', changed == ['canonical_identity']
          and old_nodes.keys() == new_nodes.keys(), changed)
    old_without_delta = copy.deepcopy(old_tree); new_without_delta = copy.deepcopy(new_tree)
    def remove_delta(tree):
        tree.body = [x for x in tree.body if not (isinstance(x, ast.FunctionDef)
                    and x.name == 'canonical_identity') and not (isinstance(x, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'BRIDGE_GENERATION'
                            for target in x.targets))]
        return ast.dump(tree, include_attributes=False)
    check('entire_other_AST_author_root_roles_modes_archive_Guard_TP_and_physical_unchanged',
          remove_delta(old_without_delta) == remove_delta(new_without_delta))
    built['source_ref'] = write_raw('w09_root_bridge.source.py', revised)
    built['consumer_launcher_ref'] = write_raw('consumer_launch.source.py',
        input_guard.get_buffer(oh['consumer_launcher_ref']['path']))
    check('consumer_launcher_exact_BR5_bytes', built['consumer_launcher_ref']['sha256']
          == oh['consumer_launcher_ref']['sha256'] and built['consumer_launcher_ref']['bytes']
          == oh['consumer_launcher_ref']['bytes'])

    # Only these new local files are used as Canon-shaped fixtures. Real Canon is untouched.
    fixture_root = D / 'alias-fixture'
    fixture_canon_dir = fixture_root / 'execution/v2.4'
    fixture_canon_dir.mkdir(parents=True, exist_ok=False)
    fixture_refs = []
    for name in ('checkpoint', 'path_ownership', 'step_state', 'commands'):
        path = fixture_canon_dir / (name + '.json')
        with path.open('xb') as stream:
            stream.write((json.dumps(dict(Source_fixture_only=True, name=name)) + '\n').encode())
        fixture_refs.append(s.pin(path))
    stable_path = fixture_root / 'stable.json'
    with stable_path.open('xb') as stream:
        stream.write(b'{"Source_fixture_only":true,"stable":true}\n')
    fixture_refs.append(s.pin(stable_path))
    # Archives are distinct physical Source files containing original fixture bytes.
    proposal_home = fixture_root / 'proposal'
    proposal_home.mkdir()
    proposal_path = proposal_home / 'result.json'
    with proposal_path.open('xb') as stream:
        stream.write(b'{"Source_fixture_only":true}\n')
    fixture_refs.append(s.pin(proposal_path))
    archive_refs = []
    for identity in fixture_refs[:4]:
        target = proposal_home / ('canonical-' + Path(identity['path']).stem + '.original.json')
        with target.open('xb') as stream:
            stream.write(Path(identity['path']).read_bytes())
        archive_refs.append(s.pin(target))
    fixture_refs.extend(archive_refs)
    held_delta = [built['source_ref'], built['consumer_launcher_ref'], *fixture_refs]
    delta_guard.acquire(held_delta)
    m = s.inert(D / 'w09_root_bridge.source.py', delta_guard.get_buffer(built['source_ref']['path']))
    m.ROOT = fixture_root; m.CANON = [Path(item['path']) for item in fixture_refs[:4]]
    m.PLAN = fixture_root / 'unused-plan.json'
    req = dict(current4=copy.deepcopy(fixture_refs[:4]))
    aliases = {
        'absolute_dotdot': str(fixture_canon_dir) + r'\..\v2.4\checkpoint.json',
        'repo_posix_dotdot': 'execution/v2.4/../v2.4/checkpoint.json',
        'absolute_dot': str(fixture_canon_dir) + r'\.\checkpoint.json',
        'repo_posix_dot': './execution/v2.4/./checkpoint.json',
        'case_and_separator': str(m.CANON[0]).upper().replace('\\', '/'),
        'mixed_separators': str(fixture_canon_dir).replace('\\', '/') + r'\..\v2.4/checkpoint.json',
    }
    for name, spelling in aliases.items():
        check(name + '_identity_matches_physical_and_fixed_Canon',
              m.canonical_identity(spelling) == m.physical(spelling) == m.CANON[0],
              dict(Source_fixture_only=True, spelling=spelling))
    canonical_alias = dict(req['current4'][0], path=aliases['absolute_dotdot'])
    for field in ('publication_ref', 'role_registry_input_ref'):
        rejection(field + '_undeclared_dotdot_Canon_ref_rejected',
            lambda field=field: m.historical_dependency_refs(dict(extra=canonical_alias), {}, req, field),
            'UNDECLARED_HISTORICAL_CANONICAL_REFERENCE')
    rejection('snapshot_files_dotdot_Canon_key_rejected',
        lambda: m.validate_persistent_snapshot(dict(files={canonical_alias['path']:canonical_alias['sha256']})),
        'HISTORICAL_SNAPSHOT_CONTAINS_CANON')
    rejection('request_extra_alias_same_digest_still_literal_ref_conflict',
        lambda: m.request_dependency_refs(dict(req, extra=canonical_alias)),
        'REQUEST_CANONICAL_AUTHORITY_CONFLICT')
    wrong_alias = dict(canonical_alias, sha256='f' * 64)
    rejection('request_extra_alias_wrong_digest_conflict',
        lambda: m.request_dependency_refs(dict(req, extra=wrong_alias)),
        'REQUEST_CANONICAL_AUTHORITY_CONFLICT')
    rejection('historical_nested_repo_posix_alias_rejected',
        lambda: m.historical_dependency_refs(dict(documents=[dict(extra=dict(canonical_alias,
            path=aliases['repo_posix_dotdot']))]), {}, req, 'publication_ref'),
        'UNDECLARED_HISTORICAL_CANONICAL_REFERENCE')
    stable_ref = fixture_refs[4]
    class LocalReader:
        read_hashes = {Path(canonical_alias['path']): canonical_alias['sha256'],
                      Path(stable_ref['path']): stable_ref['sha256']}
        w09_owned_inventories = []; w09_audit_ranges = []
    class LocalAPI:
        @staticmethod
        def recheck_inputs(data):
            return dict(status='PASS' if all(m.sha(Path(path).read_bytes()) == digest
                        for path, digest in data['files'].items()) else 'INVALID')
    persistent = m.snapshot(LocalAPI(), LocalReader())
    authority = m.snapshot(LocalAPI(), LocalReader(), authority=True)
    check('persistent_snapshot_excludes_Canon_alias_but_keeps_immutable_file',
          persistent['files'] == {stable_ref['path']:stable_ref['sha256']})
    check('authority_snapshot_keeps_current_alias_dependency_for_CAS',
          str(Path(canonical_alias['path'])) in authority['files'])
    source_ref = built['source_ref']
    source_review = dict(path=str(stable_path), sha256=stable_ref['sha256'], bytes=stable_ref['bytes'])
    req.update(bridge_source_ref=source_ref, source_review_ref=source_review)
    proposal = dict(schema='researchos.w09-bridge-proposal.v1', generation=GEN,
        source_ref=source_ref, source_review_ref=source_review, current4=copy.deepcopy(req['current4']),
        historical_current4=dict(schema='researchos.w09-bridge-historical-current4.v1',
            meaning='ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY',
            canonical_refs=copy.deepcopy(req['current4']), archive_refs=archive_refs),
        dependency_snapshot=dict(files={stable_ref['path']:stable_ref['sha256']}))
    got = m.historical_dependency_refs(proposal, s.pin(proposal_path), req, 'proposal_ref')
    check('new_normalizer_preserves_exact_original_four_archive_proof',
          all(item in got for item in archive_refs) and not any(m.canonical_identity(item['path'])
              in m.CANON for item in got))
    polluted = copy.deepcopy(proposal); polluted['extra'] = canonical_alias
    rejection('archive_covered_proposal_cannot_hide_extra_Canon_alias',
        lambda: m.historical_dependency_refs(polluted, s.pin(proposal_path), req, 'proposal_ref'),
        'UNDECLARED_HISTORICAL_CANONICAL_REFERENCE')
    clean_alias = dict(stable_ref, path=str(fixture_root) + r'\execution\..\stable.json')
    check('non_Canon_resolvable_ref_not_misclassified_or_rewritten',
          m.request_dependency_refs(dict(req, extra=clean_alias))[-1] == clean_alias)
    # Snapshot exclusion and current4 conflict behavior are checked above. The untouched
    # Root/current4/TP/Guard functions are bound by complete inverse and complete AST.
    built['inverse_ref'] = s.write('exact-inverse.json', dict(original_ref=oh['source_ref'],
        candidate_ref=built['source_ref'], replacement_blocks=[
            dict(before=old_generation.decode(), after=new_generation.decode()),
            dict(before=before_function, after=after_function)],
        complete_inverse=True, changed_existing_functions=changed, added_functions=[],
        unchanged_all_other_AST=True))
    built['patch_ref'] = write_raw('bridge06.patch', ''.join(difflib.unified_diff(
        before.decode().splitlines(True), revised.decode().splitlines(True),
        fromfile='BR5/w09_root_bridge.source.py', tofile='BR6/w09_root_bridge.source.py')).encode())
    built['inputs_ref'] = s.write('source-inputs.json', dict(base_hdf_ref=s.pin(OLD / 'HDF.json'),
        base_mf_ref=s.pin(OLD / 'MF.json'), base_source_ref=oh['source_ref'],
        base_launcher_ref=oh['consumer_launcher_ref'], base_contract_ref=oh['root_calling_contract_ref'],
        independent_request_changes_hdf_ref=s.pin(RV / 'HDF.json'),
        independent_request_changes_mf_ref=s.pin(RV / 'MF.json'),
        independent_request_changes_decision_ref=rh['decision_ref'],
        independent_findings_ref=rh['findings_ref'], original_Attach_contribution=oh['base_source_contribution'],
        held_input_refs=refs, held_delta_refs=held_delta, live_Canon_refs_held=[],
        reused_BR5_controls_ref=oh['delta_controls_ref'], old_36_controls_rerun=False,
        preserved_prior_BR5_original_io=oh['original1185_io'], Source_fixture_root=str(fixture_root)))
except BaseException as exc:
    failure = dict(type=type(exc).__name__, message=str(exc))
    raise
finally:
    built['delta_guard_ref'] = s.write('delta-source-guard.closed.json', delta_guard.close())
    built['source_guard_ref'] = s.write('source-guard.closed.json', input_guard.close())
    s.write('delta-controls.json', dict(schema='researchos.w09-bridge-canonical-alias-source-controls.v1',
        checks=checks, passed=sum(item['passed'] for item in checks), count=len(checks), failure=failure,
        built=built, source_revision_uuid=source_uuid, original1190_io=original,
        all_controls_Source_fixture_only=True, actual_Root_stages=0, actual_Main_calls=0,
        actual_Native_Go_SQL_TP_model_calls=0, live_Canon_reads=0, live_Canon_readlocks=0,
        Root_scope_grant_created=False, formal_acceptance=False, source_self_acceptance=False))
print(json.dumps(dict(Source_built=built, checks=len(checks), passed=sum(item['passed'] for item in checks),
    failure=failure, original1190_io=original, guards_closed=True), ensure_ascii=False))
