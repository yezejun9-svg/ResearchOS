"""Complete the sealed REQUEST's original-copy pairing; pure IO/AST only."""
import ast,hashlib,json,difflib
from pathlib import Path
OUT=Path(__file__).resolve().parent
def need(v,m):
    if not v:raise RuntimeError(m)
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
    raw=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/n).open('xb') as f:f.write(raw)
p=OUT/'authorization_gate.current58.v2.proposed.py';raw=p.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode();edits=[]
def change(a,b):
    global text
    a=a.replace('\n',nl);b=b.replace('\n',nl);need(text.count(a)==1,'Exact final source span');text=text.replace(a,b,1);edits.append({'old':a,'new':b})
change("all(type(x) is int for x in t)\n", "all(type(x) is int and x >= 0 for x in t)\n")
change("    current = [cp['revision'],ow['revision'],len(cp['failure_counters'])]\n",
"    copies, originals = request['original_copy_refs'], request['canonical_before']\n"
"    require(type(copies) is list and type(originals) is list and len(copies) == len(originals) == 4 and\n"
"            len(intent['metadata']) == 2 and len(intent['unchanged']) == 2, 'Forward original four layout')\n"
"    original_raw = []\n"
"    for i, canonical in enumerate(CANONICAL):\n"
"        require(bounded_path(originals[i]['path']) == ROOT/canonical and\n"
"                bounded_path(copies[i]['path']) not in [ROOT/x for x in CANONICAL], 'Forward original-copy order/path')\n"
"        raw_original = reader.verify(copies[i])\n"
"        require(hashlib.sha256(raw_original).hexdigest() == originals[i]['sha256'] and\n"
"                len(raw_original) == originals[i]['bytes'], 'Forward original copy digest/size')\n"
"        original_raw.append(raw_original)\n"
"        if i < 2:\n"
"            require(intent['metadata'][i]['path'] == canonical and\n"
"                    reader.verify(intent['metadata'][i]['original_ref']) == raw_original, 'Forward intent/request original metadata bytes')\n"
"        else:\n"
"            require(intent['unchanged'][i-2] == {'path':canonical,'sha256':originals[i]['sha256']},\n"
"                    'Forward unchanged ST/CM original binding')\n"
"    original_cp, original_ow = [strict_json(x) for x in original_raw[:2]]\n"
"    require([original_cp['revision'],original_ow['revision'],len(original_cp['failure_counters'])] == before and\n"
"            all(type(x) is int for x in [original_cp['revision'],original_ow['revision']]) and\n"
"            original_cp['head'] == PARENT, 'Forward original-copy tuple/head')\n"
"    current = [cp['revision'],ow['revision'],len(cp['failure_counters'])]\n")
new=text.encode();ast.parse(new)
oldedits=json.loads((OUT/'gate.edits.json').read_bytes());all_edits=oldedits+edits
reverse=new
for e in reversed(all_edits):need(reverse.count(e['new'].encode())==1,'Final inverse span');reverse=reverse.replace(e['new'].encode(),e['old'].encode(),1)
old=Path(json.loads((OUT/'inputs.before.json').read_bytes())[2]['path']).read_bytes();need(reverse==old,'Final whole inverse')
save('authorization_gate.current58.final.proposed.py',new);save('gate.edits.final.json',all_edits)
save('gate.final.diff',''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='old-fed62',tofile='selected-final')).encode())
scope=json.loads((OUT/'scope.current58.v2.proposed.json').read_bytes());scope['authorization_gate_ref']=ref(OUT/'authorization_gate.current58.final.proposed.py');save('scope.current58.final.proposed.json',scope)
binding=json.loads((OUT/'binding-contract.v2.json').read_bytes());binding['selected_gate_ref']=scope['authorization_gate_ref'];binding['scope_template_ref']=ref(OUT/'scope.current58.final.proposed.json');save('binding-contract.final.json',binding)
sealer=(OUT/'seal.py').read_text(encoding='utf-8')
for a,b in [('authorization_gate.current58.v2.proposed.py','authorization_gate.current58.final.proposed.py'),('scope.current58.v2.proposed.json','scope.current58.final.proposed.json'),('binding-contract.v2.json','binding-contract.final.json'),('gate.edits.json','gate.edits.final.json'),("'gate_edits':3","'gate_edits':5")]:sealer=sealer.replace(a,b)
ast.parse(sealer);save('seal.final.py',sealer.encode())
save('final-addendum.json',{'original_intermediate_preserved':ref(p),'selected_gate':scope['authorization_gate_ref'],'sealed_REQUEST_additional_literal_requirements':['Original request four canonical copy pins pair with intent metadata2 originals and unchanged ST/CM','Nonnegative exact-int forward tuples'],'final_inverse_hunks':len(all_edits),'candidate_calls':0,'new_failure_origins':[],'future_negative_control':'Original-copy substitution or ST/CM original hash mismatch must reject; NOT_RUN'})
print(json.dumps({'gate':scope['authorization_gate_ref'],'scope':ref(OUT/'scope.current58.final.proposed.json'),'inverse_hunks':len(all_edits)},ensure_ascii=False))
