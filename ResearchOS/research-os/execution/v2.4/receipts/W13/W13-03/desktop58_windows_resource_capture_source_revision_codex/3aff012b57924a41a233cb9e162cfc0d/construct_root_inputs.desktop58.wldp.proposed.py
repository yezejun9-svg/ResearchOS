"""Root-only, pure-I/O Desktop58 input constructor. Source preparation; do not run yet.

The caller must supply literal future values in root-construction.parameters.desktop58.json.
This file never invokes a builder, target, provider, network client, or canonical writer.
"""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = Path(__file__).resolve().parent
READS = {}
CANON = ['execution/v2.4/' + name + '.json' for name in
         ('checkpoint', 'path_ownership', 'step_state', 'commands')]
PHASES = ('admission.runtime', 'grant-final.runtime', 'grant-final.runtime.after')
VALUE_KEYS = ('source_catalog_ref', 'resource_catalog_ref',
              'current58_CLI2_qualification_ref', 'current58_CLI2_review_ref',
              'current58_CLI2_manifest_ref', 'Root_forward_head_seal_ref',
              'Root_forward_head_review_ref', 'negative_alias_declarations',
              'inner_seconds', 'outer_seconds', 'builder_seconds',
              'controller_evidence_reserve_seconds', 'launcher_evidence_reserve_seconds',
              'expected_runtime_observation_paths', 'runtime_observation_phases')
CODE_KEYS = ('controller_ref', 'launcher_ref', 'authorization_verifier_ref',
             'owned_helper_ref', 'debug_helper_ref', 'utility_ref')


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def parse(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'Duplicate JSON key')
            out[key] = value
        return out
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def safe(value, exists=True, repository=False):
    p = Path(value)
    need(p.is_absolute() and '..' not in p.parts, 'Absolute path required')
    if repository:
        need(p.is_relative_to(ROOT) and p != ROOT, 'Repository boundary')
    if exists:
        need(p.is_file(), 'Missing regular file: ' + str(p))
        resolved = p.resolve(strict=True)
    else:
        need(not os.path.lexists(p), 'Future path already exists: ' + str(p))
        resolved = p.absolute()
    need(resolved == p, 'Alias or noncanonical path: ' + str(p))
    guard_components(p)
    return p


def guard_components(p):
    for cursor in (p, *p.parents):
        if os.path.lexists(cursor):
            attributes = getattr(cursor.lstat(), 'st_file_attributes', 0)
            need(not cursor.is_symlink() and not (attributes & 0x400),
                 'Reparse component: ' + str(cursor))


def frozen(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'} and
         type(ref['bytes']) is int and ref['bytes'] >= 0, 'Exact frozen ref')
    p = safe(ref['path'])
    raw = p.read_bytes()
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
         'Frozen ref mismatch: ' + str(p))
    key = str(p)
    if key in READS:
        need(READS[key] == (len(raw), ref['sha256']), 'Immutable drift')
    READS[key] = (len(raw), ref['sha256'])
    return raw


def actual(ref):
    """Hash a potentially large file, returning a canonical three-key row."""
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'} and
         type(ref['bytes']) is int and ref['bytes'] >= 0, 'Exact resource row')
    p = Path(ref['path'])
    need(p.is_absolute() and '..' not in p.parts and p.is_file(), 'Resource file')
    guard_components(p)
    canonical = p.resolve(strict=True)
    safe(canonical)
    digest = hashlib.sha256()
    size = 0
    with canonical.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(chunk)
            digest.update(chunk)
    need(size == ref['bytes'] and digest.hexdigest() == ref['sha256'],
         'Actual resource mismatch: ' + str(p))
    return {'path': str(canonical), 'sha256': ref['sha256'], 'bytes': size}


def pin(p):
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    target = BASE / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with target.open('xb') as stream:
        stream.write(raw)
    return pin(target)


def add(rows, row):
    normalized = actual(row)
    key = os.path.normcase(normalized['path'])
    need(key not in rows or rows[key] == normalized,
         'Conflicting resource identity: ' + normalized['path'])
    rows[key] = normalized
    return normalized


