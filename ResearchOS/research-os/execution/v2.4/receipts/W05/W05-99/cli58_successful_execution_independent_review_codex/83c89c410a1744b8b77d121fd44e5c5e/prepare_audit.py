import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
old=P/'cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/audit.v2.py';raw=old.read_bytes();text=raw.decode();changes=[]
def rep(a,b):
 global text
 assert text.count(a)==1,(a[:90],text.count(a))
 text=text.replace(a,b,1);changes.append({'old':a,'new':b})
rep("U='c4f309c5528f5d42be5e7eeb146a20aa'","U='0e298790cd484ec9ba319a379e7e34ed'")
rep("N=P/'integration_codex'/('cli43-fresh-held2-r331-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U","N=P/'integration_codex'/('cli58-fresh-held2-r334-v2-'+U);E=P/'cli58_fresh_compiler_executor_codex'/U;L=P/'cli58_fresh_compiler_launcher_codex'/U")
rep(";completion=read(N/'root-launch.outer-completion.json')",'')
rep(" ck('Root completion supplied SHA',ref(N/'root-launch.outer-completion.json')['sha256']=='8d2b7c842836ded1bdc50b34feb4a74acfa62364040ffe51ceff3acaf6f75f06')\n",'')
rep(", (N,'root-launch.closed.manifest.json','members')",'') if ", (N,'root-launch.closed.manifest.json','members')" in text else rep(",(N,'root-launch.closed.manifest.json','members')",'')
rep(" for k,v in completion.items():\n  if k.endswith('_ref') and isinstance(v,dict) and all(y in v for y in ['path','sha256','bytes']):verify(v)\n",'')
rep(" and completion['underlying_local_failure_count']==0 and [completion[k] for k in ['actual_outer_tool_exit','actual_python_caller_exit','actual_launcher_native_exit','actual_inner_python_native_exit']]==[0,0,0,0]",'')
rep("ck('final compiled rev6 30204',final['revision']==6 and final['file_count']==30204)","ck('final compiled rev6 actual30372',final['revision']==6 and final['file_count']==30372)")
rep("  ck('graph no errors '+name,all(not x.get('Error') and not x.get('DepsErrors') for x in d['packages']))","  ck('graph no errors '+name,all(not x.get('Error') and not x.get('DepsErrors') for x in d['packages']))\n  for actualfile in d['all_referenced_files']: verify(actualfile)")
rep("and mod['before']==mod['after']);modulecount+=1","and mod['before']==mod['after']);verify({'path':str(q),**mod['before']});modulecount+=1")
rep("js[0]['status']==200", "js[0]['status']==0")
rep("ck('current331159509',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[331,159,509])","ck('current334162532',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[334,162,532])")
rep("'qualification':'BOUNDED2_PENDING_REVIEW'","'qualification':'BOUNDED2_PENDING_ROOT_CLOSURE_REVIEW'")
ast.parse(text)
with (O/'audit.py').open('xb') as f:f.write(text.encode())
record={'original_audit_ref':{'path':str(old),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'changes':changes,'reason':'Reuse audited r331 logic against entirely current58 E/L/current artifacts; incorporate proven journal internal status0; do not read or pre-approve missing Root closure. Current actual vector count from sealed inspection. Add actual current hashing of all Go graph refs and observed hFile modules.','candidate_execution':False}
with (O/'audit-adaptation.json').open('xb') as f:f.write((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'changes':len(changes),'audit_sha256':hashlib.sha256(text.encode()).hexdigest(),'bytes':len(text.encode()),'candidate_execution':False}))
