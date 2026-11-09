import pathlib,json,hashlib
P=pathlib.Path;E=P(__file__).resolve().parent;D=E.parent.parent/'product_host_native_20261028/driver-v2'
F=P('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
if sha(D/'lifecycle.mjs')!='3cb9580b89d16e9f0a65e78368012959a05d4a7564d82822726a38f2874df724':raise RuntimeError('driver drift')
refs=[]
paths=[(D/n,P('driver')/n) for n in ['lifecycle.mjs','run-owned.py','choose-owned-folder.ps1','close-owned-window.ps1','PREPARATION.json','REPORT.md']]
paths += [(F/r,P('framework')/r) for r in ['lib/client/browser.js','lib/server/dispatchers/browserDispatcher.js','lib/server/browser.js','lib/server/chromium/chromium.js','lib/server/transport.js','lib/server/utils/fileUtils.js']]
for p,n in paths:
 raw=p.read_bytes();dest=E/'snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(raw)
 if sha(p)!=sha(dest):raise RuntimeError('snapshot drift')
 refs.append({'path':str(p),'snapshot':str(dest),'sha256':sha(p),'bytes':len(raw)})
(E/'INPUTS.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'files':len(refs),'driver_sha256':sha(D/'lifecycle.mjs')}))