def physical_members(root, expected):
    """Check exact recursive membership; never traverse a junction or symlink."""
    root = Path(root)
    need(root.is_dir(), 'Physical root')
    guard_components(root)
    root = root.resolve(strict=True)
    wanted = {os.path.normcase(str(Path(ref['path']).resolve(strict=True))) for ref in expected}
    need(len(wanted) == len(expected), 'Duplicate expected physical member')
    found = set()
    def abort_walk(error):
        raise error
    for directory, dirs, files in os.walk(root, topdown=True, onerror=abort_walk, followlinks=False):
        folder = Path(directory)
        need(folder.resolve(strict=True) == folder, 'Directory alias')
        for name in dirs:
            candidate = folder / name
            need(not candidate.is_symlink() and
                 not (getattr(candidate.lstat(), 'st_file_attributes', 0) & 0x400),
                 'Reparse directory')
        for name in files:
            candidate = folder / name
            need(candidate.is_file() and not candidate.is_symlink() and
                 not (getattr(candidate.lstat(), 'st_file_attributes', 0) & 0x400),
                 'Nonregular physical member')
            found.add(os.path.normcase(str(candidate.resolve(strict=True))))
    need(found == wanted,
         'Physical membership differs at ' + str(root) +
         ': missing=' + str(len(wanted - found)) + ', extra=' + str(len(found - wanted)))
    return {'root': str(root), 'member_count': len(found),
            'matched_expected_count': len(wanted), 'extra': 0, 'missing': 0}


def root_file_rows(full, root):
    root = Path(root)
    return [row for row in full if Path(row['path']).is_relative_to(root)]


