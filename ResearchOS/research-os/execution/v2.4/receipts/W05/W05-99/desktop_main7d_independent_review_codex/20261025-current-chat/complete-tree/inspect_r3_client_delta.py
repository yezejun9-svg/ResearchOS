import json,pathlib
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree')
def rows(n):return {r['path']:r for r in json.loads((A/f'build-0{n}/client-wire-builder/inputs.before.json').read_bytes())}
old,new=rows(1),rows(2)
print(json.dumps({'old_count':len(old),'new_count':len(new),'changed':[(p,old[p],new[p]) for p in new.keys()&old.keys() if old[p]!=new[p]],'old_only':[old[p] for p in sorted(old.keys()-new.keys())],'new_only':[new[p] for p in sorted(new.keys()-old.keys())]},ensure_ascii=False,indent=2))
