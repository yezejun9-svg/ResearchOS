"""UNEXECUTED Root preparation builder. Emits drafts, never invokes a CAS mode."""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
import types
import time

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
CANON = [ROOT / 'execution/v2.4' / (x + '.json') for x in ['checkpoint', 'path_ownership', 'step_state', 'commands']]


def need(v, reason):
    if not v:
        raise RuntimeError(reason)


def parse(b):
    def pairs(items):
        d = {}
        for k, v in items:
            need(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    return json.loads(b.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def path(v, exists=True):
    p = Path(v)
    p = p if p.is_absolute() else ROOT / p
    need(p.is_relative_to(ROOT) and '..' not in p.parts and p.resolve(strict=exists) == p.absolute(), 'Root path/alias')
    for q in [p, *p.parents]:
        if os.path.lexists(q):
            need(not q.is_symlink() and not (getattr(q.lstat(), 'st_file_attributes', 0) & 0x400), 'reparse ancestor')
    return p


def ref(v):
    p = path(v)
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def verify(r):
    a = ref(r['path'])
    need(a['sha256'] == r['sha256'] and a['bytes'] == r['bytes'], 'ref bytes changed')
    return path(r['path']).read_bytes()


def doc(r):
    return parse(verify(r))


def encode(d):
    return (json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--input-sha256', required=True)
    a = ap.parse_args()
    out = None
    first = None
    try:
        need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and Path.cwd().resolve() == ROOT, 'pinned Python flags/cwd')
        ir = ref(a.input)
        need(ir['sha256'] == a.input_sha256, 'input SHA')
        data = doc(ir)
        need(data['schema'] == 'researchos.desktop15-metadata-template-parameters.v1' and data['actor'] == 'codex:/root', 'Root actual parameters')
        need(data['action'] == 'PREPARE_METADATA_TEMPLATES_ONLY' and data['authorized'] is False and data['future_root_grant'] is None, 'not CAS authority')
        binding = doc(data['binding_ref'])
        need(binding['schema'] == 'researchos.desktop15-root-binding-result.v1' and binding['actor'] == 'codex:/root' and binding['authorized'] is False, 'actual bound proposal')
        mf = doc(data['binding_manifest_ref'])
        need(mf['count'] == len(mf['entries']), 'binding MF count')
        members = {}
        parent = path(data['binding_manifest_ref']['path']).parent
        for item in mf['entries']:
            p = path(item['path'])
            need(p.is_relative_to(parent) and p not in members, 'binding MF escape/duplicate')
            verify(item)
            members[p] = item
        need(path(data['binding_ref']['path']) in members, 'binding must be sealed')
        source = doc(binding['scope_ref'])
        need(source['authorized'] is False and source['status'] == 'PREPARATION_ONLY_BOUND_NOT_EXECUTABLE', 'bound proposal state')
        active = dict(source)
        active.update(authorized=True, status='ROOT_REGISTERED_DESKTOP15_SOURCE_COMMIT_ONCE')
        active_bytes = encode(active)
        destination = path(source['registration_namespace'], False)
        need(destination.parent == ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex' and not destination.exists(), 'new registration namespace only')
        future_scope = {'path': str(destination / 'scope_registration.json'), 'sha256': hashlib.sha256(active_bytes).hexdigest(), 'bytes': len(active_bytes)}
        activation = doc(binding['activation_plan_ref'])
        need(activation['authorized'] is False and activation['future_root_grant'] is None and activation['future_scope_ref'] == future_scope and activation['future_scope_payload'] == active, 'reviewable activation plan byte identity')
        review = doc(data['controller_review_ref'])
        need(review['schema'] == 'researchos.desktop15-source-integration-controller-review.v1' and review['reviewer'] == 'codex:/root/w05_merge_review', 'new nonauthor actual scope review')
        need(review['decision'] == 'READY_FOR_ROOT_EXACT15_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES' and review['requested_changes'] == [] and review['actual_integration_executed'] is False, 'new scope review decision')
        need(review['scope_sha256'] == future_scope['sha256'] and review['controller_sha256'] == source['controller_ref']['sha256'] and review['launcher_sha256'] == source['launcher_ref']['sha256'], 'full final scope bytes and skeleton hashes')
        need(review['bound_proposal_sha256'] == binding['scope_ref']['sha256'] and review['metadata_template_builder_sha256'] == ref(__file__)['sha256'], 'this builder/full binding reviewed')
        reviewmf = doc(data['controller_review_manifest_ref'])
        need(reviewmf['count'] == len(reviewmf['entries']), 'review MF count')
        seen = {}
        rp = path(data['controller_review_manifest_ref']['path']).parent
        for x in reviewmf['entries']:
            q = path(x['path'])
            need(q.is_relative_to(rp) and q not in seen, 'review MF boundary')
            verify(x)
            seen[q] = x
        need(path(data['controller_review_ref']['path']) in seen, 'review not sealed')
        need(len(binding['canonical_before_refs']) == len(binding['canonical_copies']) == 4, 'four current/original canonical')
        before = []
        for q, actual, copied in zip(CANON, binding['canonical_before_refs'], binding['canonical_copies']):
            need(path(actual['path']) == q and verify(actual) == verify(copied), 'stale canonical/current counters')
            before.append(verify(actual))
        cp, ow = [parse(b) for b in before[:2]]
        need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == binding['expected_before'] and cp['head'] == source['expected_cli43_head'], 'no guessed tuple/head')
        lock = doc(source['toolchain_lock_ref'])['tools']
        need(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve() and hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256'], 'actual pinned Python')
        template_ref = data['metadata_engine_ref']
        need(path(template_ref['path']) == HERE / 'metadata-engine.template.py' and review['metadata_engine_sha256'] == template_ref['sha256'], 'exact reviewed metadata engine')
        template = verify(template_ref).decode('utf-8')
        ast.parse(template)
        marker = chr(10) + 'MODE = ' + repr('register') + chr(10)
        need(template.count(marker) == 1, 'unique mode marker')
        destination.mkdir(exist_ok=False)
        out = destination
        def save(name, value, raw=False):
            with (out / name).open('xb') as f:
                f.write(value if raw else encode(value))
            return ref(out / name)
        save('preparation.started.json', {'input_ref': ir, 'actual_registration_executed': False, 'source_acceptance': False})
        originals = [save(q.stem + '.original.json', b, True) for q, b in zip(CANON, before)]
        payload_ref = save('scope-registration.payload.json', {'authorized': False, 'future_root_grant': None,
            'materialization': 'Only seal after reviewed successful CAS; this payload is not a scope or grant.',
            'future_scope_ref': future_scope, 'scope': active})
        scripts = {}
        for mode, filename in [('register', 'register.py'), ('run', 'run.py'), ('seal', 'seal.py'), ('grant', 'grant-producer.py')]:
            text = template.replace(marker, chr(10) + 'MODE = ' + repr(mode) + chr(10), 1)
            ast.parse(text, filename=filename)
            scripts[mode] = save(filename, text.encode('utf-8'), True)
        resources = doc(source['runtime_resources_ref'])['files']
        immutable = {str(path(x['path'])) if Path(x['path']).is_relative_to(ROOT) else str(Path(x['path'])): x for x in binding['immutable_inputs'] if path_or_external(x['path']) not in CANON}
        for item in [ir, data['binding_ref'], data['binding_manifest_ref'], data['controller_review_ref'], data['controller_review_manifest_ref'], template_ref, ref(__file__), payload_ref, *originals]:
            immutable[str(path(item['path']))] = item
        prepared = {'authorized': False, 'future_root_grant': None, 'registration_namespace': str(out),
            'head': source['expected_cli43_head'], 'candidate': source['candidate'], 'before_tuple': binding['expected_before'],
            'after_tuple': binding['expected_after'], 'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'original_refs': originals, 'future_scope_ref': future_scope, 'active_scope_payload_ref': payload_ref,
            'controller_review_ref': data['controller_review_ref'], 'binding_ref': data['binding_ref'],
            'origins': binding['confirmed_pending_origins'], 'source_paths': [x['path'] for x in doc(source['exact15_ref'])],
            'origin_cut_ref': binding['origin_cut_ref'], 'retained_aftercut_origin_refs': binding['retained_aftercut_origin_refs'],
            'status_ref': source['status_ref'], 'old_deleted_paths': source['old_deleted_paths'],
            'runtime_files': resources, 'toolchain_lock_ref': source['toolchain_lock_ref'], 'helper_ref': source['owned_process_helper_ref'],
            'script_refs': scripts, 'immutable_inputs': list(immutable.values()), 'source_acceptance': False, 'formal_increment': 0}
        # Import definitions only and call the one reviewed, pure metadata transform.
        # No setup, source_guard, helper, subprocess, CAS or grant function is invoked.
        engine = types.ModuleType('desktop_registration_pure_transform')
        engine.__file__ = str(out / 'register.py')
        exec(compile(template, str(template_ref['path']), 'exec'), engine.__dict__)
        engine.OUT = out
        engine.DEADLINE = time.monotonic() + 1200
        checked_before, target = engine.desired(prepared)
        need(checked_before == before, 'transform originals')
        prepared['desired_refs'] = [save(q.stem + '.desired.json', b, True) for q, b in zip(CANON, target)]
        audit_ref = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
            'expected_before': prepared['before_tuple'], 'expected_after': prepared['after_tuple'], 'head': prepared['head'],
            'future_scope_ref': future_scope, 'controller_review_ref': data['controller_review_ref'], 'authorized': False,
            'future_root_grant': None, 'actual_registration_executed': False, 'source_acceptance': False, 'formal_increment': 0,
            'origin_cut_ref': binding['origin_cut_ref'], 'retained_aftercut_origin_refs': binding['retained_aftercut_origin_refs'],
            'active_scope_materialization': 'After actual CAS, in separately reviewed seal; source execution still needs exclusive grant.'})
        prepared['immutable_inputs'].extend(prepared['desired_refs'] + [audit_ref])
        pr = save('prepared_refs.json', prepared)
        need(all(q.read_bytes() == b for q, b in zip(CANON, before)), 'canonical drift during preparation')
        save('preparation.completed.json', {'prepared_ref': pr, 'audit_ref': audit_ref, 'scripts': scripts,
            'actual_registration_executed': False, 'actual_product_execution': False, 'future_root_grant': None})
        rows = [ref(q) for q in sorted(out.iterdir()) if q.is_file()]
        save('preparation.manifest.json', {'count': len(rows), 'entries': rows, 'self_excluded': True})
    except BaseException as exc:
        first = {'phase': 'METADATA_TEMPLATE_PREPARATION', 'error': repr(exc), 'traceback': traceback.format_exc(), 'actual_native_exit': None}
        print(json.dumps(first, ensure_ascii=False), file=sys.stderr)
        if out is not None:
            try:
                with (out / 'preparation.failure.json').open('xb') as f:
                    f.write(encode({'first_error': first, 'automatic_retry': False, 'counter_reset': False}))
            except BaseException as secondary:
                print(json.dumps({'first_error': first, 'secondary_error': repr(secondary), 'actual_native_exit': None}, ensure_ascii=False), file=sys.stderr)
    return 1 if first is not None else 0


def path_or_external(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


if __name__ == '__main__':
    raise SystemExit(main())
