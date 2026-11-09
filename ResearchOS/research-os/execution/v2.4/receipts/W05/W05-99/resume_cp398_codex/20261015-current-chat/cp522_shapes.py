import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); E=R/'execution/v2.4/receipts/W05/W05-99'; B=E/'resume_cp398_codex/20261015-current-chat'
def meta(p):
 v=json.loads(p.read_text(encoding='utf-8-sig')); print('\nSHAPE',p)
 if isinstance(v,dict):
  print(json.dumps({k:{'type':type(x).__name__,'len':len(x) if hasattr(x,'__len__') else None,'sample':x[:2] if isinstance(x,list) else dict(list(x.items())[:2]) if isinstance(x,dict) else x} for k,x in v.items()},ensure_ascii=False))
 else: print(json.dumps({'type':type(v).__name__,'len':len(v),'first':v[:2]},ensure_ascii=False))
br=E/'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat'
v=json.loads((br/'review.json').read_text(encoding='utf-8-sig'))
print('B_REVIEW',json.dumps(v,ensure_ascii=False))
meta(br/'FINAL-manifest.json');meta(br/'command-index.json')
s=E/'owned_core_stop_effect_state_revision05_source_codex/20261015-current-chat'
for p in [s/'candidate-37a1f6d3-final/manifest.json',s/'command-index.json',s/'diagnostic-ledger.json']:
 if p.exists(): meta(p)
print('STOP_TOP',json.dumps([p.name for p in s.iterdir()],ensure_ascii=False))
q=E/'online_backup_fixture_qualification_codex/20261015-current-chat'
for p in [q/'FINAL-manifest.json',q/'source-helper-overlay-manifest.json',q/'command-index.json',q/'capture-index-supplement.json']: meta(p)
print('REGISTRAR_PREAMBLE\n'+'\n'.join((B/'register_cp521.py').read_text(encoding='utf-8-sig').splitlines()[:130]))
