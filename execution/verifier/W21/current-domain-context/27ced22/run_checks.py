"""Independent R01/R07 checks; writes only beneath this verifier directory."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
TARGET = '27ced22e73da7631d65bdd6e1844de24dd198065'
TESTS = ['TestW04ContextRecovery', 'TestW04RestrictedContext',
         'TestW17C02ProjectIsolation', 'TestW09C19ExplicitOriginAndUnknown',
         'TestW09C19ChainInvalidation', 'TestW09A06HTTPInvalidationAndContext']

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=True).stdout

def source_snapshot():
    tracked = git('ls-files', '-z').decode().split('\0')
    files = [p for p in tracked if p and (
        (p.endswith('.go') and p.split('/')[0] in {'adapters','apps','internal','ops','tests','evaluation'})
        or p in {'go.mod','go.sum','execution/toolchains/locked.json'}
        or p.startswith(('migrations/sqlite/', 'spec/v2.0/contracts/')))]
    result = {}
    for p in sorted(files):
        result[p] = {'sha256': sha(ROOT/p), 'bytes': (ROOT/p).stat().st_size}
    return {'target_commit': TARGET, 'observed_head': git('rev-parse','HEAD').decode().strip(),
            'sampled_at': now(), 'source_files': result,
            'tracked_status': git('status','--porcelain','--untracked-files=no').decode()}

if __name__ == '__main__':
    assert ROOT.name == 'research-os', ROOT
    before = source_snapshot()
    write('source-before.json', before)
    assert before['observed_head'] == TARGET, 'target head changed before test'
    assert not before['tracked_status'], 'tracked files dirty before test'
    write('preflight.json', {
        'status':'SAFE_SELECTED_PUBLIC_FIXTURES', 'checked_at': now(), 'tests':TESTS,
        'reviewed_sources':['internal/domain/context_test.go','internal/domain/retrieval_test.go',
                            'internal/domain/remote_isolation_test.go','internal/domain/domain_test.go'],
        'helper_trace': {
            'context':'contextFixture -> setup -> t.TempDir SQLite/Bootstrap/New; fixture HTTP recorder, generated artifacts and deterministic service acceptance only',
            'restricted':'synthetic zero-byte VERIFIER_ONLY row; Service.Protected is nil; materialization must fail 503; no protected store is opened',
            'C02':'c02Start -> setup + httptest loopback; c02Principal/Materialized/Readback/ProjectDigest use temporary public fixture data; evidence override is this output directory',
            'retrieval':'contextFixture + temporary local roots; w09LocalEvidence captures local files; fixture.example is provenance text, never fetched'},
        'excluded':'No TestMain, no selected exec.Command or native child launch, no model/provider/private helper, no existing live data or blocked cleanup path',
        'filesystem_identity_scope':'Existing local-file Windows identity APIs are exercised by selected retrieval checks; this is not native process qualification'})
    env = os.environ.copy()
    env.update({'GOENV':'off','GOTOOLCHAIN':'local','GOFLAGS':'-mod=readonly',
                'RESEARCHOS_GO':str(GO),'W17_C02_EVIDENCE_DIR':str(OUT/'c02')})
    argv = [str(GO),'test','./internal/domain','-run','^('+'|'.join(TESTS)+')$', '-count=1','-json']
    started = now()
    with (OUT/'go-test.raw.jsonl').open('wb') as stdout, (OUT/'go-test.stderr.log').open('wb') as stderr:
        run = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
    ended = now()
    write('execution.json', {'argv':argv,'cwd':str(ROOT),'started_at':started,'ended_at':ended,'exit_code':run.returncode})
    after = source_snapshot()
    write('source-after.json', after)
    unchanged = before['source_files'] == after['source_files']
    rows = []
    parse_errors = []
    for number,line in enumerate((OUT/'go-test.raw.jsonl').read_text(encoding='utf-8-sig').splitlines(),1):
        try: rows.append((number,json.loads(line)))
        except Exception as e: parse_errors.append({'line':number,'error':str(e)})
    assertions = []
    streams = {}
    for number,row in rows:
        if row.get('Action') != 'output': continue
        key = (row.get('Package'),row.get('Test'))
        pending, first = streams.get(key, ('',number))
        pending += row.get('Output','')
        while '\n' in pending:
            output, pending = pending.split('\n',1)
            for prefix in ('W04_ASSERTION ', 'W09_ASSERTION ', 'W17_C02_ASSERTION '):
                if output.startswith(prefix):
                    a = json.loads(output[len(prefix):])
                    assertions.append({'test':row.get('Test'),'raw_line':first,'raw_end_line':number,'raw':'go-test.raw.jsonl','prefix':prefix.strip(),**a})
            first = number
        streams[key] = (pending,first if pending else number+1)
    write('current-assertions.json', assertions)
    summary = {'argv':argv,'cwd':str(ROOT),'started_at':started,'ended_at':ended,
        'exit_code':run.returncode,'environment':{k:env[k] for k in ('GOENV','GOTOOLCHAIN','GOFLAGS','RESEARCHOS_GO','W17_C02_EVIDENCE_DIR')},
        'go_executable_sha256':sha(GO),'raw_sha256':sha(OUT/'go-test.raw.jsonl'),
        'stderr_sha256':sha(OUT/'go-test.stderr.log'),'source_unchanged':unchanged,
        'source_file_count':len(before['source_files']), 'source_after_head':after['observed_head'],
        'passes':[r['Test'] for _,r in rows if r['Action']=='pass' and r.get('Test')],
        'failures':[r.get('Test',r.get('Package')) for _,r in rows if r['Action']=='fail'],
        'skips':[r.get('Test',r.get('Package')) for _,r in rows if r['Action']=='skip'],
        'assertion_count':len(assertions), 'assertion_ids':[a['assertion_id'] for a in assertions],
        'parse_errors':parse_errors,'formal_status_changed':False,'external_model_provider_calls':0}
    write('command.json', summary)
    print(json.dumps({k:summary[k] for k in ('exit_code','source_unchanged','source_file_count','passes','failures','skips','assertion_count')}, ensure_ascii=False))
    if run.returncode or not unchanged or parse_errors: raise SystemExit(1)
