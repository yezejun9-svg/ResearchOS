from verify_v2 import con,T,save
a=con(T/'fixture/source-data/researchos.sqlite')
b=con(T/'fixture/restored-data/researchos.sqlite')
def sch(db):return {(t,n):[tbl,sql] for t,n,tbl,sql in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema')}
x,y=sch(a),sch(b)
d={str(k):{'source':x.get(k),'restored':y.get(k)} for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
save('restored-schema-deltas.json',d)
import json
print(json.dumps(d))