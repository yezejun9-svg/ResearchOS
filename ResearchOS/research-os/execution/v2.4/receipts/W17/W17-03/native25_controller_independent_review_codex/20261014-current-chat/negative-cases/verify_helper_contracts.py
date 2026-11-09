"""Check helper syntax/known public artifact interfaces; executes no new case."""
import ast,hashlib,json,sys
from pathlib import Path
E=Path(__file__).parent;source=E/'review_negative.py';tree=ast.parse(source.read_bytes())
scope={'__name__':'readonly_helper_contract_check'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),str(source),'exec'),scope)
P=E.parent.parent.parent/'native25_actual_root_codex/20261014-current-chat/positive-replay-02'
scope.update(P=P,C=P/'controller',H=P/'harness',case='positive-replay',PURPOSE='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1',hc=json.loads((P/'harness.public.config.json').read_bytes()))
checks={}
for phase in ['release','grant']:checks[phase+'_public_signature_interface']=scope['signature'](phase,True)['signature_verified']
for label,zero in [('03-native',True),('04-replay',False)]:
 inv,request,out,err=scope['broker'](label,'RootProgram',['schema24-to25'],zero);checks[label+'_public_invocation_interface']=True
closed=json.loads((P/'controller/controller.closed.json').read_bytes());scope['verify_guard'](closed['source_guard_cleanup']);checks['closed_guard_interface']=True
read=json.loads((P/'controller/test.invocation.json').read_bytes());scope['verify_job'](read['result'],True);checks['outer_invocation_interface']=True
raw=scope['raw_member'](P/'harness/02-grant.payload.json','options');grant=json.loads((P/'harness/02-grant.payload.json').read_bytes());assert scope['digest'](raw)==grant['binding']['options_sha256'];checks['raw_options_extraction']=True
result={'schema':'researchos.readonly-review-helper-interface-check/1','helper_ref':scope['ref'](source),'checks':checks,'syntax':'PASS','new_negative_cases_run':0,'root_authority_actions':0,'sqlite_reads':0,'public_signature_verification_only':True,'limitations':'Checks existing accepted positive public artifacts and utility interfaces only. No new case config, phase, payload, outcome or closure is accepted.'}
with (E/'helper-interface-check.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=True,indent=2);f.write('\n')
print(json.dumps(result))
