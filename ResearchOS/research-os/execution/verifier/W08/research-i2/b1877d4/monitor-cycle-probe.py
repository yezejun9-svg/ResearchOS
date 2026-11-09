"""Independent SQLite-only delta probe. Never opens product databases or network."""
import hashlib
import json
import pathlib
import sqlite3

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/research-cycle-driver')
OUT = pathlib.Path(__file__).parent
db = sqlite3.connect(':memory:')
db.execute('CREATE TABLE domain_objects(project TEXT,kind TEXT,id TEXT,body TEXT)')
migrations = ['0013_research_cycles.sql', '0018_intent_planning.sql', '0020_research_cycle_work.sql']
hashes = {}
for name in migrations:
    raw = (ROOT / 'migrations/sqlite' / name).read_bytes()
    hashes[name] = hashlib.sha256(raw).hexdigest()
    db.executescript(raw.decode('utf-8-sig'))
results = []
def obj(project, kind, ident):
    db.execute('INSERT INTO domain_objects VALUES(?,?,?,?)', (project,kind,ident,'{}'))
def setup(project, accepted):
    for kind, ident in [('Goal','goal'),('NoProgressRecord','progress'),('ResearchCycle','cycle'),('ResearchCycle','next')]:
        obj(project,kind,ident)
    db.execute('INSERT INTO intent_plan_bindings(project,requirement,submission,actor,raw_hash) VALUES(?,?,?,?,?)', (project,'req','submission','actor','hash'))
    db.execute("UPDATE intent_plan_bindings SET plan_kind='MONITOR',monitor_current=1,monitor_started_at='t',monitor_progress_id='progress',compiled_goal='goal',brief_ref='{}',acceptance_ref='{}',accepted_revision=? WHERE project=?", (accepted,project))
setup('p',1)
setup('q',None)
insert = 'INSERT INTO research_monitor_cycles VALUES(?,?,?,?,?)'
db.execute(insert,('p','cycle','goal','{}','t'))
results.append({'id':'accepted-current-same-project-positive','pass':True})
def denied(name, sql, args=()):
    try:
        db.execute(sql,args)
    except sqlite3.IntegrityError as error:
        results.append({'id':name,'pass':True,'rejection':str(error)})
    else:
        results.append({'id':name,'pass':False})
denied('replace-rejected','INSERT OR REPLACE INTO research_monitor_cycles VALUES(?,?,?,?,?)',('p','cycle','goal','{}','changed'))
denied('update-rejected',"UPDATE research_monitor_cycles SET created_at='changed' WHERE project='p' AND cycle='cycle'")
denied('delete-rejected',"DELETE FROM research_monitor_cycles WHERE project='p' AND cycle='cycle'")
denied('missing-cycle-rejected',insert,('p','missing','goal','{}','t'))
denied('missing-goal-rejected',insert,('p','next','missing','{}','t'))
denied('wrong-plan-rejected',insert,('p','next','goal','{"revision":2}','t'))
denied('unaccepted-plan-rejected',insert,('q','cycle','goal','{}','t'))
obj('p','ResearchCycle','p-only')
denied('cross-project-cycle-rejected',insert,('q','p-only','goal','{}','t'))
db.execute("UPDATE intent_plan_bindings SET monitor_current=0 WHERE project='p'")
results.append({'id':'binding-survives-monitor-retirement','pass':db.execute("SELECT count(*) FROM research_monitor_cycles WHERE project='p' AND cycle='cycle'").fetchone()[0]==1})
denied('retired-monitor-new-binding-rejected',insert,('p','next','goal','{}','t'))
report = {'scope':'SQLITE_IN_MEMORY_NEW_MONITOR_CYCLE_CONSTRAINTS_ONLY','source_commit':'b1877d4a32f15868d19ed9d32f39fc2b6b563db9','sqlite_version':sqlite3.sqlite_version,'recursive_triggers':db.execute('PRAGMA recursive_triggers').fetchone()[0],'migration_sha256':hashes,'checks':results,'passed':all(x['pass'] for x in results),'not_claimed':['business acceptance','native source transport','live provider','whole-suite regression'],'prior_five_constraint_probes':'Not repeated; earlier pre-delta evidence retained in review scope.'}
(OUT/'monitor-cycle-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
