from pathlib import Path
import sqlite3, json, hashlib, sys
wt=Path(sys.argv[1]); out=Path(__file__).resolve().parent
files=sorted((wt/'migrations/sqlite').glob('*.sql')); assert len(files)==20
sql=[p.read_text(encoding='utf-8') for p in files]
results=[]
def record(name,ok,detail=None):
 results.append({'check':name,'pass':bool(ok),'detail':detail})
 if not ok: raise AssertionError(name)
def base():
 db=sqlite3.connect(':memory:')
 for i,s in enumerate(sql[:13]):
  db.executescript(s); db.execute('INSERT INTO schema_migrations(version) VALUES(?)',(i+1,))
 db.execute("INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,origin_summary_json,created_at) VALUES('probe','legacy-cycle','a',1,'fixture','REJECT','legacy one','{}','2000-01-01T00:00:00Z')")
 db.execute("INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,origin_summary_json,created_at) VALUES('probe','legacy-cycle','b',2,'fixture','REJECT','legacy two','{}','2000-01-02T00:00:00Z')")
 db.commit(); return db
def tablemap(db):
 return {r[0]:db.execute('SELECT * FROM "'+r[0]+'"').fetchall() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
def schema(db): return db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
def apply(db): db.executescript('BEGIN;\n'+''.join(s+'\nINSERT INTO schema_migrations(version) VALUES('+str(i+14)+');\n' for i,s in enumerate(sql[13:]))+'COMMIT;')
db=base(); before=tablemap(db); oldcols=[r[1] for r in db.execute('PRAGMA table_info(research_candidate_reviews)')]; apply(db); after=tablemap(db)
new=set(after)-set(before)
record('exact_versions_1_to_20',db.execute('SELECT version FROM schema_migrations ORDER BY version').fetchall()==[(i,) for i in range(1,21)])
record('new_tables_empty_including_sqlite_sequence','sqlite_sequence' in new and all(after[n]==[] for n in new),sorted(new))
added=[r[1] for r in db.execute('PRAGMA table_info(research_candidate_reviews)') if r[1] not in oldcols]
record('exact_three_nullable_review_columns',added==['reviewer_id','review_task_ref','acceptance_ref'] and db.execute('SELECT count(*) FROM research_candidate_reviews WHERE reviewer_id IS NOT NULL OR review_task_ref IS NOT NULL OR acceptance_ref IS NOT NULL').fetchone()==(0,),added)
projected=db.execute('SELECT '+','.join(oldcols)+' FROM research_candidate_reviews').fetchall()
record('legacy_rows_preserved_multiset',sorted(projected)==sorted(before['research_candidate_reviews']))
record('all_other_old_tables_preserved',all(after[t]==rows for t,rows in before.items() if t not in ['schema_migrations','research_candidate_reviews']))
db.close()
db=base(); db.execute('CREATE TABLE research_cycle_work(public_collision_fixture)'); db.commit(); baseline_schema=schema(db); baseline_rows=tablemap(db)
try: apply(db); raise AssertionError('collision was accepted')
except sqlite3.Error as e:
 failure=str(e); db.rollback()
record('late_0020_failure_occurs','research_cycle_work' in failure,failure)
record('late_failure_rolls_back_all_schema',schema(db)==baseline_schema)
record('late_failure_rolls_back_all_rows_versions_and_added_columns',tablemap(db)==baseline_rows)
db.close()
report={'scope':'SQLITE_IN_MEMORY_ONLY','sqlite_version':sqlite3.sqlite_version,'author_go_tests_replayed':False,'provider_calls':0,'native_process_calls':0,'source_commit':'028654b5cbe59ac2651c8536908dd2d8eb9a15e3','migration_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':results}
(out/'sqlite-probe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'pass':len(results),'fail':sum(not r['pass'] for r in results),'sqlite_version':sqlite3.sqlite_version,'new_tables':len(new)},indent=2))
