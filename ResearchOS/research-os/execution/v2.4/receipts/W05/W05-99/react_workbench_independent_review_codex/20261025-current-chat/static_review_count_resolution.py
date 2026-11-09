from review_driver import *
import ast,sqlite3
prior=json.loads((E/'STATIC-COMPARISON.json').read_text())
ci=ast.parse((WT/'ops/ci/ui.py').read_text());patterns=ast.literal_eval(next(n.value for n in ast.walk(ci) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='patterns' for t in n.targets)))
authorwt=Path(json.loads((AUTHOR/'SOURCE14-SEAL.json').read_text())['worktree'])
actual=json.loads((E/'CI-SOURCE-MANIFEST.json').read_text());author={p.relative_to(authorwt).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for pattern in patterns for p in authorwt.glob(pattern) if p.is_file()}
extra=sorted(set(actual)-set(author));missing=sorted(set(author)-set(actual))
expected=['execution/commands.json','execution/toolchains/locked.json']
checks=dict(prior['checks']); del checks['CI-571-sources'];checks['CI-author571-review573-precisely-explained']=len(actual)==573 and len(author)==571 and extra==expected and not missing and all(actual[p]==v for p,v in author.items())
save(E/'STATIC-COMPARISON-FINAL.json',dict(checks=checks,author_manifest_entries=len(author),review_manifest_entries=len(actual),review_additional_exact_paths=extra,missing_author_paths=missing,explanation='Author sparse worktree omitted two execution files; own review includes both exact committed inputs. Count mismatch was an over-specific review expectation, not a code defect. Original failed result retained.'))
assert all(checks.values()),checks
ledger('023-static-review-diagnostic','RESOLVED','573 vs author571: two exact committed execution files additionally present; no mismatched common source')
data=ASCII/'real-isolated-01-data';dbs=[p for p in data.rglob('*') if p.suffix in ['.db','.sqlite','.sqlite3']]
save(E/'ISOLATED-DATA-FILES.json',dict(data_dir=str(data),databases=[str(p) for p in dbs],core_sha256=hashlib.sha256((ASCII/'control.exe').read_bytes()).hexdigest()))
results=[]
for db in dbs:
 con=sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True);tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
 counts={t:con.execute('SELECT count(*) FROM "'+t+'"').fetchone()[0] for t in tables if t in ['projects','runs','worker_runs','sessions','tasks','goals']}
 results.append(dict(database=str(db),selected_counts=counts,read_only=True));con.close()
save(E/'ISOLATED-SQLITE-PROOF.json',results)
print(json.dumps(dict(checks=checks,counts=results,browser_checks=len(json.loads((E/'browser-independent-01/report.json').read_text())['checks']),real_checks=len(json.loads((E/'real-isolated-01/report.json').read_text())['checks'])),ensure_ascii=False))
