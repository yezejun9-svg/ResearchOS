[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$code=@"
from verify_v2 import con,T,save
a=con(T/'fixture/source-data/researchos.sqlite')
b=con(T/'fixture/restored-data/researchos.sqlite')
def sch(db):return {(t,n):[tbl,sql] for t,n,tbl,sql in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema')}
x,y=sch(a),sch(b)
d={str(k):{'source':x.get(k),'restored':y.get(k)} for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
save('restored-schema-deltas.json',d)
import json
print(json.dumps(d))
"@
[IO.File]::WriteAllText("$PSScriptRoot\schema_delta.py",$code,[Text.UTF8Encoding]::new($false))
python -B -Xutf8 "$PSScriptRoot\schema_delta.py"
$ec=$LASTEXITCODE
@{id='020-web';fullargv=@('web.run','open https://www.sqlite.org/lang_vacuum.html line 20','open https://www.sqlite.org/isolation.html line 20');cwd='D:\作品集\ResearchOS\research-os';relevantenv=@{};nativeexit='not_applicable_web';rawstdout='020-web-result.json';rawstderr='020-web-errors.txt'}|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot\020-web.recipe.json" -Encoding utf8
exit $ec