from pathlib import Path
import shutil,subprocess,json
R=Path(r'D:\作品集\ResearchOS\research-os')
print('TOOLS',{n:shutil.which(n)for n in ['node','npm','npx','bash','playwright-cli','pwsh']})
node=shutil.which('node')
if node:
 r=subprocess.run([node,'--version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);print('NODE',r.returncode,r.stdout.decode().strip())
for p in [R/'.local/tools',R/'apps/web/node_modules',R/'apps/web/dist',Path(r'C:\Users\yqyyds\.codex\skills\playwright\scripts\playwright_cli.sh')]:
 print('PATH',str(p),'EXISTS',p.exists())
 if p.is_dir()and p.name=='tools':print('CHILDREN',[x.name for x in p.iterdir()])
p=R/'apps/web/src/preview.jsx';print('PREVIEW_SIZE',p.stat().st_size)
