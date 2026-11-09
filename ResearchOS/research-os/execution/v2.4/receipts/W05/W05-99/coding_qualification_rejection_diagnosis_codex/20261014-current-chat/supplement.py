import datetime,json,pathlib,sqlite3,subprocess,hashlib
E=pathlib.Path(__file__).resolve().parent;R=E.parents[6]
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
core='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
captures=[]
for rel in ['internal/domain/client_runtime_setup_windows.go','internal/domain/client_protocol_configuration.go','internal/domain/client_runtime_coding_windows.go','internal/host/runtime_qualification_windows.go','internal/host/runtime_verifier_process_windows.go']:
    p=subprocess.run(['git','show',core+':'+rel],cwd=R,capture_output=True);assert p.returncode==0
    dest=E/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.stdout)
    captures.append(dict(commit=core,path=rel,sha256=hashlib.sha256(p.stdout).hexdigest(),native_exit=p.returncode))
put('additional-source-captures.json',captures)
db=R/'.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite';c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
q={
'unsettled_runs':"SELECT count(*) AS count FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')",
'unsettled_effects':"SELECT count(*) AS count FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')",
'unsettled_dispatches':"SELECT count(*) AS count FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')",
'managed_unsettled':"SELECT count(*) AS count FROM idempotency i LEFT JOIN domain_objects r ON r.project=i.project AND r.kind='Run' AND r.id=json_extract(i.body,'$.run_ref.id') WHERE i.operation='host:managed-runtime-qualification' AND (r.id IS NULL OR coalesce(json_extract(r.body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED') OR EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=i.project AND d.run=r.id AND d.state IN ('PREPARED','STARTED','UNKNOWN')) OR EXISTS(SELECT 1 FROM resource_effects x WHERE x.project=i.project AND x.run=r.id AND x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(x.body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')))"
}
rows={k:[dict(r) for r in c.execute(sql)] for k,sql in q.items()}
c.rollback();c.close();put('live-readonly-global-idle.json',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),database=str(db),uri_mode='ro',query_only=True,transaction='BEGIN/ROLLBACK',queries=q,results=rows,not_checked=['in-memory coordinator worker map and quiesce flags','current provider availability','full protected Host/Owner current gate'],mutations=0,api_requests=0,model_requests=0))
print(json.dumps(rows))
