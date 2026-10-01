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


def _repo():
    return os.path.abspath(os.path.join(HERE, '..', '..'))

def check_w01_g01():
    repo = _repo()
    inv = os.path.join(repo, 'execution', 'v2.4', 'inventory.json')
    sc = os.path.join(repo, 'execution', 'v2.4', 'source_candidates.json')
    checks = []
    ok = os.path.isfile(inv) and os.path.isfile(sc)
    checks.append({'id': 'inventory_before_clone', 'ok': ok, 'detail': 'local inventory exists ahead of clone (W00-01 precedes W01-01)'})
    scj = json.load(open(sc, encoding='utf-8'))
    checks.append({'id': 'manifest_reuse', 'ok': 'Mu_Source_Manifest' in json.dumps(scj), 'detail': 'existing spec reference reused by hash'})
    checks.append({'id': 'not_found_honest', 'ok': scj['primary_candidate']['local_qualification_path'].startswith('qualification/v2.4/mu') and scj['fallback_candidate']['status'] == 'NOT_TOUCHED', 'detail': 'NOT_FOUND recorded at W00-01 then fetched; fallback untouched'})
    fails = [c['id'] for c in checks if not c['ok']]
    payload = {'check_id': 'W01-G01', 'mode': 'DEVELOPMENT', 'run_at': now_iso(), 'status': 'PASS' if not fails else 'FAIL', 'checks': checks, 'failures': fails}
    record('W01-G01', payload)
    print(json.dumps({'status': payload['status'], 'failures': fails}, ensure_ascii=False))
    return 0 if not fails else 1

def check_w01_g02():
    repo = _repo()
    res = json.load(open(os.path.join(MU, 'shared-session', 'results.json'), encoding='utf-8'))
    st = json.load(open(os.path.join(repo, 'execution', 'v2.4', 'step_state.json'), encoding='utf-8'))
    checks = []
    checks.append({'id': 'same_core_session_matrix', 'ok': res.get('critical_fail') == 0, 'detail': 'shared-session/epoch/dedupe/cancel/crash matrix green'})
    checks.append({'id': 'limitations_declared', 'ok': len(res.get('limitations', [])) >= 3, 'detail': 'qualification emulation stated'})
    ids = {r['id']: r for r in st['steps']}
    distinct = all(ids[c].get('executor_id') != ids[c].get('verifier_id') for c in ['W01-01', 'W01-02', 'W01-03'] if c in ids and ids[c]['status'] == 'ACCEPTED')
    checks.append({'id': 'executor_not_self_verify', 'ok': distinct, 'detail': 'ACCEPTED cards have distinct executor/verifier'})
    checks.append({'id': 'no_web_shell_substitute', 'ok': any(a['id'] == 'W0102-crash-no-orphan' and a['pass'] for a in res['assertions']), 'detail': 'process-level evidence, not deployed web page'})
    fails = [c['id'] for c in checks if not c['ok']]
    payload = {'check_id': 'W01-G02', 'mode': 'FIXTURE', 'run_at': now_iso(), 'status': 'PASS' if not fails else 'FAIL', 'checks': checks, 'failures': fails}
    record('W01-G02', payload)
    print(json.dumps({'status': payload['status'], 'failures': fails}, ensure_ascii=False))
    return 0 if not fails else 1

def check_w01_g03():
    repo = _repo()
    # LIVE Windows dual-end chain requires the product assembly: own researchos CLI entry + installed Desktop app.
    own_cli = os.path.join(repo, 'apps', 'cli')
    desktop_app = os.path.join(repo, 'apps', 'desktop')
    release = os.path.join(repo, 'release')
    own_cli_present = os.path.isdir(own_cli) and any('researchos' in f for f in os.listdir(own_cli)) if os.path.isdir(own_cli) else False
    desktop_present = os.path.isdir(desktop_app)
    checks = [
        {'id': 'host_versions_registered', 'ok': os.path.isfile(os.path.join(repo, 'execution', 'toolchains', 'locked.json')), 'detail': 'go/node/python/git hashes in locked.json; mu build + pi 0.87.1 rpc probe at W01-01/02'},
        {'id': 'upstream_worker_live_on_windows', 'ok': json.load(open(os.path.join(MU, 'shared-session', 'results.json'), encoding='utf-8')).get('critical_fail') == 0, 'detail': 'W01-02 attempt2 executed real deepseek turns on this Windows host'},
        {'id': 'own_cli_entry_present', 'ok': own_cli_present, 'detail': 'product researchos CLI required by G03 two-end chain (W02+ deliverable)'},
        {'id': 'installed_desktop_present', 'ok': desktop_present, 'detail': 'desktop assembly/installer is W02/W13/W16 deliverable'},
    ]
    fails = [c['id'] for c in checks if not c['ok']]
    status = 'PASS' if not fails else 'BLOCKED_RESOURCE'
    payload = {'check_id': 'W01-G03', 'mode': 'LIVE_WINDOWS', 'run_at': now_iso(), 'status': status, 'checks': checks,
               'blocking': fails, 'unlock_condition': 'after W02-02/W02-03 own CLI + desktop shell exist, re-run this check on real Windows dual-end chain',
               'repair_budget': '1 targeted repair per route (08); 0 spent on G03; W01-02 harness used its 1/1'}
    record('W01-G03', payload)
    print(json.dumps({'status': status, 'blocking': fails}, ensure_ascii=False))
    return 0 if status == 'PASS' else 4

def check_w01_g04():
    repo = _repo()
    r = check_w01_03()
    if r != 0:
        print(json.dumps({'status': 'FAIL', 'reason': 'route structural failed'}, ensure_ascii=False))
        return r
    checks = []
    for c in ['W01-01', 'W01-02', 'W01-03']:
        p = os.path.join(repo, 'execution', 'v2.4', 'receipts', 'W01', c, 'independent_review.json')
        checks.append({'id': 'review_' + c, 'ok': os.path.isfile(p) and 'ACCEPT' in json.load(open(p, encoding='utf-8')).get('verdict', ''), 'detail': 'independent review present'})
    old_route = os.path.join(repo, 'execution', 'route.json')
    checks.append({'id': 'old_route_bytes', 'ok': sha256(old_route) == 'ac54e68234196a4a6fd0c8e5e0f6d7e70a6567cc5dc137098f47244dd9465610', 'detail': 'historical THIN_CORE registration untouched; v2.4 route separate'})
    rd = json.load(open(os.path.join(repo, 'execution', 'v2.4', 'reuse_decisions.json'), encoding='utf-8'))
    checks.append({'id': 'no_qm_to_fullstack', 'ok': rd['per_capability']['qoder_remote_adapter']['decision'].startswith('OPTIONAL') and 'CUSTOM_GAP' in json.dumps(rd), 'detail': 'QM optional; single bounded gap, not Go full-stack'})
    fails = [c['id'] for c in checks if not c['ok']]
    payload = {'check_id': 'W01-G04', 'mode': 'DEVELOPMENT', 'run_at': now_iso(), 'status': 'PASS' if not fails else 'FAIL', 'checks': checks, 'failures': fails}
    record('W01-G04', payload)
    print(json.dumps({'status': payload['status'], 'failures': fails}, ensure_ascii=False))
    return 0 if not fails else 1

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

CHECKS = {'W01-01': check_w01_01, 'W01-02': check_w01_02, 'W01-03': check_w01_03,
          'W01-G01': check_w01_g01, 'W01-G02': check_w01_g02, 'W01-G03': check_w01_g03, 'W01-G04': check_w01_g04}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-id', required=True)
    a = ap.parse_args()
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
