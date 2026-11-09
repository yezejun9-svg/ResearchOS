from pathlib import Path
import hashlib,json,os,subprocess,datetime
Q=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
first=json.loads((Q/'checks01/input.json').read_text(encoding='utf-8'))
old=(Q/'independent-ui.mjs').read_text(encoding='utf-8').replace(
    ")],taskRef)\n assert.ok(JSON.stringify(rows).includes('denied'))",
    ")],task({status:'UNKNOWN',terminal:true}))\n assert.ok(JSON.stringify(rows).includes('denied'))",1)
assert hashlib.sha256(old.encode()).hexdigest()==first['independent_test_sha256']['independent-ui.mjs']
out=Q/'checks02-qa-fixture-correction';out.mkdir(exist_ok=False)
(out/'independent-ui.before-correction.mjs').write_text(old,encoding='utf-8',newline='\n')
manifest=json.loads((Q/'stage01-manifest.json').read_text(encoding='utf-8'))
node=Path(manifest['node']['path']);assert sha(node)==manifest['node']['sha256']
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','PI_','MU_','OPENAI_','ANTHROPIC_','CODEX_')) and k.upper() not in ['NODE_OPTIONS','NODE_PATH']}
env.update(first['environment_overrides'])
argv=[str(node),'--require',str(Q/'guard.cjs'),str(Q/'activity-proof.mjs')]
with (out/'stdout.raw').open('wb') as stdout,(out/'stderr.raw').open('wb') as stderr:
    result=subprocess.run(argv,cwd=Q,env=env,stdout=stdout,stderr=stderr,timeout=60)
row={'action':'QA_FIXTURE_ARGUMENT_CORRECTION_ONLY','cause':'Independent test passed a Task where harnessActivityRows expects TaskRef. No product-source defect.',
 'first_failure_retained':'checks01/independent-ui.stdout.raw','source_tests_before_sha256':first['independent_test_sha256']['independent-ui.mjs'],
 'exact_before_copy_sha256':sha(out/'independent-ui.before-correction.mjs'),'corrected_current_test_sha256':sha(Q/'independent-ui.mjs'),
 'focused_test_sha256':sha(Q/'activity-proof.mjs'),'argv':argv,'cwd':str(Q),'exit_code':result.returncode,
 'stdout_sha256':sha(out/'stdout.raw'),'stderr_sha256':sha(out/'stderr.raw'),'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_sha256_exact10':manifest['source_sha256_exact10'],'product_acceptance_increment':0}
with (out/'result.json').open('x',encoding='utf-8') as f:json.dump(row,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'exit_code':result.returncode,'result_sha256':sha(out/'result.json'),'output':str(out)},ensure_ascii=True))
raise SystemExit(result.returncode)
