"""Finite shape and text extraction only; no source functions are invoked."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
e=json.loads((D/'repin-input-extract.json').read_bytes())
ref=e['input_refs']['NF5_blueprint'];raw=Path(ref['path']).read_bytes()
if hashlib.sha256(raw).hexdigest()!=ref['sha256'] or len(raw)!=ref['bytes']:raise ValueError('SEALED_BLUEPRINT_DRIFT')
bp=json.loads(raw)
old=e['candidate_HDF']['before_main_ref']['sha256']
hits=[]
def walk(v,path):
    if type(v) is dict:
        if v.get('sha256')==old:hits.append({'json_path':path,'ref':v})
        for k,x in v.items():walk(x,path+[k])
    elif type(v) is list:
        for i,x in enumerate(v):walk(x,path+[i])
walk(bp,[])
view={'schema':'researchos.w09-nf6-repin-finite-tail-extract.v1','blueprint_old_Main_pin_locations':hits,'choice_common':e['NF5_choice']['common'],'selector_template_fields':{k:list(v) for k,v in e['NF5_choice']['selectors'].items()},'REG5_input_keys':list(e['REG5_inputs']),'REG5_inputs':e['REG5_inputs'],'contract_scope_field_count':len(e['NF5_contract']['scope_required_fields']),'contract_request_field_count':len(e['REG5_contract']['request_required_fields']),'code_evidence':{name:rows for name,rows in e['source_function_evidence'].items() if name in ('REG5_caller','NF5_runtime','BR3_source','NF5_launcher')},'constants':e['source_constant_evidence'],'Rootexecute':False,'currentMainqualified':False,'compiler_3905_checks_rerun':False}
out=D/'repin-finite-tail-extract.json'
with out.open('xb') as f:f.write((json.dumps(view,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'tail_extract_ref':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size},'blueprint_old_Main_pin_locations':hits,'choice_common_non_source21':{k:v for k,v in view['choice_common'].items() if k!='source21'},'REG5_input_keys':list(e['REG5_inputs']),'contract_scope_field_count':view['contract_scope_field_count'],'contract_request_field_count':view['contract_request_field_count'],'available_extracted_function_names':{k:[r['name'] for r in v] for k,v in view['code_evidence'].items()},'Rootexecute':False,'currentMainqualified':False},ensure_ascii=False))
