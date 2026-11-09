from pathlib import Path
p=Path(__file__).resolve().parent/'record_product_v1_build10_runtime.py';assert not p.exists();b=p.with_name('record_product_v1_build09_runtime.py').read_bytes()
start=b.index(b'events=[dict(');end=b.index(b';old=list(',start);b=b[:start]+b'events=[]'+b[end:]
for x,y in [(b'build-09',b'build-10'),(b'build09',b'build10'),(b'BUILD09',b'BUILD10'),(b'Build09',b'Build10'),(b'build10.controller',b'build10.controller'),(b'cp656',b'cp661'),(b'revision=656',b'revision=661'),(b'previous_revision=655',b'previous_revision=660'),(b"cp['revision']==655",b"cp['revision']==660"),(b"len(cp['failure_counters'])==2559",b"len(cp['failure_counters'])>=2563"),(b"head==reg['main_head']=='5956907bd640d2d4f4abcb583aeb2520883e97c8'",b"head==reg['main_head']"),(b"reg['source_sha256']['apps/web/src/workbench.css']=='5ef1a169db8c193f77e0410bc9e4ed960ae66752f1bed1387bd2097640900f02'",b"reg['source_sha256']['apps/web/src/workbench.css']==sha(ROOT/'apps/web/src/workbench.css')"),(b'CP655',b'CP660'),(b'visual08',b'visual09'),(b'visual02',b'visual03'),(b'visual01 failures',b'visual01/02 failures')]:
 if x==y:continue
 if x==b'Build09' and x not in b:continue
 assert x in b,x;b=b.replace(x,y)
x=b"mobile_source='Exact1 CSS independently approved and integrated CP660; normal mobile composer flow plus bottom-navigation/safe-area clearance. Existing18 input/draft checks passed. Actual real visual03 still pending.'"
y=b"mobile_source='Exact1 CSS independently approved and integrated CP660; real mobile root flex layout accounts for header and optional banners, content scrolls above safe-area navigation. Composer normal flow retained. Actual visual03 still pending.'";assert x in b;b=b.replace(x,y)
x=b"mxc='Fixed local echo04 actually failed with command syntax error; independent runtime audit archived CP654. Capability/enforcement remain UNDETERMINED/UNVERIFIED; no model retry, permission/config/OS change.'"
y=b"mxc='Fixed local echo04 failed with syntax error; path-only echo05 succeeded. Both independent runtime audits archived CP659, local diagnostic budget2/2 consumed. Split-read enforcement/model/cancel/resume unverified; no model retry or permission/config/OS change.'";assert x in b;b=b.replace(x,y)
x=b"'PRODUCT_V1_MOBILE_CONVERSATION_LAYOUT'";assert x in b;b=b.replace(x,b"'PRODUCT_V1_MOBILE_SCROLL_REGION'")
p.write_bytes(b);compile(b,str(p),'exec');print(p)