def run():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,
         'Pinned -I -S -X utf8 required')
    q = parse((BASE / 'root-construction.parameters.desktop58.json').read_bytes())
    need(q['schema'] == 'researchos.desktop58-root-input-construction-request.v1' and
         q['actor'] == 'codex:/root' and q['source_acceptance'] is False and
         q['compile_or_case_execution_authorized'] is False and q['formal_increment'] == 0,
         'Root source-only request')
    future = ('before', 'after', 'canonical_copies', 'pending_origin_refs',
              'source_commit', 'main_git', 'public_environment', 'allocation',
              'controller_review_path', 'source_catalog_ref', 'current58_authority_ref',
              'metadata_code_refs', 'static_image_refs', 'toolchain_lock_ref',
              'current58_CLI2_qualification_ref', 'current58_CLI2_review_ref',
              'current58_CLI2_manifest_ref', 'Root_forward_head_seal_ref',
              'Root_forward_head_review_ref', 'negative_alias_declarations',
              'inner_seconds', 'outer_seconds', 'builder_seconds',
              'controller_evidence_reserve_seconds', 'launcher_evidence_reserve_seconds',
              'wldp_static_ref', 'wldp_candidate_report_ref')
    need(all(q.get(key) is not None for key in future), 'Root literal future value missing')
    need(len(q['canonical_copies']) == 4 and type(q['pending_origin_refs']) is list,
         'Four copies and explicit pending origin cut')
    need(q['after'] == [q['before'][0] + 1, q['before'][1] + 1,
                        q['before'][2] + len(q['pending_origin_refs'])],
         'Explicit origin cut')
    copies = [frozen(ref) for ref in q['canonical_copies']]
    need(all((ROOT / name).read_bytes() == raw for name, raw in zip(CANON, copies)),
         'Live four changed')
    cp, ow = map(parse, copies[:2])
    need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == q['before'] and
         cp['head'] == q['source_commit'], 'Current Root tuple/head')
    prefix = parse(frozen(q['failure_prefix430_ref']))['failure_counters']
    need(len(prefix) == 430 and cp['failure_counters'][:430] == prefix,
         'Original 430 and full prior failure prefix')
    origins = []
    prior = {x.get('evidence_ref', {}).get('sha256') for x in cp['failure_counters']}
    for ref in q['pending_origin_refs']:
        payload = parse(frozen(ref))
        need(ref['sha256'] not in prior, 'Origin already registered or duplicated')
        prior.add(ref['sha256'])
        origins.append({'origin_key': ref['sha256'], 'evidence_ref': ref,
                        'original_payload': payload, 'counter_reset': False,
                        'counted_once': True, 'automatic_retry': False})

    source_catalog = parse(frozen(q['source_catalog_ref']))
    need(source_catalog['commit'] == q['source_commit'] and
         source_catalog['file_count'] == len(source_catalog['files']) == 639,
         'Actual 639 source catalog')
    source = []
    for item in source_catalog['files']:
        ref = {'path': str(ROOT / item['path']), 'sha256': item['sha256'],
               'bytes': item['bytes']}
        raw = frozen(ref)
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
             == item['git_blob'], 'Actual Git blob')
        source.append(ref)
    authority = parse(frozen(q['current58_authority_ref']))
    need(authority['source_commit'] == q['source_commit'] and
         authority['unique_combined_source_paths'] == 58 and
         authority['fresh_compilation_or_cases_accepted'] is False,
         'Current58 source authority only')

    template = parse(frozen(q['scope_template_ref']))
    need(template['preparation_only'] is True and template['execution_authorized'] is False and
         template['source_commit'] == q['source_commit'] and
         'source_catalog_ref' in template and 'catalog_ref' not in template,
         'Desktop source-catalog template ABI')
    for key in CODE_KEYS:
        frozen(template[key])
    frozen(q['builder_source_ref'])
    frozen(q['metadata_pipeline_ref'])
    frozen(q['inventory_review_ref'])
    correction = parse(frozen(q['mandatory_correction_ref']))
    resource_map = parse(frozen(q['resource_map_ref']))
    wldp_report = parse(frozen(q['wldp_candidate_report_ref']))
    need(wldp_report['stage'] == 'SOURCE_RESOURCE_CANDIDATE_ONLY' and
         wldp_report['actual_qualification'] is False and
         wldp_report['native_target_executed'] is False and
         len(wldp_report['candidate_additions']) == 1,
         'Wldp static evidence only, never prior native qualification')
    candidate = wldp_report['candidate_additions'][0]
    wldp_ref = {key: candidate[key] for key in ('path', 'sha256', 'bytes')}
    need(q['wldp_static_ref'] == wldp_ref and
         Path(wldp_ref['path']) == Path('C:/Windows/System32/wldp.dll') and
         candidate['canonical_path'] == wldp_ref['path'],
         'Root explicit canonical Wldp pin')
    pe = parse(frozen(wldp_report['fresh_evidence_refs']['pe_explicit']))
    names = parse(frozen(wldp_report['fresh_evidence_refs']['direct_import_name_matches']))
    need(pe['targets']['wldp']['sha256'] == wldp_ref['sha256'] and
         pe['targets']['wldp']['bytes'] == wldp_ref['bytes'] and
         'wldp.dll' in [name.casefold() for name in pe['targets']['cmd']['pe']['delay_imports']] and
         any(edge['from'] == pe['targets']['cmd']['path'] and
             edge['raw_name'].casefold() == 'wldp.dll' and
             edge['import_kind'] == 'delay_imports' and
             edge['system32_filename_matches'] == [wldp_ref['path']] and
             edge['catalog_matches'] == [] for edge in names['edges']),
         'Direct static PE dependency and old-catalog gap')

    compiler = copy.deepcopy(parse(frozen(q['compiler_base_ref'])))
    runtime = copy.deepcopy(parse(frozen(q['runtime_base_ref'])))
    need(len(compiler['files']) == 22138 and len(runtime['files']) == 1242 and
         len(correction['missing_Windows_refs']) == 40,
         'Actual compiler/runtime/Windows reference membership')
    compiler_rows, runtime_rows, union = {}, {}, {}
    for ref in compiler['files']:
        add(compiler_rows, ref)
    need(len(compiler_rows) == 22138, 'Compiler identity count')
    for group in compiler['complete_public_roots']:
        members = [actual(ref) for ref in group['files']]
        need(all(os.path.normcase(ref['path']) in compiler_rows for ref in members),
             'Compiler root member omitted')
        group['files'] = members
    membership = {'compiler_roots': [physical_members(group['path'], group['files'])
                                    for group in compiler['complete_public_roots']]}
    for ref in runtime['files'] + correction['missing_Windows_refs'] + [wldp_ref]:
        add(runtime_rows, ref)
    need(len(runtime_rows) == 1283, 'Runtime base plus Windows40 plus Wldp identity count')
    need(len(q['metadata_code_refs']) == 8, 'Current Desktop metadata8 only')
    metadata_names = {Path(ref['path']).name for ref in q['metadata_code_refs']}
    need(metadata_names == {'scope_builder.py', 'prepare.py', 'register.py',
                            'run.py', 'seal.py', 'grant_preflight.py',
                            Path(q['builder_source_ref']['path']).name,
                            Path(q['metadata_pipeline_ref']['path']).name} and
         q['builder_source_ref'] in q['metadata_code_refs'] and
         q['metadata_pipeline_ref'] in q['metadata_code_refs'],
         'Exact current Desktop metadata wrappers, builder and pipeline')
    for ref in q['metadata_code_refs']:
        add(runtime_rows, ref)
    for key in CODE_KEYS:
        add(runtime_rows, template[key])
    runtime['files'] = sorted(runtime_rows.values(), key=lambda row: os.path.normcase(row['path']))
    runtime['desktop58_overlay'] = {
        'base_ref': q['runtime_base_ref'],
        'Windows40_correction_ref': q['mandatory_correction_ref'],
        'Windows_Wldp_static_ref': actual(wldp_ref),
        'Windows_Wldp_static_evidence_ref': q['wldp_candidate_report_ref'],
        'Windows_Wldp_actual_loaded_proven': False,
        'metadata8_refs': [actual(ref) for ref in q['metadata_code_refs']],
        'six_runtime_controller_refs': [actual(template[key]) for key in CODE_KEYS],
        'old_CLI_metadata8_inherited': False,
        'actual_case_acceptance': False}
    compiler['files'] = sorted(compiler_rows.values(),
                               key=lambda row: os.path.normcase(row['path']))
    for group in compiler['complete_public_roots']:
        group['path'] = str(Path(group['path']).resolve(strict=True))
    compiler['compiler_images'] = [actual(ref) for ref in compiler['compiler_images']]
    compiler['explicit_metadata_files'] = [actual(ref) for ref in compiler['explicit_metadata_files']]
    for row in compiler['files'] + runtime['files']:
        add(union, row)

    full = parse(frozen(q['full_finite_inputs_ref']))
    need(type(full) is list and len(full) == 8577, 'Old full input provenance 8577')
    roots = resource_map['resource_roots']
    electron_root = str(Path(roots['electron_dist']['root']).resolve(strict=True))
    web_root = str(Path(roots['web_modules']['root']).resolve(strict=True))
    electron = root_file_rows(full, electron_root)
    web = root_file_rows(full, web_root)
    need(len(electron) == 75 and len(web) == 356,
         'Original Electron75/web356 provenance membership')
    membership['electron_dist'] = physical_members(electron_root, electron)
    membership['web_modules'] = physical_members(web_root, web)
    for row in electron + web:
        add(union, row)
    need(all(os.path.normcase(actual(ref)['path']) in union
             for ref in correction['web_native_addons']),
         'Rolldown/lightningcss native addons required')
    tools_from_map = {item['name']: item['current_actual_ref']
                      for item in resource_map['tools']}
    need('node' in tools_from_map and
         all(os.path.normcase(row['path']) !=
             os.path.normcase(tools_from_map['node']['path']) for row in full),
         'Node.exe is separate current tool provenance, not old 8577')
    add(union, tools_from_map['node'])
    lock = parse(frozen(q['toolchain_lock_ref']))
    tools = {}
    for name in ('python', 'go', 'node'):
        need(name in tools_from_map, 'Current tool provenance missing: ' + name)
        row = lock['tools'][name]
        selected = add(union, tools_from_map[name])
        need(row['sha256'] == selected['sha256'] and
             Path(row['path']).resolve(strict=True) == Path(selected['path']),
             'Locked tool identity/SHA differs: ' + name)
        tools[name] = selected
    git_lock = lock['tools']['git']
    git_path = git_lock['path']
    git_resolved = Path(git_path).resolve(strict=True)
    git_key = os.path.normcase(str(git_resolved))
    need(git_key in union and union[git_key]['sha256'] == git_lock['sha256'],
         'Locked Git must have an actual compiler/runtime three-key row')
    tools['git'] = union[git_key]
    need('electron' in tools_from_map, 'Current Electron tool provenance')
    tools['electron'] = add(union, tools_from_map['electron'])
    need(tools['python']['path'] == str(Path(sys.executable).resolve(strict=True)),
         'Actual pinned Python tool identity')
    images = []
    need(0 < len(q['static_image_refs']) <= 60, 'Root explicit static image set <=60')
    for ref in q['static_image_refs']:
        image = add(union, ref)
        need(Path(image['path']).suffix.lower() == '.exe' and image not in images,
             'Unique actual executable image')
        images.append(image)
    need(all(tool in images for tool in tools.values()) and
         all(image in images for image in compiler['compiler_images']),
         'Five tools and compiler images in static executable set')
    for name in ('GOMODCACHE', 'web_modules'):
        root = compiler[name] if name == 'GOMODCACHE' else web_root
        need(Path(root).is_dir(), 'Required physical public root')
        guard_components(Path(root))
    compiler['GOMODCACHE'] = str(Path(compiler['GOMODCACHE']).resolve(strict=True))

    # Everything above must complete before this source-only producer publishes a
    # complete flag. The runtime observation itself remains for the later runner.
    cut_ref = save('failure-origins.cut.json', {
        'schema': 'researchos.root-failure-origin-cut.v1', 'owner': 'codex:/root',
        'before': q['before'], 'after': q['after'], 'origins': origins,
        'counter_reset': False})
    canonical_ref = save('canonical-before.constructed.json', {
        'entries': [{'canonical_path': name, 'ref': ref}
                    for name, ref in zip(CANON, q['canonical_copies'])]})
    source_ref = save('source-inputs.json', {
        'schema': 'researchos.current58-actual-public-source-inputs.v1',
        'source_commit': q['source_commit'], 'catalog_ref': q['source_catalog_ref'],
        'files': source, 'count': len(source), 'actual_compile_graph': None,
        'source_acceptance': False, 'formal_increment': 0})
    compiler_ref = save('compiler-resources.desktop58.json', compiler)
    runtime_ref = save('runtime-resources.desktop58.json', runtime)
    membership_ref = save('root-membership.actual.json', {
        'schema': 'researchos.desktop58-root-membership-actual.v1',
        'provenance': {'resource_map_ref': q['resource_map_ref'],
                       'full_finite_inputs_ref': q['full_finite_inputs_ref'],
                       'inventory_review_ref': q['inventory_review_ref'],
                       'mandatory_correction_ref': q['mandatory_correction_ref']},
        'membership': membership, 'all_actual_file_hashes_verified': True,
        'compiler_file_count': len(compiler['files']),
        'runtime_file_count': len(runtime['files']),
        'electron_file_count': len(electron), 'web_file_count': len(web)})
    catalog_ref = save('resource-catalog.desktop58.json', {
        'schema': 'researchos.desktop58-actual-resource-catalog.v1',
        'source_commit': q['source_commit'],
        'files': sorted(union.values(), key=lambda row: os.path.normcase(row['path'])),
        'images': images, 'tools': tools,
        'GOMODCACHE': compiler['GOMODCACHE'], 'web_modules': web_root,
        'runtime_resources_ref': runtime_ref, 'compiler_resources_ref': compiler_ref,
        'root_membership_ref': membership_ref,
        'complete_public_roots_frozen': True,
        'actual_runtime_closure_verified': False,
        'preparation_only': True, 'execution_authorized': False,
        'source_acceptance': False, 'formal_increment': 0})
    staged = copy.deepcopy(template)
    staged['source_catalog_ref'] = q['source_catalog_ref']
    staged['resource_catalog_ref'] = catalog_ref
    staged['not_run_reason'] = 'Root review, registration/CAS, grant and Desktop cases remain pending.'
    template_ref = save('scope.desktop58.actual-resources.template.json', staged)
    allocation = q['allocation']
    need(type(allocation) is dict and all(allocation.get(key) is not None for key in
         ('run_uuid', 'new_output_root', 'new_wrapper_root', 'new_export_root',
          'new_authorization_root', 'new_grant_preflight_root', 'registration_namespace')),
         'Root literal allocation')
    for name in ('new_output_root', 'new_wrapper_root', 'new_export_root',
                 'new_authorization_root', 'new_grant_preflight_root'):
        safe(allocation[name], exists=False)
    observation = [str(Path(allocation['new_authorization_root']) / (phase + '.json'))
                   for phase in PHASES]
    values = {key: q[key] for key in VALUE_KEYS if key not in
              ('source_catalog_ref', 'resource_catalog_ref',
               'expected_runtime_observation_paths', 'runtime_observation_phases')}
    values.update(source_catalog_ref=q['source_catalog_ref'], resource_catalog_ref=catalog_ref,
                  expected_runtime_observation_paths=observation,
                  runtime_observation_phases=[{'stage': phase, 'path': path}
                                              for phase, path in zip(PHASES, observation)])
    need(set(values) == set(VALUE_KEYS) and all(value is not None for value in values.values()),
         'Exact Desktop scope values ABI')
    values_ref = save('desktop-values.json', values)
    # The metadata pipeline's pin(output/name) returns Root-relative paths.
    # Keep absolute refs in runtime resources, but bind Root-relative refs here.
    metadata_entries = []
    for ref in q['metadata_code_refs']:
        row = actual(ref)
        need(Path(row['path']).is_relative_to(ROOT), 'Metadata source boundary')
        metadata_entries.append(dict(row, path=Path(row['path']).relative_to(ROOT).as_posix()))
    metadata_ref = save('metadata-code-refs.constructed.json',
                        {'entries': metadata_entries})
    inputs = {'owner': 'codex:/root', 'run_uuid': allocation['run_uuid'],
              'before': q['before'], 'after': q['after'], 'main_git': q['main_git'],
              'public_environment': q['public_environment'],
              'registration_namespace': allocation['registration_namespace'],
              'controller_review_path': q['controller_review_path'],
              'controller_review_ref': None, 'scope_template_ref': template_ref,
              'runtime_resources_ref': runtime_ref, 'compiler_resources_ref': compiler_ref,
              'current43_authority_ref': q['current58_authority_ref'],
              'origin_cut_ref': cut_ref, 'canonical_before_ref': canonical_ref,
              'source_inputs_ref': source_ref, 'metadata_code_refs_ref': metadata_ref,
              'failure_prefix430_ref': q['failure_prefix430_ref'],
              'desktop_values_ref': values_ref,
              'toolchain_lock_ref': q['toolchain_lock_ref'],
              'formal_increment': 0, 'scope_binding_or_candidate_executed': False,
              'actual_case_acceptance': False}
    inputs.update({key: allocation[key] for key in
                   ('new_output_root', 'new_wrapper_root', 'new_export_root',
                    'new_authorization_root', 'new_grant_preflight_root')})
    need(all((ROOT / name).read_bytes() == raw for name, raw in zip(CANON, copies)),
         'Final live four changed')
    for path, (size, digest) in READS.items():
        p = Path(path)
        need(p.stat().st_size == size and hashlib.sha256(p.read_bytes()).hexdigest() == digest,
             'Final immutable input drift')
    root_ref = save('root-inputs.desktop58.pre-review.json', inputs)
    audit_ref = save('root-construction.audit.json', {
        'actor': 'codex:/root', 'root_inputs_ref': root_ref, 'before': q['before'],
        'after': q['after'], 'new_origins': len(origins),
        'source_files': len(source), 'compiler_files': len(compiler['files']),
        'runtime_files': len(runtime['files']), 'resource_union_files': len(union),
        'root_membership_ref': membership_ref, 'actual_candidate_runs': 0,
        'canonical_writes': 0, 'formal_increment': 0, 'source_acceptance': False,
        'actual_compilation_or_cases': 0, 'created_execution_leaves': 0})
    print(json.dumps({'status': 'DESKTOP58_ROOT_INPUTS_CONSTRUCTED_NO_EXECUTION_AUTHORITY',
                      'root_inputs_ref': root_ref, 'audit_ref': audit_ref,
                      'formal_increment': 0, 'actual_candidate_runs': 0}))


if __name__ == '__main__':
    run()
