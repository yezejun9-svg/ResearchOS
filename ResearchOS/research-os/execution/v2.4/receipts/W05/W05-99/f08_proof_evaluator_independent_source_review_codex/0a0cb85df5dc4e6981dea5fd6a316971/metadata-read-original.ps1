@'
import json,pathlib
p=pathlib.Path('execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/inputs')
for name in ('inherited-dependency-callgraph.json','inherited-dependency-patch-contract.json','static-source-audit.json','erratum.registry-table-labels.json','source-registry.generated.json','snapshots/050-source-registry34.exact.json','inputs.before.json','additional-inputs.before.json','final-additional-inputs.before.json'):
 o=json.loads((p/name).read_text(encoding='utf-8'));print('FILE',name)
 if name in ('inputs.before.json','additional-inputs.before.json','final-additional-inputs.before.json'):
  print(json.dumps({'keys':list(o),'summary':{k:v for k,v in o.items() if k not in ('files','inputs','refs')},'vector_count':{k:len(v) for k,v in o.items() if k in ('files','inputs','refs')}},ensure_ascii=True))
 elif 'registry' in name:print(json.dumps(o,ensure_ascii=True)[:19000])
 else:print(json.dumps(o,ensure_ascii=True))
for name in ('failure-origin.019a53.json','failure-origin.aba1eb.json','failure-origin.cd1776.json','failure-origin.d94238.json'):
 print('FILE',name);print((p/name).read_text(encoding='utf-8'))
'@ | python -

