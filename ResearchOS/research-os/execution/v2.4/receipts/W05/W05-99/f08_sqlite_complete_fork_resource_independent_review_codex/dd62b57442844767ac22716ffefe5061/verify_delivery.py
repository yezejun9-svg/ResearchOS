from pathlib import Path
import base64, datetime, hashlib, json, os, stat

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0'
OUT = Path(__file__).resolve().parent
READS = {}
CHECKS = []
START = datetime.datetime.now(datetime.timezone.utc).isoformat()

def check(name, passed, detail=None):
    CHECKS.append({'name': name, 'passed': bool(passed), 'detail': detail})

def ordinary(path, directory=False):
    p = Path(path).absolute()
    if not p.is_relative_to(ROOT) or p.resolve(strict=True) != p:
        raise ValueError(('out of root or alias', str(p)))
    for q in [p] + list(p.parents):
        s = q.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 1024:
            raise ValueError(('reparse', str(q)))
    s = p.lstat()
    if not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)):
        raise ValueError(('wrong file type', str(p)))
    return p, s

def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)

def read(path):
    p, before = ordinary(path)
    raw = p.read_bytes()
    _, after = ordinary(p)
    if identity(before) != identity(after) or len(raw) != before.st_size:
        raise ValueError(('read drift', str(p)))
    r = {'path': p.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if r['path'] in READS and READS[r['path']] != r:
        raise ValueError(('repeat read drift', str(p)))
    READS[r['path']] = r
    return raw

def strict_pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(('duplicate JSON key', k))
        out[k] = v
    return out

def doc(path):
    return json.loads(read(path).decode('utf-8'), object_pairs_hook=strict_pairs)

def verify(ref):
    p = Path(ref['path'])
    if not p.is_absolute():
        p = ROOT / p
    raw = read(p)
    check('pin', hashlib.sha256(raw).hexdigest() == ref['sha256'] and len(raw) == ref['bytes'], p.as_posix())
    return raw

def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    p = OUT / name
    with p.open('xb') as f:
        f.write(raw)
    return {'path': p.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def inventory(root):
    ordinary(root, True)
    rows, dirs, pending = [], [], [root]
    while pending:
        parent = pending.pop()
        ordinary(parent, True)
        for p in sorted(parent.iterdir()):
            st = p.lstat()
            rel = p.relative_to(root).as_posix()
            if stat.S_ISDIR(st.st_mode):
                ordinary(p, True)
                dirs.append(rel)
                pending.append(p)
            else:
                ordinary(p)
                if any(c in rel for c in '\r\n') or any(x in ('', '.', '..') for x in rel.split('/')):
                    raise ValueError(('invalid module path', rel))
                read(p)
                rows.append({'relative_path': rel, **READS[p.as_posix()]})
    rows.sort(key=lambda x: x['relative_path'])
    check('no_windows_case_collision', len({r['relative_path'].casefold() for r in rows}) == len(rows), str(root))
    return rows, sorted(dirs)

def h1(rows, prefix=None):
    entries = [(prefix + '/' + r['relative_path'] if prefix else r['relative_path'], r['sha256']) for r in rows]
    raw = ''.join(digest + '  ' + name + '\n' for name, digest in sorted(entries, key=lambda e: e[0].encode('utf-8'))).encode('utf-8')
    return 'h1:' + base64.b64encode(hashlib.sha256(raw).digest()).decode('ascii')

pins = {
    'handoff.json': ('1db1cedbb28d1615ff9d6125346eb1b2e4e767c3411168aab883ce2fa3d5e3fe', 4881),
    'manifest.json': ('5e4aaf7c438796626e0120264236afeae11fdfe0a196e2bb61fb3145b5c873b3', 685369),
    'fork.file-lock.json': ('3dd2cd4dd14c184121b8d3c0d4d39e0e16de9b55b5421a8a28d3d4f19afd8dc0', 778776),
}
for name, (sha, size) in pins.items():
    verify({'path': (SOURCE/name).as_posix(), 'sha256': sha, 'bytes': size})
handoff = doc(SOURCE/'handoff.json')
mf = doc(SOURCE/'manifest.json')
check('manifest_count', len(mf['files']) == 1927)
check('manifest_unique_paths', len({r['path'].casefold() for r in mf['files']}) == len(mf['files']))
for r in mf['files']:
    check('manifest_source_namespace', Path(r['path']).is_relative_to(SOURCE), r['path'])
    verify(r)
for key, val in handoff.items():
    if key.endswith('_ref') and isinstance(val, dict) and {'path','sha256','bytes'} <= set(val):
        verify(val)
lock = doc(SOURCE/'fork.file-lock.json')
before = doc(SOURCE/'module.before.json')
after = doc(SOURCE/'module.after.json')
original_root = Path(handoff['source_module'])
fork_root = Path(handoff['fork_root'])
original_rows, original_dirs = inventory(original_root)
fork_rows, fork_dirs = inventory(fork_root)
check('original_before_exact_current', original_rows == before['files'])
check('original_after_exact_current', original_rows == after['files'])
check('fork_exact_lock', fork_rows == lock['files'])
check('directories_exact', original_dirs == fork_dirs == lock['directories'])
check('both_1899', len(original_rows) == len(fork_rows) == 1899)
check('original_bytes', sum(r['bytes'] for r in original_rows) == 150427576)
check('fork_bytes', sum(r['bytes'] for r in fork_rows) == 150427944)
old = {r['relative_path']:r for r in original_rows}
new = {r['relative_path']:r for r in fork_rows}
check('same_path_set', set(old) == set(new))
changed = [n for n in old if (old[n]['sha256'], old[n]['bytes']) != (new[n]['sha256'], new[n]['bytes'])]
check('exact_one_reviewed_file_delta', changed == ['sqlite.go'], changed)
check('candidate_exact_peer_bytes', new['sqlite.go']['sha256'] == '0eea393caed04ad05ff9a8ca2a1e81d6dc3ad519728ebfcd62fec66b1101e2cb' and new['sqlite.go']['bytes'] == 45071)
origin = doc(SOURCE/'module-origin-verification.json')
verify(origin['algorithm_ref'])
directory_h1 = h1(original_rows, 'modernc.org/sqlite@v1.60.1')
fork_h1 = h1(fork_rows, 'modernc.org/sqlite@v1.60.1')
mod_h1 = h1([old['go.mod']])
sum_lines = read(ROOT/'go.sum').decode('utf-8').splitlines()
check('upstream_dir_h1_all_three', directory_h1 == origin['directory_h1'] == origin['cached_ziphash'] == read(SOURCE/'origin/cache-v1.60.1.ziphash').decode().strip())
check('root_go_sum_dir_h1', sum_lines.count('modernc.org/sqlite v1.60.1 ' + directory_h1) == 1)
check('root_go_sum_mod_h1', sum_lines.count('modernc.org/sqlite v1.60.1/go.mod ' + mod_h1) == 1 and mod_h1 == origin['go_mod_h1'])
check('fork_h1_informational', fork_h1 == origin['fork_directory_h1_informational'] and fork_h1 != directory_h1)
check('cache_mod_same', read(original_root/'go.mod') == read(SOURCE/'origin/cache-v1.60.1.mod'))
check('go_module_identity_unchanged', read(fork_root/'go.mod').startswith(b'module modernc.org/sqlite\n'))
closure = doc(SOURCE/'inputs.before-after.json')
for r in closure['files']:
    verify(r)
check('source_reported_no_drift', closure['drift_count'] == 0)
notice = doc(SOURCE/'license-and-module-preservation.json')
for r in notice['license_notice_files']:
    verify(r)
    check('notice_unchanged', old[r['relative_path']]['sha256'] == r['sha256'])
tests = doc(SOURCE/'future-tests.corrected.proposed.json')
oracle = doc(SOURCE/'origin/independent-oracle-review.json')
check('future18_notrun', tests['count'] == len(tests['cases']) == 18 and all(r['status'] == 'NOT_RUN' for r in tests['cases']))
check('future18_ids', [r['id'] for r in tests['cases']] == ['I%02d'%i for i in range(1,19)])
for t, peer in zip(tests['function_list_oracle'], oracle['cases'], strict=True):
    check('peer_oracle_preserved', t['enc'] == peer['enc'] == 'utf8' and t['flags'] == peer['pragma_flags'] and t['internal_eTextRep'] == peer['eTextRep'] and t['deterministic'] == peer['Deterministic'] and t['innocuous'] == peer['Innocuous'])
contract = doc(SOURCE/'consumer-and-driver-validation.contract.proposed.json')
check('version_qualified_replace', contract['version_qualified_replace'] == 'replace modernc.org/sqlite v1.60.1 => ./third_party/modernc_sqlite_v1_60_1_researchos_innocuous')
check('no_implicit_authorization', contract['authorized'] is False and contract['actual_grant'] is None and tests['bounded_future_execution_authorization'] is False)
for k in ('consumer_go_mod_before_ref','consumer_go_sum_before_ref'):
    verify(contract[k])
before_reads = list(READS.values())
write('input-vector.before.json', before_reads)
for ref in before_reads:
    verify(ref)
write('input-vector.after.json', list(READS.values()))
write('verification.json', {'schema':'researchos.complete-fork-independent-io-audit.v1','started_at':START,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':CHECKS,'failed':[r for r in CHECKS if not r['passed']],'read_input_count':len(READS),'source_files':len(original_rows),'fork_files':len(fork_rows),'directory_h1':directory_h1,'go_mod_h1':mod_h1,'fork_h1_informational':fork_h1,'changed_files':changed,'independent_patch_correctness_review':False,'no_handle_level_anti_race_claim':True,'target_execution':0})
print(json.dumps({'out':OUT.as_posix(),'checks':len(CHECKS),'failed':[r for r in CHECKS if not r['passed']],'inputs':len(READS)},ensure_ascii=False))
