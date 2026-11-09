from pathlib import Path
import subprocess,json,hashlib,shutil
R=Path(r'D:\作品集\ResearchOS\research-os');E=Path(__file__).parent
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
p=R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json'
baseline=json.loads(p.read_bytes());checked=[]
for x in baseline['protected_source']:
 y=ref(R/x['path']);assert y['sha256']==x['sha256'];checked.append(y)
print('PROTECTED9_OK',len(checked))
old=json.loads((R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/selector-verification.json').read_bytes())
with (E/'selector-live.recipe.json').open('x',encoding='utf8')as f:json.dump({'argv':old['argv'],'cwd':str(R)},f,ensure_ascii=False,indent=2);f.write(chr(10))
r=subprocess.run(old['argv'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(E/'selector-live.stdout.raw').write_bytes(r.stdout);(E/'selector-live.stderr.raw').write_bytes(r.stderr)
v=json.loads(r.stdout);print('SELECTOR_KEYS',list(v));print('SELECTOR_SUMMARY',json.dumps({k:z for k,z in v.items()if k not in ['task','packet','step','next','evidence','candidates']},ensure_ascii=False))
assert r.returncode==0
s={'native_exit':r.returncode,'stdout':ref(E/'selector-live.stdout.raw'),'stderr':ref(E/'selector-live.stderr.raw'),'recipe':ref(E/'selector-live.recipe.json'),'parsed':v,'protected_source':checked}
with (E/'selector-live-verification.json').open('x',encoding='utf8')as f:json.dump(s,f,ensure_ascii=False,indent=2);f.write(chr(10))
for n in ['apps/web/package.json','apps/desktop/package.json']:
 p=R/n;print('PACKAGE',n);print(p.read_text(encoding='utf-8-sig'))
r=subprocess.run(['rg','--files','apps/web','apps/desktop','-g','!**/node_modules/**','-g','!**/dist/**'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('SCOPED_FILES',r.stdout.decode('utf8','replace'));print('FILES_EXIT',r.returncode)
print('DISK_FREE',{'D':shutil.disk_usage('D:/').free,'C':shutil.disk_usage('C:/').free})
