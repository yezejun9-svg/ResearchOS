"""Preparation template. Only an explicit future Root request may bind a proposal.
This program never imports the candidate controller, mutates Git/canonical state,
or creates an execution grant. Do not run during author preparation.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import types

ROOT = Path('D:/作品集/ResearchOS/research-os')
N05 = ROOT / 'execution/v2.4/receipts/W05/W05-99'
N13 = ROOT / 'execution/v2.4/receipts/W13/W13-03'
PREP = N13 / 'desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916'
CANON = [ROOT / 'execution/v2.4' / (n + '.json') for n in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
CLI = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
DESKTOP = '06b1fbcb5934cbc70e5d65a46481e60c05c6594b'
ORIGINAL = '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
READS = {}
EXTERNAL = {}
DEADLINE = None
TOTAL = 0


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def parse(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'duplicate JSON key')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def bounded(value, existing=True, external=False):
    p = Path(value)
    p = p if p.is_absolute() else ROOT / p
    require('..' not in p.parts and p.absolute() == p.resolve(strict=existing), 'alias/path boundary')
    require(p.is_relative_to(ROOT) or (external and p in EXTERNAL), 'not approved public input')
    for q in [p, *p.parents]:
        if os.path.lexists(q):
            require(not q.is_symlink() and not (getattr(q.lstat(), 'st_file_attributes', 0) & 0x400), 'reparse ancestor')
    return p


def read(value):
    global TOTAL
    p = bounded(value, external=True)
    require(DEADLINE is not None and time.monotonic() < DEADLINE and p.stat().st_size <= 256 * 1024**2, 'read limits')
    chunks = []
    with p.open('rb') as f:
        while True:
            require(time.monotonic() < DEADLINE, 'read deadline')
            b = f.read(1024**2)
            if not b:
                break
            TOTAL += len(b)
            require(TOTAL <= 32 * 1024**3, '32GiB read cap')
            chunks.append(b)
    raw = b''.join(chunks)
    item = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if p in EXTERNAL:
        require(item['sha256'] == EXTERNAL[p]['sha256'] and item['bytes'] == EXTERNAL[p]['bytes'], 'runtime drift')
    require(p not in READS or READS[p] == item, 'input drift')
    READS[p] = item
    return raw


def ref(value, sha=None):
    p = bounded(value, external=True)
    read(p)
    item = dict(READS[p])
    require(sha is None or item['sha256'] == sha, 'fixed SHA mismatch')
    return item


def verify(item):
    actual = ref(item['path'], item['sha256'])
    require(actual['bytes'] == item['bytes'], 'bytes mismatch')
    return actual


def doc(item):
    verify(item)
    return parse(read(item['path']))


def same(a, b):
    return verify(a) == verify(b)


def seal_members(mref, required=()):
    mf = doc(mref)
    require(mf.get('count', len(mf['entries'])) == len(mf['entries']), 'MF count')
    parent = bounded(mref['path']).parent
    rows = {}
    for item in mf['entries']:
        p = bounded(item['path'])
        require(p.is_relative_to(parent) and p not in rows, 'MF duplicate/escape')
        verify(item)
        rows[p] = item
    for item in required:
        p = bounded(item['path'])
        require(p in rows and same(rows[p], item), 'unsealed required member')
    return rows


def save(out, name, value, raw=False):
    b = value if raw else (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (out / name).open('xb') as f:
        f.write(b)
    return ref(out / name)


def tree(raw):
    out = {}
    for line in raw.split(b'\0'):
        if line:
            hdr, name = line.split(b'\t', 1)
            mode, kind, blob = hdr.decode('ascii').split()
            name = name.decode('utf-8', 'strict')
            require(name not in out, 'duplicate tree path')
            out[name] = {'mode': mode, 'kind': kind, 'blob': blob}
    return out


def job_ok(result):
    require(result and result.get('actual_exit') == 0 and result.get('error') is None and result.get('timed_out') is False, 'owned child failed')
    require(result.get('resumed') is True and result.get('owned_child_pid', 0) > 0 and result.get('creation_time_100ns', 0) > 0, 'child identity')
    cleanup = result.get('job_cleanup', {})
    require(cleanup.get('errors') == [] and cleanup.get('active_processes_last_observed') == 0, 'cleanup not closed')
    require(all(cleanup.get(k) is True for k in ['unnamed_exclusive_job', 'kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed']), 'owned Job flags')


def main():
    global DEADLINE
    DEADLINE = time.monotonic() + 1200
    ap = argparse.ArgumentParser()
    ap.add_argument('--request', required=True)
    ap.add_argument('--request-sha256', required=True)
    args = ap.parse_args()
    out = None
    first = None
    secondary = []
    helper = None
    actual_native = None
    phase = 'REQUEST'
    try:
        require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize, 'Python -I -S -X utf8 required')
        require(Path.cwd().resolve() == ROOT, 'explicit repository cwd')
        request_ref = ref(args.request, args.request_sha256)
        request = doc(request_ref)
        require(request['schema'] == 'researchos.desktop15-root-binding-parameters.v1' and request['actor'] == 'codex:/root', 'actual Root parameters')
        require(request['action'] == 'PREPARE_BOUND_PROPOSAL_ONLY' and request['authorized'] is False and request['future_root_grant'] is None, 'no preparation grant')
        before, after = request['expected_before'], request['expected_after']
        require(type(before) is list and type(after) is list and len(before) == len(after) == 3 and all(type(x) is int and x >= 0 for x in before + after), 'explicit full tuples')
        require(after[:2] == [before[0] + 1, before[1] + 1] and after[2] >= before[2], 'exact forward revisions')
        require(request['expected_cli43_head'] == CLI and request['expected_main_branch'].startswith('refs/heads/'), 'explicit fixed43/branch')
        operation = request['operation_uuid']
        require(len(operation) == 32 and all(c in '0123456789abcdef' for c in operation), 'explicit UUID')
        destination = bounded(request['registration_namespace'], False)
        require(destination.parent == N05 / 'integration_codex' and ('r' + str(after[0])) in destination.name and not destination.exists(), 'new Root registration namespace')
        execution = N13 / 'desktop_exact15_integration_executor_codex' / operation
        bounded(execution, False)
        bounded(execution.with_name(operation + '-outer'), False)
        require(not execution.exists() and not execution.with_name(operation + '-outer').exists(), 'unused once operation')
        output = bounded(request['binding_output_root'], False)
        require(output.parent == N13 / 'desktop15_root_scope_binding_executor_codex' and output.name == operation and not output.exists(), 'exclusive preparation leaf')
        require(output.parent.is_dir(), 'Root must explicitly create bounded parent first')
        output.mkdir(exist_ok=False)
        out = output
        save(out, 'started.json', {'argv': [sys.executable, *sys.orig_argv[1:]], 'request_ref': request_ref, 'phase': phase, 'authorized': False, 'automatic_retry': False})
        phase = 'FIXED_SOURCE_AND_REVIEWS'
        proposed_ref = ref(PREP / 'scope.v3.proposed.json', '73f48cfb9aa7ffe7632a263202cda8da017f0b58e51c3f20f907f48f5ac5e227')
        scope = doc(proposed_ref)
        controller_review_ref = ref(N13 / 'desktop_exact15_integration_revision_independent_review_codex/87707854354a4cd8ad3a26aaf7627007/review.json', 'af1625660f48b4e1b70585dd2242aa852029503d03b73833835675c00af5665f')
        cr = doc(controller_review_ref)
        require(cr['requested_changes'] == [] and cr['actual_integration_executed'] is False and cr['controller_sha256'] == scope['controller_ref']['sha256'] and cr['launcher_sha256'] == scope['launcher_ref']['sha256'], 'fixed skeleton review')
        require(scope['authorized'] is False and scope['candidate'] == DESKTOP and scope['exact_paths'] == 15 and scope['union_paths'] == 58, 'source bounds')
        for item in [scope['controller_ref'], scope['launcher_ref'], scope['exact15_ref'], scope['patch_ref'], scope['logical43_tree_ref'], scope['owned_process_helper_ref']]:
            verify(item)
        desktop = doc(request['desktop_source_review_ref'])
        require(desktop['reviewer'] not in ['codex:/root/sources_parent_impl', 'codex:/root'] and desktop['source_commit'] == DESKTOP and desktop['source_integration_permitted'] is True and desktop['requested_changes'] == [], 'missing independent Desktop import permission; old reviews cannot be promoted')
        seal_members(request['desktop_source_review_manifest_ref'], [request['desktop_source_review_ref']])
        cli_ref = ref(N05 / 'cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e/review.json', 'fe7d4cb67d28517c4c55ca82461c0448f791635b128020faa1278b86d971fbf8')
        closed = doc(cli_ref)
        require(closed['schema'] == 'researchos.cli43-closed-execution-review.v1' and closed['reviewer'] != 'codex:/root' and closed['decision'] == 'EXACT43_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED' and closed['requested_changes'] == [], 'closed43 actual review')
        seal_members(ref(Path(cli_ref['path']).parent / 'manifest.json', '874c7461649170aad345357f2634cb5bf77f335871a4df1300f1fef45a0025a5'), [cli_ref])
        completed = doc(closed['completed_ref'])
        require(completed['actual_new_commit'] == CLI and completed['unique_combined_paths'] == 43 and completed['apply_attempts'] == completed['commit_attempts'] == 1, 'actual43')
        cm = seal_members(closed['manifest_ref'], [closed['completed_ref']])
        require(cm[bounded(closed['completed_ref']['path'])] == closed['completed_ref'], 'original ABS dictionary retained')
        post = doc(closed['post_registration_audit_ref'])
        require(post['registered_head'] == CLI and post['actual_registration_exit'] == 0 and post['completed_ref'] == closed['completed_ref'] and post['manifest_ref'] == closed['manifest_ref'], 'actual forward head registration')
        seal_members(closed['root_registration_manifest_ref'], [closed['post_registration_audit_ref'], closed['root_registration_handoff_ref']])
        scope.update(cli43_completed_ref=closed['completed_ref'], cli43_manifest_ref=closed['manifest_ref'], cli43_post_registration_audit_ref=closed['post_registration_audit_ref'], cli43_execution_review_ref=cli_ref)
        old = doc(ref(N05 / 'integration_codex/cli-exact8-source-integration-r323/scope_registration.json', '52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71'))
        for key in ['main38_completed_ref', 'main38_manifest_ref', 'main38_post_registration_audit_ref', 'main38_execution_review_ref']:
            scope[key] = old[key]
            verify(scope[key])
        seal_members(scope['main38_manifest_ref'], [scope['main38_completed_ref']])
        require(doc(scope['main38_execution_review_ref'])['requested_changes'] == [], 'Main38 unchanged closure')
        phase = 'CURRENT_CANONICAL_AND_CONFIRMED_ORIGINS'
        require(len(request['canonical_before_refs']) == 4, 'explicit ordered canonical4')
        raw_before = []
        for p, item in zip(CANON, request['canonical_before_refs']):
            require(bounded(item['path']) == p, 'canonical order')
            verify(item)
            raw_before.append(read(p))
        cp, ow = [parse(b) for b in raw_before[:2]]
        require([cp['revision'], ow['revision'], len(cp['failure_counters'])] == before and cp['head'] == CLI, 'no inferred/stale current tuple')
        prior = doc(request['current_root_handoff_ref'])
        seal_members(request['current_root_manifest_ref'], [request['current_root_handoff_ref']])
        require(len(prior['canonical_refs']) == 4 and all(same(a, b) for a, b in zip(prior['canonical_refs'], request['canonical_before_refs'])), 'current Root handoff not canonical-current')
        require('desktop_exact15_source_integration' not in ow['card_path_bindings']['W13-03'].get('subtasks', {}), 'no existing Desktop writer/registration')
        origins = request['confirmed_pending_origins']
        cut = doc(request['origin_cut_ref'])
        require(cut['schema'] == 'researchos.root-pending-origin-cut.v1' and cut['actor'] == 'codex:/root' and cut['registered_before'] == before,
            'actual Root pending-origin cut required; do not infer unseen branch counters')
        require(cut['confirmed_origins'] == origins and cut['registration_after'] == after and cut['counter_reset'] is False,
            'Root explicit cut/normalization differs')
        require(type(cut['retained_aftercut_origin_refs']) is list, 'remaining postcut origins must remain explicit')
        for item in cut['retained_aftercut_origin_refs']:
            verify(item)
        require(after[2] == before[2] + len(origins), 'only explicit confirmed pending additions')
        hashes = set()
        old_origin_sha = {x.get('evidence_ref', {}).get('sha256') for x in cp['failure_counters']}
        for row in origins:
            original = doc(row['evidence_ref'])
            require(original == row['original_payload'] and row['evidence_ref']['sha256'] not in hashes | old_origin_sha, 'origin duplicate/payload drift')
            require(row['count_once'] is True and row['counter_reset'] is False and row['product_cases_run'] == 0, 'confirmed tool-origin fields')
            require(row['actual_outer_exit'] is None or type(row['actual_outer_exit']) is int, 'nullable actual outer')
            require(row['actual_native_exit'] is None or type(row['actual_native_exit']) is int, 'nullable actual native')
            hashes.add(row['evidence_ref']['sha256'])
        phase = 'RUNTIME_RESOURCE_PINS'
        lock = doc(scope['toolchain_lock_ref'])['tools']
        catalog = doc(request['runtime_resources_ref'])
        require(type(catalog['files']) is list and catalog['files'], 'full actual public runtime catalog required')
        for row in catalog['files']:
            p = Path(row['path'])
            require(p.is_absolute() and p not in EXTERNAL, 'runtime exact paths')
            if not p.is_relative_to(ROOT):
                EXTERNAL[p] = row
        for row in catalog['files']:
            verify(row)
        require(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'pinned Python identity')
        for name in ['python', 'git']:
            require(ref(lock[name]['path'])['sha256'] == lock[name]['sha256'], 'actual executable SHA')
        expected = {bounded(x['path'], external=True): x for x in catalog['files']}
        expected[Path(__file__).resolve()] = ref(Path(__file__))
        expected[bounded(scope['owned_process_helper_ref']['path'])] = scope['owned_process_helper_ref']
        def runtime(label, dll=False):
            paths = {Path(sys.executable)}
            for module in list(sys.modules.values()):
                for key in ['__file__', '__cached__']:
                    p = getattr(module, key, None)
                    if p and Path(p).is_file():
                        paths.add(Path(p))
            if dll:
                paths.update(Path(x) for x in helper.runtime_resource_paths())
            rows = []
            for p in sorted(paths):
                q = bounded(p, external=True)
                require(q in expected, 'unfrozen Python/OS runtime')
                verify(expected[q])
                rows.append(ref(q))
            save(out, label + '.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': rows})
        runtime('runtime.before-import')
        hr = scope['owned_process_helper_ref']
        helper = types.ModuleType('desktop_binding_owned')
        helper.__file__ = str(bounded(hr['path']))
        sys.modules[helper.__name__] = helper
        exec(compile(read(hr['path']), helper.__file__, 'exec'), helper.__dict__)
        runtime('runtime.before', True)
        steps = 0
        def git(label, argv):
            nonlocal steps, phase, actual_native
            steps += 1
            require(steps <= 16, 'preparation readonly Git16')
            require(argv[0] in ['rev-parse', 'symbolic-ref', 'status', 'diff', 'ls-tree', 'rev-list', 'diff-tree', 'config'], 'readonly command allowlist')
            phase = label
            actual_native = None
            call = [lock['git']['path'], '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', *argv]
            env = {k: v for k, v in os.environ.items() if k.upper() in ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT']}
            env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul', GIT_TERMINAL_PROMPT='0')
            result = None
            error = None
            try:
                with (out / (label + '.stdout.raw')).open('xb') as so, (out / (label + '.stderr.raw')).open('xb') as se:
                    result = helper.run_owned(call, str(ROOT), env, so, se, 30)
                actual_native = result.get('actual_exit') if isinstance(result, dict) else None
                job_ok(result)
            except BaseException as exc:
                error = repr(exc)
                raise
            finally:
                save(out, label + '.invocation.json', {'argv': call, 'cwd': str(ROOT), 'actual_native_exit': actual_native, 'owned_result': result, 'error': error, 'automatic_retry': False})
            phase = 'POST_' + label
            actual_native = None
            return read(out / (label + '.stdout.raw'))
        require(git('head', ['rev-parse', 'HEAD']).decode().strip() == CLI, 'current43 head')
        require(git('branch', ['symbolic-ref', '--quiet', 'HEAD']).decode().strip() == request['expected_main_branch'], 'branch identity')
        status = git('status', ['status', '--porcelain=v1', '--untracked-files=no'])
        require(len(status.splitlines()) == 13 and sum(x[:2] == b' D' for x in status.splitlines()) == 11, 'old11/status shape')
        require(status == read(request['status_ref']['path']) and same(ref(request['status_ref']['path']), request['status_ref']), 'explicit current status')
        require(git('index', ['diff', '--cached', '--name-only']) == b'', 'index must be empty')
        config = git('config', ['config', '--local', '--no-includes', '--name-only', '--list']).decode()
        require(not any(x.lower().startswith(('filter.', 'include.', 'includeif.')) for x in config.splitlines()), 'Git external filtering refused')
        live = tree(git('tree43', ['ls-tree', '-r', '-z', CLI]))
        oldtree = tree(git('tree2cdb', ['ls-tree', '-r', '-z', ORIGINAL]))
        desktop_tree = tree(git('tree06b', ['ls-tree', '-r', '-z', DESKTOP]))
        require(live == doc(scope['logical43_tree_ref']), 'whole source-only43 tree')
        require(git('desktop-parent', ['rev-list', '--parents', '-n', '1', DESKTOP]).decode().split() == scope['candidate_parent_record'], 'candidate exact chain')
        require(git('desktop-delta6', ['diff-tree', '--no-commit-id', '--name-only', '-r', DESKTOP]).decode().splitlines() == scope['revision_delta6'], 'only reviewed6 final delta')
        exact = doc(scope['exact15_ref'])
        names = [x['path'] for x in exact]
        require(len(names) == len(set(names)) == 15 and names == sorted(names), 'exact15')
        actual43 = {x for x in set(live) | set(oldtree) if live.get(x) != oldtree.get(x)}
        require(len(actual43) == 43 and actual43 == set(scope['shared38_paths']) | set(scope['cli8_paths']) and not actual43.intersection(names), '43 disjoint15')
        desired_tree = dict(live)
        for row in exact:
            name = row['path']
            require(live.get(name) == oldtree.get(name) == row['before_git'] and desktop_tree[name] == row['after_git'], 'exact immutable preimage/finalblob')
            p = bounded(ROOT / name, row['before_git'] is not None)
            if row['before_git'] is None:
                require(not p.exists(), 'new source path already exists')
            else:
                current = ref(p, row['before_sha256'])
                require(current['bytes'] == row['before_bytes'], 'preimage bytes')
            desired_tree[name] = row['after_git']
        require(sum(oldtree.get(x) != desired_tree.get(x) for x in set(oldtree) | set(desired_tree)) == 58, 'union58')
        for name in actual43:
            raw = read(ROOT / name)
            require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == live[name]['blob'], 'current43 file/blob drift')
        planned = doc(scope['protected_source_paths_ref'])
        require(len(planned) == len(set(planned)) == 6983 and not set(names).intersection(planned), 'fixed full6983 inventory')
        protected = [ref(ROOT / name) for name in planned]  # Missing means refusal; never NULL replacement.
        require(scope['main_runtime_bundle_ref'] in protected, 'original Mu2a8 dictionary and bytes')
        require(read(ROOT / '.gitattributes') == b'* -text\n' and live['.gitattributes'] == oldtree['.gitattributes'] == desktop_tree['.gitattributes'] == {'mode': '100644', 'kind': 'blob', 'blob': 'fa1385d99a319b43c06f5309d1aae9fdd3adea46'}, 'root attributes bytes/blob')
        attrs = {ROOT / '.git/info/attributes'}
        for name in names:
            p = (ROOT / name).parent
            while p != ROOT:
                attrs.add(p / '.gitattributes')
                p = p.parent
        for p in attrs:
            if p.exists():
                require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()), 'active nested/info attributes')
        for name in scope['old_deleted_paths']:
            require(not os.path.lexists(ROOT / name), 'old deletion restored')
        phase = 'WRITE_BOUND_PROPOSAL'
        protected_ref = save(out, 'protected.actual-current43.json', protected)
        scope.update(authorized=False, status='PREPARATION_ONLY_BOUND_NOT_EXECUTABLE', expected_registration=after,
            expected_before_registration=before, registration_namespace=str(destination), operation_uuid=operation,
            new_output_root=str(execution), expected_cli43_head=CLI, expected_main_branch=request['expected_main_branch'],
            protected_source_vector_ref=protected_ref, runtime_resources_ref=request['runtime_resources_ref'],
            status_ref=ref(out / 'status.stdout.raw'), desktop_source_review_ref=request['desktop_source_review_ref'])
        scope['historical_evidence_refs'].extend([controller_review_ref, request['desktop_source_review_manifest_ref'],
            ref(N13 / 'desktop_http_exact15_revision_independent_review_codex/874a69212bac4d44be6316a27dc0bf32/review.json', 'ec0db191e493799a7e1623da8c04bc6dff8a320b9a700afc0f2c24e5ed74fa2a'),
            ref(N13 / 'desktop_go3_debug_component_evidence_independent_review_codex/35ff2da3523e4619b3f7bd763b2c91f2/review.json', 'a2f5729ba47437a158ca0857a91a732aa0ea099ce873a335f38998ec92a81de7')])
        copies = [save(out, p.stem + '.before.json', raw, True) for p, raw in zip(CANON, raw_before)]
        bound_ref = save(out, 'scope.bound.proposed.json', scope)
        active_plan = dict(scope)
        active_plan.update(authorized=True, status='ROOT_REGISTERED_DESKTOP15_SOURCE_COMMIT_ONCE')
        active_bytes = (json.dumps(active_plan, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        activation_ref = save(out, 'scope.activation-plan.json', {'authorized': False, 'future_root_grant': None,
            'materialization': 'Not an active scope. Only separately reviewed Root seal may write these exact bytes after actual CAS.',
            'future_scope_ref': {'path': str(destination / 'scope_registration.json'), 'sha256': hashlib.sha256(active_bytes).hexdigest(), 'bytes': len(active_bytes)},
            'future_scope_payload': active_plan})
        runtime('runtime.after', True)
        for p, raw in zip(CANON, raw_before):
            require(read(p) == raw, 'canonical drift during preparation')
        for item in list(READS.values()):
            verify(item)
        save(out, 'binding.prepared.json', {'schema': 'researchos.desktop15-root-binding-result.v1', 'actor': 'codex:/root',
            'authorized': False, 'future_root_grant': None, 'request_ref': request_ref, 'scope_ref': bound_ref,
            'activation_plan_ref': activation_ref,
            'canonical_copies': copies, 'canonical_before_refs': request['canonical_before_refs'], 'confirmed_pending_origins': origins,
            'expected_before': before, 'expected_after': after, 'current_root_handoff_ref': request['current_root_handoff_ref'],
            'origin_cut_ref': request['origin_cut_ref'], 'retained_aftercut_origin_refs': cut['retained_aftercut_origin_refs'],
            'current_root_manifest_ref': request['current_root_manifest_ref'], 'Git_readonly_calls': steps,
            'immutable_inputs': list(READS.values()), 'source_acceptance': False, 'formal_increment': 0,
            'candidate_imports': 0, 'source_canonical_index_writes': 0})
    except BaseException as exc:
        first = {'phase': phase, 'error': repr(exc), 'traceback': traceback.format_exc(), 'actual_native_exit': actual_native}
        print(json.dumps(first, ensure_ascii=False), file=sys.stderr)
    finally:
        if out is not None:
            if first is not None:
                try:
                    save(out, 'failure.origin.json', {'first_error': first, 'secondary_errors': secondary, 'automatic_retry': False, 'counter_reset': False})
                except BaseException as exc:
                    secondary.append({'phase': 'failure-evidence', 'error': repr(exc), 'actual_native_exit': None})
            try:
                entries = [ref(p) for p in sorted(out.iterdir()) if p.is_file()]
                save(out, 'manifest.json', {'count': len(entries), 'entries': entries, 'self_excluded': True})
            except BaseException as exc:
                detail = {'phase': 'manifest', 'error': repr(exc), 'actual_native_exit': None}
                if first is None:
                    first = detail
                else:
                    secondary.append(detail)
        if first is not None:
            print(json.dumps({'first_error': first, 'secondary_errors': secondary, 'retry': False, 'counter_reset': False}, ensure_ascii=False), file=sys.stderr)
    return 1 if first is not None else 0


if __name__ == '__main__':
    raise SystemExit(main())
