import collections, hashlib, json, subprocess, sys, difflib
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_anchor_revision02_source_codex/20261015-current-chat'
W=R/'.local/worktrees/owned-core-stop-anchor-r2-20261015'
CARD=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp514/owned-core-stop-source-r2-independent-review-scope.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): (E/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def command(label,args):
    result=subprocess.run([sys.executable,'-B','-X','utf8',str(E/'run_logged.py'),'--label',label,'--cwd',str(W),'--',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode: raise RuntimeError(result.stderr.decode())
    return result.stdout
card=read(CARD)
assert sha(CARD)=='46e13d21bbd047fbc75f171844c8fc95bd280fce0428fe0155d75fb79a450146'
manifest=read(A/'candidate-f5db4a96-final/manifest.json')
verified=[]; errors=[]; visited=set()
def refs(obj,base=R):
    if isinstance(obj,dict):
        if isinstance(obj.get('path'),str) and 'sha256' in obj and 'bytes' in obj:
            p=Path(obj['path']); p=p if p.is_absolute() else (R/p if obj['path'].replace('\\','/').startswith('execution/') else base/p)
            key=(str(p),obj['sha256'])
            if key not in visited:
                visited.add(key)
                try:
                    ok=p.stat().st_size==obj['bytes'] and sha(p)==obj['sha256']
                    verified.append({'path':str(p),'sha256':obj['sha256'],'ok':ok})
                    if not ok: errors.append(str(p))
                    # Recurse only the frozen author's Source package. Scope-card
                    # references to older design reviews are verified as inputs,
                    # not an authorization to recursively crawl prior reviews.
                    if p.suffix=='.json' and p.is_relative_to(A): refs(read(p),p.parent)
                except Exception as ex: errors.append(str(p)+': '+repr(ex))
        for x in obj.values(): refs(x,base)
    elif isinstance(obj,list):
        for x in obj: refs(x,base)
refs(card); refs(manifest)
head=command('lineage-head',['git','rev-parse','HEAD','HEAD^{tree}']).decode().splitlines()
assert head==[card['candidate'],card['candidate_tree']]
names=command('lineage-whole19',['git','diff','--name-only',card['main_base'],card['candidate']]).decode().splitlines()
assert sorted(names)==sorted(card['source_allowlist'])
source=[]
for name in names:
    blob=command('lineage-blob-'+str(len(source)),['git','show',card['candidate']+':'+name])
    raw=(W/name).read_bytes()
    # Git may check Windows text out as CRLF; compare normalized source and exact Git blob hash.
    blobid=hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()
    source.append({'path':name,'git_blob_oid':blobid,'git_blob_sha256':hashlib.sha256(blob).hexdigest(),'worktree_sha256':sha(W/name),'normalized_match':raw.replace(b'\r\n',b'\n')==blob})
assert all(x['normalized_match'] for x in source)
for key,base in [('whole19_patch',card['main_base']),('repair_patch',card['repair_base'])]:
    p=manifest[key]; raw=command('lineage-'+key,['git','diff','--binary',base,card['candidate'],'--',*names])
    expected=Path(p['path']).read_bytes()
    write(key+'-comparison.json',{'expected_sha256':hashlib.sha256(expected).hexdigest(),'generated_sha256':hashlib.sha256(raw).hexdigest(),'equal':raw==expected})
index=read(Path(manifest['command_capture_index']['path']))
ledger=read(Path(manifest['failure_ledger']['path']))
nonzero=[]
for rec in ledger['raw_nonzero_command_captures']:
    p=Path(rec['capture']); before=read(p/'before.json'); after=read(p/'after.json')
    out=(p/'stdout.bin').read_text(errors='replace'); err=(p/'stderr.bin').read_text(errors='replace')
    label=p.name; classification='UNCLASSIFIED'; reason=''
    if 'test-compile-grant' in label: classification='TOOL_ENV_ERROR'; reason='GOTMPDIR absent; Go work directory creation failed before compilation'
    elif 'find-securityinfo-api' in label: classification='TOOL_QUERY_ERROR'; reason='rg searched nonexistent unversioned module directory'
    elif 'test-compile-commit' in label: classification='IMPLEMENTATION_TEST_COMPILE_ERROR'; reason='changed journal record layout left test positional literals uncompilable'
    elif 'test-ownedcorestop-r2' in label: classification='TEST_ENV_ERROR'; reason='missing fixture executable and RESEARCHOS_GO for broader native test'
    elif 'ownedcorestop-tests-audit' in label: classification='TOOL_QUERY_ERROR'; reason='unexpanded Windows wildcard passed to rg'
    elif 'fixture-wrong_native' in label: classification='HARNESS_ERROR'; reason='harness parsed empty fail-fast stdout as JSON after correct CLI denial'
    elif 'fixture-wrong_root' in label: classification='HARNESS_ERROR'; reason='harness expected exit1 instead of correct STOP_UNAVAILABLE exit3'
    elif 'test-final-r2-focused' in label: classification='TEST_ENV_ERROR'; reason='wrong fixture environment key and forward-slash TEMP failed canonical-path test'
    elif 'freeze-final-r2' in label: classification='EVIDENCE_TOOL_ERROR'; reason='freezer required mode key absent from early case-result'
    elif err.strip() in ('STOP_GRANT_ACTION_DENIED','STOP_GRANT_EXPIRED','STOP_GRANT_UNCONFIGURED','commit arguments differ from compiled grant','pinned plan subject/authority differs','pinned operation directory identity differs'):
        classification='EXPECTED_DENIAL'; reason=err.strip()
    elif 'cli-concurrent' in label and 'operation already locked' in err: classification='EXPECTED_DENIAL'; reason='concurrent contender denied by exclusive operation lock'
    elif rec['native_exit']==3 and out:
        result=json.loads(out)
        if result['state'] in ('STOP_UNAVAILABLE','STALE_PLAN','STOP_OBSERVED_MAINTENANCE_BLOCKED'):
            classification='EXPECTED_DENIAL_OR_BLOCKED_OUTCOME'; reason=result.get('reason','')
    nonzero.append({**rec,'classification':classification,'reason':reason,'stdout_sha256':sha(p/'stdout.bin'),'stderr_sha256':sha(p/'stderr.bin'),'raw_stdout':out,'raw_stderr':err,'before_sha256':sha(p/'before.json'),'after_sha256':sha(p/'after.json'),'native_exit_verified':after['native_exit']==rec['native_exit']})
counts=dict(collections.Counter(x['classification'] for x in nonzero))
assert len(nonzero)==63 and 'UNCLASSIFIED' not in counts
write('classified-author-nonzero.json',{'schema':'researchos.stop-r2.classified-author-nonzero.v1','total_raw_nonzero_records':len(nonzero),'counts':counts,'records':nonzero,'summary_only_not_additional_failures':ledger['known_harness_corrections'],'historical_capture_gap':ledger['capture_gap'],'three_summary_links':{'wrong_native':['20261015T114815.817601Z-fixture-wrong_native-0eb4f619'],'wrong_root':['20261015T114837.583965Z-fixture-wrong_root-08ef443c'],'final_focused_test':['20261015T115019.416306Z-test-final-r2-focused-85df36e2']}})
captures=index.get('captures',[])
if not captures:
    captures=next(v for v in index.values() if isinstance(v,list))
zeroassert=[]; skipped=[]
for item in captures:
    p=Path(item['directory']); out=(p/'stdout.bin').read_text(errors='replace'); err=(p/'stderr.bin').read_text(errors='replace')
    if '[no tests to run]' in out: zeroassert.append(str(p))
    if '--- SKIP' in out or '--- SKIP' in err: skipped.append(str(p))
write('input-lineage.json',{'card_sha256':sha(CARD),'head':head,'source':source,'referenced_file_count':len(verified),'references':verified,'errors':errors,'capture_count':len(captures),'case_count':len(manifest['fixture_cases']),'zero_assertion_captures':zeroassert,'explicit_skip_captures':skipped,'classified_counts':counts})
diff=''.join(difflib.unified_diff((A/'fixture_e2e_r2.py').read_text().splitlines(True),(E/'fixture_e2e_r2.py').read_text().splitlines(True),fromfile='author/fixture_e2e_r2.py',tofile='review/fixture_e2e_r2.py'))
(E/'copied-harness.diff').write_text(diff,encoding='utf-8')
write('copied-harness-lineage.json',{'original_sha256':sha(A/'fixture_e2e_r2.py'),'derived_sha256':sha(E/'fixture_e2e_r2.py'),'runner_original_sha256':sha(A/'run_logged.py'),'runner_derived_sha256':sha(E/'run_logged.py'),'change':'only four go_env temporary/cache path constants changed; WORKTREE stays frozen','fixture_sha256':sha(E/'fixture-r2.exe')})
print(json.dumps({'references':len(verified),'errors':errors,'sources':len(source),'captures':len(captures),'cases':len(manifest['fixture_cases']),'counts':counts,'zero_assertion_captures':len(zeroassert),'explicit_skips':len(skipped)},ensure_ascii=False))
