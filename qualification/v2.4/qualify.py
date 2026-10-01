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

CHECKS = {'W01-01': check_w01_01, 'W01-02': check_w01_02}

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
