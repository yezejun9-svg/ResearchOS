#!/usr/bin/env python3
"""ResearchOS v2.4 qualification driver.
Runs REAL checks against fixed upstream sources in qualification/v2.4.
--check-id selects one check; unknown/unimplemented ids exit non-zero with NOT_IMPLEMENTED.
No dependency on the old dispatcher. Raw upstream outputs are saved under qualification/v2.4/evidence/.
"""
import argparse, hashlib, json, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MU = os.path.join(HERE, 'mu')
EVID = os.path.join(HERE, 'evidence')
MU_COMMIT = '8dfebe36508ac0c2508735bb866756dab9283e74'
MU_REMOTE = 'https://github.com/qybaihe/mu'
SPEC_REFS = r'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/references/Mu_Source_Manifest.json'

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def git(*args, cwd=MU):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')

def record(name, payload):
    os.makedirs(EVID, exist_ok=True)
    p = os.path.join(EVID, name + '.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return p

def check_w01_01():
    results, failures = [], []
    def gate(cid, ok, detail):
        results.append({'check_id': cid, 'result': 'PASS' if ok else 'FAIL', 'detail': detail})
        if not ok:
            failures.append(cid)
    # 1 fixed source
    r = git('rev-parse', 'HEAD')
    head = r.stdout.strip()
    gate('W01-01-HEAD', head == MU_COMMIT, f'HEAD={head}')
    rem = git('remote', 'get-url', 'origin').stdout.strip()
    gate('W01-01-REMOTE', rem == MU_REMOTE, f'remote={rem}')
    # 2 manifest hashes from spec references
    try:
        man = json.load(open(SPEC_REFS, encoding='utf-8'))
        mism = []
        for e in man['files']:
            p = os.path.join(MU, *e['path'].split('/'))
            if not os.path.isfile(p):
                mism.append({'path': e['path'], 'problem': 'missing'})
            elif sha256(p) != e['sha256']:
                mism.append({'path': e['path'], 'problem': 'hash'})
        gate('W01-01-MANIFEST', not mism, f'{len(man["files"])} files, mismatches={mism}')
    except Exception as exc:
        gate('W01-01-MANIFEST', False, f'exception {exc}')
    # 3 licenses
    lic = os.path.join(MU, 'LICENSE')
    lic_text = open(lic, encoding='utf-8', errors='replace').read() if os.path.isfile(lic) else ''
    gate('W01-01-LICENSE-MIT', 'MIT' in lic_text and 'Permission is hereby granted, free of charge' in lic_text, 'root LICENSE is MIT text')
    dlic = os.path.join(MU, 'desktop', 'LICENSE')
    dtext = open(dlic, encoding='utf-8', errors='replace').read() if os.path.isfile(dlic) else ''
    gate('W01-01-LICENSE-APACHE', 'Apache License' in dtext and 'Version 2.0' in dtext, 'desktop LICENSE is Apache-2.0')

    # 4 entry points per 19 §3
    entries = {
        'nativeClient(NativeClientContext)': 'desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts',
        'NativeHost': 'desktop/packages/desktop/src/main/nativeHost/NativeHost.ts',
        'nodeFork': 'desktop/packages/desktop/src/main/nativeHost/nodeFork.ts',
        'coding-agent package': 'packages/coding-agent/package.json',
        'kyrn-judge goal check': 'packages/kyrn-judge/src/goal/check.ts',
    }
    found = {}
    for key, hint in entries.items():
        exact = os.path.join(MU, *hint.split('/'))
        if os.path.isfile(exact):
            found[key] = hint
        else:
            pat = hint.split('/')[-1]
            r2 = subprocess.run(['git', 'ls-files', '*' + pat], cwd=MU, capture_output=True, text=True, encoding='utf-8')
            lines = r2.stdout.splitlines()
            found[key] = lines[0] if lines else None
        gate('W01-01-ENTRY-' + key.split('(')[0], found[key] is not None, f'path={found[key]}')
    rpc_args = os.path.join(MU, 'packages', 'coding-agent', 'src', 'cli', 'args.ts')
    rpc_jsonl = os.path.join(MU, 'packages', 'coding-agent', 'src', 'modes', 'rpc', 'jsonl.ts')
    hits = []
    for fp, needle in ((rpc_args, 'rpc'), (rpc_jsonl, 'jsonl')):
        if os.path.isfile(fp) and needle in open(fp, encoding='utf-8', errors='replace').read().lower():
            hits.append(os.path.relpath(fp, MU).replace(os.sep, '/'))
    gate('W01-01-RPC-STDIO', len(hits) == 2, 'tightened rpc stdio entry files: ' + json.dumps(hits))
    aion_lic = os.path.join(MU, 'desktop', 'LICENSE')
    aion_hit = os.path.isfile(aion_lic) and 'AionUi' in open(aion_lic, encoding='utf-8', errors='replace').read()
    tpn = subprocess.run(['git', 'grep', '-l', 'AionUi', '--', 'desktop/LICENSE', 'packages/kyrn-judge/THIRD_PARTY_NOTICES.md', 'README.md'],
                         cwd=MU, capture_output=True, text=True, encoding='utf-8', errors='replace')
    prov_files = [l for l in tpn.stdout.splitlines() if l]
    gate('W01-01-AIONUI-PROVENANCE', bool(aion_hit) and len(prov_files) >= 2, f'explicit AionUi copyright in desktop/LICENSE={aion_hit}, notice files={prov_files}')
    # 5 package scripts and lock presence (no install here; install is a separate bounded step)
    pkgj = os.path.join(MU, 'desktop', 'package.json')
    scripts = []
    if os.path.isfile(pkgj):
        d = json.load(open(pkgj, encoding='utf-8'))
        scripts = sorted((d.get('scripts') or {}).keys())
    locks = [f for f in ('pnpm-lock.yaml', 'package-lock.json', 'yarn.lock', 'bun.lockb')
             if os.path.isfile(os.path.join(MU, f)) or os.path.isfile(os.path.join(MU, 'desktop', f))]
    gate('W01-01-SCRIPTS-LOCKS', bool(scripts) and bool(locks), f'desktop scripts={len(scripts)} locks={locks}')
    status = 'PASS' if not failures else 'FAIL'
    payload = {'check_id': 'W01-01', 'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'mu_head': head, 'remote': rem, 'status': status, 'results': results, 'failures': failures,
               'scope': 'QUALIFICATION_READ_ONLY_REVIEW', 'install_or_build': 'NOT_RUN_THIS_CHECK'}
    ev = record('W01-01', payload)
    print(json.dumps({'status': status, 'evidence': ev, 'failures': failures}, ensure_ascii=False))
    return 0 if status == 'PASS' else 1

def check_w01_02():
    """Run the shared-session harness (Node) and require exit 0 + critical_fail==0."""
    hs = os.path.join(MU, 'shared-session', 'harness.mjs')
    if not os.path.isfile(hs):
        print(json.dumps({'status': 'NOT_IMPLEMENTED', 'reason': 'harness missing'}, ensure_ascii=False))
        return 2
    r = subprocess.run(['node', hs], cwd=MU, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1500)
    res_path = os.path.join(MU, 'shared-session', 'results.json')
    res = json.load(open(res_path, encoding='utf-8')) if os.path.isfile(res_path) else {}
    payload = {'check_id': 'W01-02', 'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'harness_exit_code': r.returncode, 'harness_tail': (r.stdout or '')[-400:],
               'stderr_tail': (r.stderr or '')[-300:], 'results_summary': {
                   'critical_fail': res.get('critical_fail'), 'pass_count': sum(1 for a in res.get('assertions', []) if a['pass']),
                   'total': len(res.get('assertions', [])), 'assertions': res.get('assertions', [])},
               'cost_ledger': res.get('cost_ledger'), 'mode': 'QUALIFICATION_LIVE_MODEL'}
    record('W01-02', payload)
    ok = r.returncode == 0 and res.get('critical_fail') == 0
    print(json.dumps({'status': 'PASS' if ok else 'FAIL', 'evidence': res_path,
                      'critical_fail': res.get('critical_fail')}, ensure_ascii=False))
    return 0 if ok else 1

def check_w01_03():
    """Validate the frozen route decision files structurally against required evidence refs."""
    repo = os.path.abspath(os.path.join(HERE, '..', '..'))
    fails = []
    checks = []
    def need(name, ok, detail=''):
        checks.append({'id': name, 'ok': bool(ok), 'detail': str(detail)[:160]})
        if not ok:
            fails.append(name)
    rt_path = os.path.join(repo, 'execution', 'v2.4', 'route.json')
    rd_path = os.path.join(repo, 'execution', 'v2.4', 'reuse_decisions.json')
    adr_path = os.path.join(repo, 'docs', 'adr', 'ADR-next-v24-route.md')
    if not (os.path.isfile(rt_path) and os.path.isfile(rd_path) and os.path.isfile(adr_path)):
        print(json.dumps({'status': 'FAIL', 'missing': [rt_path, rd_path, adr_path]}, ensure_ascii=False))
        return 1
    rt = json.load(open(rt_path, encoding='utf-8'))
    rd = json.load(open(rd_path, encoding='utf-8'))
    adr_text = open(adr_path, encoding='utf-8').read()
    need('route-selected', rt.get('selected_route') == 'MU_FORK', rt.get('selected_route'))
    need('mu-commit', rt.get('mu', {}).get('commit') == '8dfebe36508ac0c2508735bb866756dab9283e74', rt.get('mu', {}).get('commit'))
    need('gates-g01-g07-present', all(k in rt.get('gates_g01_g07', {}) for k in ['G0%d' % i for i in range(1, 8)]), list(rt.get('gates_g01_g07', {})))
    need('jev-not-run-stated', rt.get('jev', {}).get('status') == 'NOT_RUN', rt.get('jev'))
    need('fallback-not-triggered', rt.get('fallback', {}).get('status') == 'NOT_TRIGGERED', rt.get('fallback', {}).get('status'))
    need('provisional-no', rt.get('provisional') == 'NO', rt.get('provisional'))
    need('product-acceptance-not-run', rt.get('product_acceptance') == 'NOT_RUN', rt.get('product_acceptance'))
    need('adr-hashes-route', rt.get('adr_sha256') == hashlib.sha256(open(adr_path, 'rb').read()).hexdigest(), 'adr hash binding')
    need('custom-gap-bounded', 'CUSTOM_GAP' in json.dumps(rd) and 'writer_epoch' in json.dumps(rd), 'gap entries')
    need('reject-and-watch-kept', rd['per_capability']['paperclip']['decision'] == 'REJECT' and rd['per_capability']['judge_jev']['decision'] == 'WATCH', 'negative dispositions preserved')
    need('adr-no-deletion', ('不删除' in adr_text) or ('零删除' in adr_text), 'rollback preserves assets')
    payload = {'check_id': 'W01-03', 'run_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'status': 'PASS' if not fails else 'FAIL', 'checks': checks, 'failures': fails,
               'scope': 'ROUTE_DECISION_STRUCTURAL + evidence refs; independent bootstrap review is separate'}
    record('W01-03', payload)
    print(json.dumps({'status': payload['status'], 'failures': fails}, ensure_ascii=False))
    return 0 if not fails else 1


def run_git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd or os.getcwd(), capture_output=True, text=True, encoding='utf-8', errors='replace').stdout

