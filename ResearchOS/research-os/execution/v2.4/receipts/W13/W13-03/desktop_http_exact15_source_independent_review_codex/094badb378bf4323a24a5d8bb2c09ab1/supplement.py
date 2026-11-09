from pathlib import Path
import datetime, hashlib, json, re

R = Path('D:/作品集/ResearchOS/research-os')
W = R / '.local/worktrees/codex-w1303-desktop-http-r311'
O = Path(__file__).parent
N = W / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'
F = N / 'final-audit-c0fea60e04e34fbd803b5d2feae78df8'
C = N / 'cohort-e959253f81ad4b5ab7e76c8b9ec30494'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def ref(p):
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def write(name, value):
    with (O/name).open('xb') as f: f.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

checks = []
def check(name, ok, detail=None): checks.append({'check': name, 'ok': bool(ok), 'detail': detail})
matrix = read(O/'input-finite-matrix.json')
corrected = []
for row in matrix['regressions']:
    if row['unit'] != 'node:test leaf': continue
    p = W / row['stdout_ref']['path']; raw = p.read_bytes(); text = raw.decode('utf-8')
    ok = (row['exit'] == 0 and hashlib.sha256(raw).hexdigest() == row['stdout_ref']['sha256']
          and re.search(r'(?:#|ℹ) pass 1(?:\r?\n|$)', text)
          and re.search(r'(?:#|ℹ) fail 0(?:\r?\n|$)', text)
          and re.search(r'(?:#|ℹ) skipped 0(?:\r?\n|$)', text))
    corrected.append({'name':row['name'], 'reporter':'Node default spec (not TAP)', 'stdout_ref':ref(p),
                      'invocation_ref':row['invocation_ref'], 'native_exit':row['exit'], 'corrected_readonly_check':bool(ok)})
    check('default reporter '+row['name'],ok)

base = read(C/'build/inputs.before.json')
key = lambda rows: {x['path']:(x['sha256'],x['bytes']) for x in rows}
base_map = key(base)
vectors=[]
paths=[C/'build/inputs.after.json',F/'inputs.current.json']
paths.extend((W/x['path']).parent/'inputs.after.json' for x in matrix['runs'])
for p in paths:
    rows=read(p)
    same=key(rows)==base_map and all(x.get('current_sha256',x['sha256'])==x['sha256'] for x in rows)
    vectors.append({'ref':ref(p),'count':len(rows),'same_original_full_vector':same})
    check('cohort vector '+str(p),same)

module_rows=read(F/'process-modules.current.json')
module_files={}; modules=[]
for row in module_rows:
    p=W/row['closure_ref']['path']; observed=read(p)
    check('module closure pin '+str(p),ref(p)['sha256']==row['closure_ref']['sha256'])
    file_checks=[]
    for x in observed['files']:
        q=Path(x['path'])
        if str(q) not in module_files: module_files[str(q)]=ref(q)
        current=module_files[str(q)]
        ok=current['sha256']==x['sha256'] and current['bytes']==x['bytes']
        file_checks.append({'original':x,'current':current,'same':ok})
        check('observed process file '+str(q),ok)
    modules.append({'closure_ref':ref(p),'owned_pid':observed['pid'],'start_time':observed['start_time'],'files':file_checks})

supports=[]
for label,p in [
    ('go-json-decode',R/'.local/tools/go1.27.1/go/src/encoding/json/decode.go'),
    ('api-schema-loader',W/'internal/api/v2.go'),
    ('domain-schema-validator',W/'internal/domain/client_protocol_schema.go'),
    ('author-seal',N/'seal_current_v2.py'),
    ('author-build',N/'build_cohort.py'),
    ('author-finite',N/'run_finite_v2.py'),
    ('author-regressions',N/'run_regressions.py')]:
    b=p.read_bytes(); dest=O/(label+'.source')
    with dest.open('xb') as f:f.write(b)
    supports.append({'original_ref':ref(p),'copied_ref':ref(dest)})

source_rows=[]
for row in read(O/'input-source-scope-audit.json')['rows']:
    current=ref(W/row['path']);same=current['sha256']==row['sha256']
    source_rows.append({'path':row['path'],'current':current,'frozen_sha256':row['sha256'],'same':same})
    check('source remains frozen '+row['path'],same)

accounting=read(F/'all-cohorts-accounting.json')
failure_index=read(F/'failure-origins-index.json')
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'operation':'READONLY_BYTES_JSON_AND_STATIC_SOURCE_NO_PRODUCT_EXECUTION',
    'original_collect_audit_ref':ref(O/'collect-audit.json'),
    'original_collect_native_exit':0,
    'reporter_correction':{'original_false_count':5,'cause':'Reviewer applied TAP-only regex to actual default spec reporter; all original checks/raw remain unchanged. No new native/product failure.', 'rows':corrected},
    'cohort_vector_comparisons':vectors,'before_ref':ref(C/'build/inputs.before.json'),
    'observed_process_module_closures':modules,'unique_observed_process_files':len(module_files),
    'module_limit':'Only actually recorded process modules; not proof that every child/late load was individually observed.',
    'support_sources':supports,'final_source_rows':source_rows,
    'author_accounting_ref':ref(F/'all-cohorts-accounting.json'),
    'author_history_result_count':len(accounting['history']),
    'author_failure_index_ref':ref(F/'failure-origins-index.json'),
    'author_failure_index_count':len(failure_index['origins']),
    'checks':checks,'failed_checks':[x for x in checks if not x['ok']],
    'product_execution':False,'source_acceptance':False}
write('supplement-audit.json',report)
print(json.dumps({'supplement':ref(O/'supplement-audit.json'),'checks':len(checks),'failed_checks':len(report['failed_checks']),'module_closures':len(modules),'unique_process_files':len(module_files)},ensure_ascii=False))
