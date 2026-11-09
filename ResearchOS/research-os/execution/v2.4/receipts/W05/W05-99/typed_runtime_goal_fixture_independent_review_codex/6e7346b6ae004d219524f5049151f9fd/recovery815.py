from pathlib import Path
import hashlib, json
v=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd')
p=Path('C:/Users/yqyyds/AppData/Local/Temp/w0599_review_4396.py')
current=p.read_text(encoding='utf-8')
definition="V=B / 'typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd'\n"
original=current.replace(definition,'').replace('from collections import Counter\n','from collections import Counter\n'+definition).replace("    if (V/'checks.json').exists(): raise ValueError('check output already exists; do not overwrite')",'    V.mkdir(parents=True,exist_ok=False)')
with (v/'failed-script.815.py').open('x',encoding='utf-8',newline='') as f: f.write(original)
with (v/'corrected-check.py').open('x',encoding='utf-8',newline='') as f: f.write(current)
with Path('C:/Users/yqyyds/AppData/Local/Temp/w0599_review_check815fixed.py').open('x',encoding='utf-8',newline='') as f: f.write(current)
pending=v/'failure-origin.pending.json'
body=json.loads(pending.read_text(encoding='utf-8'))
body.update({'ordinal':815,'Python_exit':1,'native_exit':None,'failure_script_preservation':'Reconstructed from exact apply_patch deltas after temporary script was edited before allocation response; failed script not rerun.','failed_script_sha256':hashlib.sha256(original.encode('utf-8')).hexdigest()})
with (v/'failure-origin.815.json').open('x',encoding='utf-8',newline='') as f: json.dump(body,f,ensure_ascii=False,indent=2); f.write('\n')
print('815 original IO and reconstructed failed script preserved; corrected script has new path')
