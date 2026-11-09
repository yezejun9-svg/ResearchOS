import sys,json,hashlib,urllib.request,urllib.error,time
from pathlib import Path
from urllib.parse import urlparse
N=Path(__file__).resolve().parent
url,name=sys.argv[1:3]
assert urlparse(url).hostname in {"api.github.com","raw.githubusercontent.com"}
assert "/" not in name and "\\" not in name
p=N/name
assert not p.exists() and not (N/(name+".fetch.json")).exists()
meta=dict(url=url,method="GET",authenticated=False,started=time.time())
try:
 req=urllib.request.Request(url,headers={"User-Agent":"ResearchOS-public-source-audit/1.0","Accept":"application/vnd.github+json" if urlparse(url).hostname=="api.github.com" else "*/*"})
 with urllib.request.urlopen(req,timeout=35) as r:
  raw=r.read(4*1024*1024+1)
  assert len(raw)<=4*1024*1024,"public response exceeds cap"
  meta.update(status=r.status,final_url=r.url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 with p.open("xb") as f:f.write(raw)
 meta["ok"]=True
except Exception as e:
 meta.update(ok=False,error_type=type(e).__name__,error=str(e))
with (N/(name+".fetch.json")).open("x",encoding="utf-8") as f:json.dump(meta,f,ensure_ascii=False,indent=2)
print(json.dumps(meta,ensure_ascii=False))
sys.exit(0 if meta["ok"] else 1)
