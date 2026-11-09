import json, subprocess
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
def get(p): return json.loads(p.read_bytes())
def git(*args):
 return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=ROOT).decode('utf8').strip()
cp=get(ROOT/'execution/v2.4/checkpoint.json')
print(json.dumps({'checkpoint':cp['revision'],'head':git('rev-parse','HEAD'),'failure_records':len(cp['failure_counters']),'tracked_status':git('status','--porcelain=v1','-uno'),'index':git('diff','--cached','--name-only'),'agents':(ROOT/'AGENTS.md').read_text(encoding='utf8'),'v1_state':get(ROOT/'execution/product-v1/state.json'),'plan_keys':list(get(ROOT/'execution/product-v1/plan.json'))},ensure_ascii=True,indent=2))
