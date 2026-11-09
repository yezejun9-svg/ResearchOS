from review_driver import *
import sqlite3
p=ASCII/'real-isolated-01-data/researchos.sqlite';con=sqlite3.connect('file:'+p.as_posix()+'?mode=ro',uri=True)
kind_counts=dict(con.execute('SELECT kind,count(*) FROM domain_objects GROUP BY kind').fetchall())
counts={t:con.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['runtime_dispatches','host_model_configurations','client_sessions']}
con.close()
save(E/'ISOLATED-SQLITE-DOMAIN-PROOF.json',dict(database=str(p),read_only=True,domain_kind_counts=kind_counts,runtime_counts=counts))
assert counts['runtime_dispatches']==0 and counts['host_model_configurations']==0 and counts['client_sessions']==0
assert kind_counts.get('ProjectProfile')==1,kind_counts
print(json.dumps(dict(domain_kind_counts=kind_counts,runtime_counts=counts)))