def _repo():
    return os.path.abspath(os.path.join(HERE, '..', '..'))

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def check_w02_01():
    repo = os.path.abspath(os.path.join(HERE, '..', '..'))
    tp = os.path.join(repo, 'third_party', 'mu')
    checks = []
    def need(cid, ok, detail=''):
        checks.append({'id': cid, 'ok': bool(ok), 'detail': str(detail)[:200]})
    tracked = [f for f in run_git('ls-files', 'third_party/mu', cwd=repo).splitlines() if f]
    up_paths = [l.split(' ', 1)[1] for l in run_git('ls-tree', '-r', '--format=%(objectmode) %(path)', MU_COMMIT, cwd=os.path.join(repo, 'qualification', 'v2.4', 'mu')).splitlines()]
    need('layout-present', set(tracked) == set('third_party/mu/' + p for p in up_paths) and all(os.path.isfile(os.path.join(repo, t)) for t in tracked[:200]), f'tracked==upstream path set ({len(tracked)}), disk sample 200 present')
    gitdir = [r_ for r_, d, fs in os.walk(tp) if '.git' in d]
    gitfile = [os.path.join(r_, '.git') for r_, d, fs in os.walk(tp) if os.path.isfile(os.path.join(r_, '.git'))]
    gitlinks = [l for l in run_git('ls-files', '-s', cwd=repo).splitlines() if l.startswith('160000')]
    need('no-nested-git', not gitdir and not gitfile and not gitlinks, f'dirs={gitdir[:2]} files={gitfile[:2]} gitlinks={gitlinks[:2]}')
    need('no-node_modules', sum(1 for r_, d, fs in os.walk(tp) if 'node_modules' in d) == 0 and not [f for f in tracked if 'node_modules/' in f], 'deps not vendored')
    up_raw = run_git('ls-tree', '-r', '--format=%(objectmode) %(path)', MU_COMMIT, cwd=os.path.join(repo, 'qualification', 'v2.4', 'mu')).splitlines()
    up755 = [l for l in up_raw if l.startswith('100755')]
    idx_modes = {}
    for l in run_git('ls-files', '-s', 'third_party/mu', cwd=repo).splitlines():
        meta, _, path = l.partition('\t')
        idx_modes[path] = meta.partition(' ')[0]
    up_exec = {'third_party/mu/' + l.split(' ', 1)[1] for l in up_raw if l.startswith('100755 ')}
    idx_exec = {p for p, m in idx_modes.items() if m == '100755'}
    need('modes-match-upstream', up_exec == idx_exec, f'exec set diff upstream-only={list(up_exec - idx_exec)[:3]} index-only={list(idx_exec - up_exec)[:3]}')
    man = json.load(open(SPEC_REFS, encoding='utf-8'))
    mism = [e['path'] for e in man['files'] if not (os.path.isfile(os.path.join(tp, *e['path'].split('/'))) and sha256(os.path.join(tp, *e['path'].split('/'))) == e['sha256'])]
    need('commit-declared-equals-tree', not mism, f'spec manifest {len(man["files"])} files vs third_party; mismatch={mism}')
    need('licenses-kept', os.path.isfile(os.path.join(tp, 'LICENSE')) and os.path.isfile(os.path.join(tp, 'desktop', 'LICENSE')), 'MIT + Apache-2.0 present')
    need('upstream-structure', os.path.isfile(os.path.join(tp, 'package.json')) and os.path.isdir(os.path.join(tp, 'packages', 'coding-agent')) and os.path.isdir(os.path.join(tp, 'desktop')), 'workspace layout preserved')
    need('tree-manifest', os.path.isfile(os.path.join(repo, 'third_party', 'mu.MANIFEST.json')), 'reproducible full-tree hash list')
    need('vendored-from-record', os.path.isfile(os.path.join(repo, 'third_party', 'VENDORED_FROM.md')), 'source/commit/method')
    po = json.load(open(os.path.join(repo, 'execution', 'v2.4', 'path_ownership.json'), encoding='utf-8'))
    owners = []
    uniform = all(isinstance(v, dict) and isinstance(v.get('paths'), list) and v.get('owner') for v in po['aliases'].values())
    for v in po['aliases'].values():
        owners += [(p, v['owner']) for p in v['paths']]
    dupes = sorted({p for p, o in owners if [x for x in owners if x[0] == p and x[1] != o]})
    need('ownership-uniform-unique', uniform and not dupes, f'uniform={uniform} dupes={dupes[:3]}')
    clj = json.load(open(os.path.join(repo, 'execution', 'v2.4', 'component_lock.json'), encoding='utf-8'))
    reg_locks = set(clj['single_integrator']['locks'])
    actual_locks = {f for f in run_git('ls-files', 'third_party/mu', cwd=repo).splitlines() if os.path.basename(f).lower() in ('package-lock.json', 'bun.lock', 'bun.lockb', 'yarn.lock', 'pnpm-lock.yaml', 'npm-shrinkwrap.json', 'requirements.lock.txt', 'go.sum') or os.path.basename(f).lower().endswith('.lock')}
    need('locks-fully-registered', actual_locks <= reg_locks, f'unregistered={sorted(actual_locks - reg_locks)[:3]}')
    for reg in ['component_lock.json', 'path_ownership.json', 'patch_inventory.json']:
        p = os.path.join(repo, 'execution', 'v2.4', reg)
        need('registry-' + reg, os.path.isfile(p) and bool(json.load(open(p, encoding='utf-8')).get('schema_version')), reg)
    cl = json.load(open(os.path.join(repo, 'execution', 'v2.4', 'component_lock.json'), encoding='utf-8'))
    need('locks-pinned', 'go' in cl and 'node' in cl and cl.get('mu', {}).get('commit') == MU_COMMIT, 'go/node/mu commit pinned with sha256 refs')
    fails = [c['id'] for c in checks if not c['ok']]
    payload = {'check_id': 'W02-01', 'mode': 'DEVELOPMENT', 'run_at': now_iso(), 'status': 'PASS' if not fails else 'FAIL', 'checks': checks, 'failures': fails}
    record('W02-01', payload)
    print(json.dumps({'status': payload['status'], 'failures': fails}, ensure_ascii=False))
    return 0 if not fails else 1

CHECKS = {'W01-01': check_w01_01, 'W01-02': check_w01_02, 'W01-03': check_w01_03,
          'W02-01': check_w02_01}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-id', required=True)
    a = ap.parse_args()
    # Parent gates never call the historical fixed-path writers or live-provider
    # harness. Their evidence is immutable per invocation and source-bound.
    if a.check_id in ('W01-G01', 'W01-G02', 'W01-G03', 'W01-G04'):
        from parent_gates import run
        sys.exit(run(a.check_id))
    fn = CHECKS.get(a.check_id)
    if fn is None:
        print(json.dumps({'status': 'NOT_IMPLEMENTED', 'check_id': a.check_id}, ensure_ascii=False))
        sys.exit(2)
    if not os.path.isdir(os.path.join(MU, '.git')):
        print(json.dumps({'status': 'BLOCKED', 'reason': 'fixed source absent under qualification/v2.4/mu'}, ensure_ascii=False))
        sys.exit(3)
    sys.exit(fn())

if __name__ == '__main__':
    main()
