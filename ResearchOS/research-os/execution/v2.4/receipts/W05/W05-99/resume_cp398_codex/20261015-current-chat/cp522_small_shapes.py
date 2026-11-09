import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
s=E/'owned_core_stop_effect_state_revision05_source_codex/20261015-current-chat/candidate-37a1f6d3-final'
m=read(s/'manifest.json')
print('STOP_FIELDS',json.dumps({k:v for k,v in m.items() if k in ['source_commit','source_tree','source_files','source_hashes','worktree','unlogged_readonly_gap','limits']},ensure_ascii=False))
for n in ['command-index.json','failure-ledger.json']:
 v=read(s/n);print(n,json.dumps(v if 'ledger' in n else {'type':type(v).__name__,'count':len(v),'first':v[0] if isinstance(v,list) else dict(list(v.items())[:1])},ensure_ascii=False))
q=E/'online_backup_fixture_qualification_codex/20261015-current-chat'
print('BACKUP_FINAL',json.dumps(read(q/'FINAL-manifest.json'),ensure_ascii=False))
for n in ['source-helper-overlay-manifest.json','capture-index-supplement.json']:
 v=read(q/n);print(n,json.dumps({k:({'type':type(x).__name__,'count':len(x),'first':next(iter(x)) if isinstance(x,dict) else x[:1]} if isinstance(x,(dict,list)) else x) for k,x in v.items()},ensure_ascii=False))
sup=read(q/'capture-index-supplement.json')
for k,v in sup.items():
 if k in ['nonzero_exit_audit','diagnostic_vs_limit','incomplete_capture_rows','initial_path_setup_deviation','initial_path_deviation','bootstrap_capture_gap']:print('SUPDETAIL',k,json.dumps(v,ensure_ascii=False))
