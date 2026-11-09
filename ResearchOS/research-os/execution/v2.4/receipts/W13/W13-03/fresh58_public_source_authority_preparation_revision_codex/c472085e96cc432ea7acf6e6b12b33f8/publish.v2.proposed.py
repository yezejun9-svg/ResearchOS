"""Root-only future pure-IO source publication. Preparation is not execution authority.

No Git/process/compiler/package/network API. Missing Main bytes are OPEN, never restored.
Run only after independent source review, using explicit immutable Root request + SHA.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import traceback
import types

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
PARENT = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
FIXED_SHA = 'bc865b00f4093f14b6cb5d40ba05099cd13e6b39cfb36ac8d520eb7eecac0a93'
PUBLISH_PARENT = ROOT/'execution/v2.4/receipts/W13/W13-03/fresh58_public_source_authority_codex'
CANONICAL = ['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']]
READS = {}
LIVE_OBSERVATIONS = []


def need(value, message):
    if not value:
        raise RuntimeError(message)


def parse(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'Duplicate JSON key')
            result[k] = v
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON: '+value)
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=invalid)


def safe(value, exists=True):
    p = Path(value)
    if not p.is_absolute():
        p = ROOT/p
    need('..' not in p.parts and p != ROOT and p.is_relative_to(ROOT), 'Outside public repository')
    need(str(p.resolve(strict=exists)) == str(p.absolute()), 'Noncanonical path')
    for q in [p, *p.parents]:
        if os.path.lexists(q):
            st = os.lstat(q)
            need(not q.is_symlink() and not (getattr(st, 'st_file_attributes', 0) & 0x400), 'Reparse path')
        if q == ROOT:
            break
    return p


def read(value):
    p = safe(value)
    need(p.is_file(), 'Not a regular public input')
    raw = p.read_bytes()
    key = str(p)
    if key in READS:
        need(READS[key] == raw, 'Input drift: '+key)
    READS[key] = raw
    return raw


def pin_bytes(path, raw):
    return {'path':str(path), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}


def verify(ref):
    need(type(ref) is dict and set(ref) == {'path','sha256','bytes'}, 'Exact ref fields')
    need(type(ref['bytes']) is int and ref['bytes'] >= 0, 'Invalid bytes')
    raw = read(ref['path'])
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Ref mismatch')
    return raw


def doc(ref):
    return parse(verify(ref))


def relative(value):
    p = PurePosixPath(value)
    need(type(value) is str and not p.is_absolute() and str(p) == value and
         '\\' not in value and ':' not in value and '..' not in p.parts and value != '.', 'Bad tree name')
    need(not value.startswith(('execution/', '.local/', '.git/')) and
         not any(x.lower() in ('secrets','vault','private_holdout','privateholdout') for x in p.parts), 'Private/nonproduct source')
    return value


def tree_rows(raw):
    need(raw.endswith(b'\0'), 'ls-tree -z terminator')
    rows, folded = {}, set()
    for entry in raw[:-1].split(b'\0'):
        meta, name = entry.split(b'\t', 1)
        mode, kind, blob = meta.decode('ascii').split(' ')
        p = name.decode('utf-8', errors='strict')
        need(p not in rows and p.casefold() not in folded, 'Duplicate/Windows alias in tree')
        need(len(blob) == 40 and all(x in '0123456789abcdef' for x in blob), 'Invalid blob')
        rows[p] = {'mode':mode, 'kind':kind, 'git_blob':blob}
        folded.add(p.casefold())
    return rows


def select(tree, old, combined):
    oldnames = {relative(x['path']) for x in old['files']}
    need(len(oldnames) == old['file_count'] == len(old['files']) and old['commit'] == PARENT, 'Old catalogue shape')
    go = {p for p in tree if p.endswith('.go') and not p.startswith(('execution/','.local/'))}
    extra = {'apps/desktop/build-validator.py','spec/v2.0/ui/design-tokens.json',
             'tests/contracts/fixtures/client_protocol_v2_fixtures.json','tests/ui/desktop/w13-react.test.js',
             'apps/desktop/package.json','apps/desktop/package-lock.json','apps/web/package.json','apps/web/package-lock.json'}
    for p in tree:
        if (p.startswith(('apps/desktop/main/','apps/desktop/preload/','apps/desktop/validator/','apps/web/src/','apps/web/public/')) or
            (p.startswith('apps/web/') and p.count('/') == 2) or
            (p.startswith('tests/ui/desktop/') and p.count('/') == 3 and p.endswith('.mjs')) or
            (p.startswith('apps/desktop/tests/') and p.count('/') == 3 and p.endswith('.js'))):
            extra.add(p)
    names = oldnames | go | set(combined) | extra | {'go.mod','go.sum'}
    names |= {p for p in tree if p.startswith(('migrations/sqlite/','spec/v2.0/contracts/'))}
    for p in names:
        relative(p)
        need(p in tree and tree[p]['mode'] == '100644' and tree[p]['kind'] == 'blob', 'Missing/unsupported public blob: '+p)
    return sorted(names), oldnames, go


def live_guard(copies, expected_tuple):
    # Mutable canonical files are observations, never immutable READS entries.
    observation = {'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'point_in_time_only':True,'lifecycle_proof':False,'files':[],
                   'tuple':None,'head':None,'matched':False}
    LIVE_OBSERVATIONS.append(observation)
    live_raw = []
    for i, canonical in enumerate(CANONICAL):
        need(copies[i]['canonical_path'] == canonical, 'Live canonical copy order')
        expected = verify(copies[i]['ref'])
        p = safe(ROOT/canonical)
        need(p.is_file(), 'Live canonical is not a regular file')
        raw = p.read_bytes()
        observation['files'].append({'canonical_path':canonical,'live_ref':pin_bytes(p,raw),
                                     'copy_ref':copies[i]['ref'],'byte_equal':raw == expected})
        live_raw.append(raw)
    need(all(x['byte_equal'] for x in observation['files']), 'Current live canonical bytes differ from reviewed copies')
    cp, ow = [parse(x) for x in live_raw[:2]]
    actual = [cp['revision'],ow['revision'],len(cp['failure_counters'])]
    observation['tuple'], observation['head'] = actual, cp['head']
    need(all(type(x) is int for x in actual) and actual == expected_tuple and cp['head'] == SOURCE,
         'Current live canonical tuple/head differs from explicit reviewed authority')
    observation['matched'] = True
    observation['completed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()


def stable(copies, expected_tuple):
    for p, raw in list(READS.items()):
        need(read(p) == raw, 'Frozen input drift')
    live_guard(copies, expected_tuple)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use Python -I -S -X utf8')
    sys.dont_write_bytecode = True
    need(len(sys.argv) == 3, 'request-path request-sha256 required')
    rr = pin_bytes(safe(sys.argv[1]), read(sys.argv[1]))
    need(rr['sha256'] == sys.argv[2], 'Request SHA')
    q = doc(rr)
    need(q['schema'] == 'researchos.fresh58-public-source-publication-request.v1' and
         q['owner'] == 'codex:/root' and q['source_commit'] == SOURCE and q['source_parent'] == PARENT,
         'Explicit Root source-publication request required')
    need(q['source_acceptance'] is False and q['execution_authorized'] is False and q['formal_increment'] == 0,
         'Metadata publication cannot authorize source/compile/tests/grant')
    need(safe(q['producer_ref']['path']) == Path(__file__).resolve(), 'Producer identity')
    verify(q['producer_ref'])
    fixed = doc(q['fixed_inputs_ref'])
    need(q['fixed_inputs_ref']['sha256'] == FIXED_SHA, 'Fixed source input contract')
    for ref in fixed.values():
        verify(ref)
    review = doc(q['independent_preparation_review_ref'])
    need(review['schema'] == 'researchos.fresh58-catalog-producer-independent-review.v1' and
         review['reviewer'] in ['codex:/root/w05_merge_review','codex:/root/f08_whole_scope_review'] and
         review['decision'] == 'READY_SOURCE_PREPARATION_ONLY' and review['requested_changes'] == [] and
         review['producer_ref'] == q['producer_ref'] and review['fixed_inputs_ref'] == q['fixed_inputs_ref'],
         'Independent source-only preparation review required')
    uid = q['publish_uuid']
    need(type(uid) is str and len(uid) == 32 and all(c in '0123456789abcdef' for c in uid), 'Explicit UUID')
    need(type(q['timestamp_utc']) is str and datetime.datetime.fromisoformat(q['timestamp_utc']).utcoffset() == datetime.timedelta(0), 'Explicit UTC timestamp')
    out = safe(q['new_publish_root'], False)
    need(out.parent == PUBLISH_PARENT and out.name == uid and not os.path.lexists(out) and out.parent.is_dir(), 'Exclusive Root publication leaf')
    need(all(not safe(p).is_relative_to(out) for p in READS), 'Inputs inside output')
    inv = doc(fixed['tree_invocation'])
    need(inv['argv'][-4:] == ['ls-tree','-r','-z',SOURCE] and str(Path(inv['cwd']).resolve()) == str(ROOT),
         'Actual sealed tree invocation framing')
    need(inv['actual_native_exit'] == 0 and inv['wrapper_error'] is None and
         inv['process_observation']['actual_exit'] == 0 and inv['automatic_retry'] is False, 'Tree invocation failed')
    closure = doc(fixed['closure'])
    original_scope = doc(fixed['source_scope'])
    need(closure['scope_ref'] == fixed['source_scope'], 'Source scope exact binding')
    source_mf = doc(closure['manifest_ref'])
    members = source_mf['entries']
    need(len(members) == source_mf['count'], 'Source manifest cardinality')
    for ref in [fixed['tree'],fixed['tree_invocation']]:
        need(any(safe(m['path']) == safe(ref['path']) and m['sha256'] == ref['sha256'] and m['bytes'] == ref['bytes'] for m in members), 'Tree not in closed source manifest')
    combined = sorted(set(original_scope['shared38_paths']+original_scope['cli8_paths']+closure['source_paths']))
    need(len(combined) == 58, 'Accepted exact58 union')
    tree = tree_rows(verify(fixed['tree']))
    old = doc(fixed['old_catalog'])
    names, oldnames, go = select(tree, old, combined)
    oldrows = {x['path']:x for x in old['files']}
    need(all(tree[p]['git_blob'] == row['git_blob'] or p in closure['source_paths'] for p,row in oldrows.items()), 'Unknown historical source delta')
    rows, provenance, embeds = [], [], []
    for p in names:
        raw = read(ROOT/p)
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
        need(blob == tree[p]['git_blob'], 'OPEN: Main bytes do not equal sealed Git blob: '+p)
        row = {'path':p, **tree[p], 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
        rows.append(row)
        provenance.append({'path':p,'read_from':'MAIN_READ_ONLY','git_blob_verified':blob,'source_ref':pin_bytes(ROOT/p,raw)})
        if p.endswith('.go'):
            for line in raw.decode('utf-8', errors='strict').splitlines():
                if line.strip().startswith('//go:embed '):
                    embeds.append({'file':p,'directive':line.strip(),'future_actual_go_list_embed_gate':True})
    need(next(x for x in rows if x['path']=='apps/desktop/build-validator.py')['sha256'] == fixed['builder']['sha256'], 'Builder changed')
    copies = q['canonical_copies']
    need(type(copies) is list and [x['canonical_path'] for x in copies] == CANONICAL, 'Canonical copy order')
    documents = []
    for item in copies:
        need(safe(item['ref']['path']) not in [ROOT/x for x in CANONICAL], 'Do not freeze live canonical as immutable')
        documents.append(doc(item['ref']))
    cp, ow = documents[:2]
    actual = [cp['revision'],ow['revision'],len(cp['failure_counters'])]
    need(type(q['expected_current_tuple']) is list and len(q['expected_current_tuple']) == 3 and
         all(type(x) is int for x in q['expected_current_tuple']) and actual == q['expected_current_tuple'], 'Explicit actual copied tuple')
    forward_review_ref = q['forward_registration_review_ref']
    need(forward_review_ref['sha256'] == 'f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624' and
         forward_review_ref['bytes'] == 7591, 'Actual independently closed forward registration')
    forward_review = doc(forward_review_ref)
    need(forward_review['schema'] == 'researchos.desktop58-source-head-registration-closed-review.v1' and
         forward_review['reviewer'] == 'codex:/root/w05_merge_review' and
         forward_review['decision'] == 'SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' and
         forward_review['requested_changes'] == [] and forward_review['actual_registration_evidence_closed'] is True and
         forward_review['actual_head'] == SOURCE and forward_review['actual_parent'] == PARENT and
         forward_review['canonical_tuple'] == actual and forward_review['source_acceptance'] is False and
         forward_review['fresh58_qualified'] is False, 'Forward review/current copied authority mismatch')
    for key, ref in [('post_registration_audit_ref',fixed['forward_audit']),
                     ('registration_manifest_ref',fixed['forward_manifest']),('source_execution_review_ref',fixed['closure'])]:
        need(verify(forward_review[key]) == verify(ref), 'Forward review source chain')
    verify(forward_review['root_tool_observations_ref'])
    need(len(forward_review['canonical_refs']) == 4, 'Reviewed canonical count')
    for i, original in enumerate(forward_review['canonical_refs']):
        need(safe(original['path']) == ROOT/CANONICAL[i], 'Reviewed canonical identity/order')
        raw = verify(copies[i]['ref'])
        need(len(raw) == original['bytes'] and hashlib.sha256(raw).hexdigest() == original['sha256'], 'Copied bytes not actual reviewed canonical')
    catalog = {'schema':'researchos.cli43.public-source-catalog.v1','commit':SOURCE,'files':rows,
               'file_count':len(rows),'all_platform_Go_count':len(go),'old_paths_used_as_public_name_hints_only':len(oldnames),
               'old_blobs_and_hashes_reused':False,'embed_directives':embeds,'runtime_graph_NOT_RUN':True,
               'runtime_missing_input_policy':'FAIL_BEFORE_COMPILE; no on-demand unregistered filesystem widening'}
    byname = {r['path']:r for r in rows}
    combined_doc = {'schema':'researchos.current58-combined-source-set.v1','source_commit':SOURCE,'source_parent':PARENT,
                    'source_commit_closure_ref':fixed['closure'],
                    'files':[{k:byname[p][k] for k in ['path','sha256','bytes']} for p in combined]}
    pending = {}
    def proposed(name, value):
        raw = encode(value); path = out/name; pending[str(path)] = raw
        return pin_bytes(path, raw)
    catalog_ref = proposed('public-source-catalog.json',catalog)
    combined_ref = proposed('combined58-source-set.json',combined_doc)
    history = doc(fixed['old_authority'])['sealed_integration_refs']
    for ref in history:
        verify(ref)
    authority = {'schema':'researchos.cli43.current-source-validation-authority.v1','actor':'codex:/root',
                 'source_commit':SOURCE,'source_parent':PARENT,'current_canonical_head':cp['head'],
                 'source_integration_completed':True,'unique_combined_source_paths':58,
                 'combined_source_set_ref':combined_ref,'source_commit_closure_ref':fixed['closure'],
                 'forward_head_audit_ref':fixed['forward_audit'],'forward_head_manifest_ref':fixed['forward_manifest'],
                 'forward_registration_review_ref':forward_review_ref,
                 'sealed_integration_refs':history+[fixed['closure'],fixed['forward_audit'],fixed['forward_manifest'],forward_review_ref],
                 'current_canonical_copies':copies,'canonical_tuple_at_publication':actual,
                 'current_canonical_refs':forward_review['canonical_refs'],
                 'catalog_ref':catalog_ref,'publication_request_ref':rr,'timestamp_utc':q['timestamp_utc'],
                 'source_acceptance':False,'fresh_compilation_or_cases_accepted':False,'formal_increment':0,
                 'goal_complete':False,'execution_authorized':False,'grant_authorized':False,
                 'historical_wire_name_only':'current43; actual immutable source set is current58'}
    # Reuse the independently reviewed pure-IO source predicate, not its execution-grant entry.
    gate_raw = verify(fixed['gate'])
    module = types.ModuleType('current58_source_predicate'); module.__file__ = str(safe(fixed['gate']['path']))
    exec(compile(gate_raw,module.__file__,'exec'),module.__dict__)
    class ProspectiveReader:
        def verify(self, ref):
            key = str(safe(ref['path'],False))
            if key in pending:
                raw = pending[key]
                need(pin_bytes(Path(key),raw) == ref, 'Prospective exact ref')
                return raw
            return verify(ref)
        def doc(self, ref):
            return parse(self.verify(ref))
    module.validate_current58_source(ProspectiveReader(), {'catalog_ref':catalog_ref}, authority, cp, ow)
    proposed('current43-authority.json',authority)
    proposed('source-provenance.json',{'files':provenance,'selection_added_paths':sorted(set(names)-oldnames),
             'selected_count':len(rows),'actual_compiler_graph':None,'loose_or_packed_git_objects_read':False})
    stable(copies, q['expected_current_tuple'])
    need(not os.path.lexists(out), 'Output appeared before allocation')
    out.mkdir()
    try:
        for name, raw in pending.items():
            with Path(name).open('xb') as f:
                f.write(raw)
        stable(copies, q['expected_current_tuple'])
        before = [pin_bytes(Path(p),raw) for p,raw in sorted(READS.items())]
        with (out/'inputs.json').open('xb') as f:
            f.write(encode({'files':before,'drift':[],'only_public_source_IO':True}))
        stable(copies, q['expected_current_tuple'])
        entries = [pin_bytes(p,p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()]
        with (out/'manifest.json').open('xb') as f:
            f.write(encode({'entries':entries,'count':len(entries),'self_excluded':True}))
        stable(copies, q['expected_current_tuple'])
        print(json.dumps({'status':'SOURCE_METADATA_PUBLISHED_NOT_QUALIFIED','output':str(out),'files':len(rows),
                          'source_acceptance':False,'formal_increment':0,'execution_authorized':False,
                          'live_canonical_observations':LIVE_OBSERVATIONS}))
    except BaseException as error:
        try:
            with (out/'failure.json').open('xb') as f:
                f.write(encode({'error':str(error),'traceback':traceback.format_exc(),'actual_native_exit':None,
                                'source_acceptance':False,'automatic_retry':False,'counter_reset':False,
                                'live_canonical_observations':LIVE_OBSERVATIONS}))
        except BaseException as secondary:
            print('Secondary evidence write error: '+str(secondary),file=sys.stderr)
        raise


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print(json.dumps({'live_canonical_observations':LIVE_OBSERVATIONS,'actual_native_exit':None}),file=sys.stderr)
        sys.exit(1)
