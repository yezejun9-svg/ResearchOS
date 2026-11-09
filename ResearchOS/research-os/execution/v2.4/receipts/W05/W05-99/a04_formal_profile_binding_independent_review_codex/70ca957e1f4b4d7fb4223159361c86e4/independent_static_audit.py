"""Independent static closure and byte-inverse audit; no inspected code execution."""
import ast,difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94")
h=json.loads((B/'handoff.json').read_bytes());report=json.loads((B/'report.json').read_bytes())
raws={g:json.loads((B/('public.'+g+'.schema.original.json')).read_bytes()) for g in ['domain','client','persistence']}
src=Path(h['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_bytes();tree=ast.parse(src)
const={}
for n in tree.body:
 if isinstance(n,ast.Assign):
  for target in n.targets:
   if isinstance(target,ast.Name):
    try:const[target.id]=ast.literal_eval(n.value)
    except (ValueError,TypeError):pass
embedded=const['PUBLIC_SCHEMAS']
roots=[('domain','Task'),('domain','Run'),('domain','Artifact'),('client','SessionEvent'),('persistence','Task')]
wanted=set(roots);done=set();derived={g:{} for g in raws};removed=[]
def rewrite(node,g,path):
 if isinstance(node,list):return [rewrite(v,g,path+'/'+str(i)) for i,v in enumerate(node)]
 if not isinstance(node,dict):return node
 out={}
 for k,v in node.items():
  if k=='description':removed.append(path+'/description');continue
  if k=='$ref':
   before,name=v.split('#/$defs/')
   if before not in ('','domain.schema.json'):raise ValueError('Unexpected external schema reference')
   group='domain' if before else g;wanted.add((group,name));out[k]=group+':'+name
  else:out[k]=rewrite(v,g,path+'/'+k)
 return out
while wanted-done:
 g,name=sorted(wanted-done)[0];done.add((g,name));derived[g][name]=rewrite(raws[g]['$defs'][name],g,g+':'+name)
projection=json.loads((B/'public-schema-projection.actual.json').read_bytes())
closure={'count':len(done),'roots':roots,'embedded_matches_current_public_schemas':derived==embedded,'author_projection_matches_independent':projection['projection']==derived,'reachable_definitions':sorted(done),'only_removed_annotations':removed}
inverse=json.loads((B/'source.inverse.actual.json').read_bytes());inverses=[]
for entry in inverse['entries']:
 before=Path(entry['before_ref']['path']).read_bytes();after=Path(entry['after_ref']['path']).read_bytes()
 restore_before=''.join(difflib.restore(entry['ndiff'],1)).encode();restore_after=''.join(difflib.restore(entry['ndiff'],2)).encode()
 bt,at=ast.parse(before),ast.parse(after)
 bd={n.name:n for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};ad={n.name:n for n in at.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed=[name for name in bd if name not in ad or ast.dump(bd[name],include_attributes=False)!=ast.dump(ad[name],include_attributes=False)]
 added=sorted(set(ad)-set(bd));removed_defs=sorted(set(bd)-set(ad))
 inverses.append({'target':entry['target'],'before_pin_match':hashlib.sha256(before).hexdigest()==entry['before_ref']['sha256'] and len(before)==entry['before_ref']['bytes'],'after_pin_match':hashlib.sha256(after).hexdigest()==entry['after_ref']['sha256'] and len(after)==entry['after_ref']['bytes'],'before_restore_exact':before==restore_before,'after_restore_exact':after==restore_after,'changed':changed,'added':added,'removed':removed_defs,'exact_copy':before==after})
 if entry['target']=='ops/ci/runtime_w05_live.py':
  oldsha=report['basis_handoff_ref'];prior=json.loads(Path(oldsha['path']).read_bytes());oldpin=prior['source_pins']['execution/v2.4/formal_profile_w05.py']['sha256'].encode()
  newpin=h['source_pins']['execution/v2.4/formal_profile_w05.py']['sha256'].encode()
  runtime_only_two_pin_replacements=before.count(oldpin)==2 and before.replace(oldpin,newpin)==after
 if entry['target']=='execution/v2.4/formal_profile_w05.py':
  before_globals={}
  for n in bt.body:
   if isinstance(n,ast.Assign):
    for target in n.targets:
     if isinstance(target,ast.Name):
      try:before_globals[target.id]=ast.literal_eval(n.value)
      except (ValueError,TypeError):pass
  prior_constants_unchanged=all(name in const and const[name]==value for name,value in before_globals.items())
  globals_added=sorted(set(const)-set(before_globals))
def deepdiff(a,b,path=''):
 if type(a) is not type(b):return [{'path':path,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':path+'/'+k,'before':a.get(k),'after':b.get(k)})
   else:out+=deepdiff(a[k],b[k],path+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':path,'before_count':len(a),'after_count':len(b)}]
  return [x for i,(x1,x2) in enumerate(zip(a,b)) for x in deepdiff(x1,x2,path+'/'+str(i))]
 return [] if a==b else [{'path':path,'before':a,'after':b}]
control1=json.loads((B/'source-controls.actual.json').read_bytes());control2=json.loads((B/'source-controls.actual.v2.json').read_bytes())
fixture1=json.loads((B/'source-data-controls.fixtures.json').read_bytes());fixture2=json.loads((B/'source-data-controls.fixtures.v2.json').read_bytes())
fnd={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
capture=fnd['verify_capture_bundle'];last=capture.body[-1]
always_raise=isinstance(last,ast.Raise) and isinstance(last.exc,ast.Call) and isinstance(last.exc.args[0],ast.Constant) and last.exc.args[0].value=='OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED'
live=fnd['verify_live_originals']; open_strings=[n.value for n in ast.walk(live) if isinstance(n,ast.Constant) and isinstance(n.value,str) and ('ACTUAL_PRODUCER' in n.value or 'OPEN_A04_' in n.value)]
io=json.loads((B/'original-tool-io.json').read_bytes());observations=io['observations']
io_shape=[{'index':i,'keys':list(v),'tool':v.get('tool'),'result_keys':list(v.get('result',{})) if isinstance(v.get('result'),dict) else None} for i,v in enumerate(observations)]
audit={'schema':'researchos.independent-a04-static-review.v1','closure':closure,'inverses':inverses,'runtime_only_two_pin_replacements':runtime_only_two_pin_replacements,'prior_literal_constants_unchanged':prior_constants_unchanged,'literal_constants_added':globals_added,'author_first_controls':{'count':control1['control_count'],'matched':control1['matched_count'],'mismatches':[x for x in control1['results'] if not x['matched']]},'author_second_controls':{'count':control2['control_count'],'matched':control2['matched_count'],'mismatches':[x for x in control2['results'] if not x['matched']]},'author_fixture_changes':deepdiff(fixture1,fixture2),'author_control_result_changes':deepdiff(control1,control2),'author_controls_source_diff':list(difflib.unified_diff((B/'source_controls.py').read_text(encoding='utf-8').splitlines(),(B/'source_controls.v2.py').read_text(encoding='utf-8').splitlines())),'selector_count':1+len(const['GATES']),'selectors':['A04',*const['GATES']],'last_statement_unconditional_open':always_raise,'four_semantic_open_strings':open_strings,'original_io_shape':io_shape,'original_io_metadata':{k:v for k,v in io.items() if k!='observations'},'no_candidate_imports':True,'sql_calls':0}
with (O/'independent-static-audit.json').open('xb') as f:f.write(json.dumps(audit,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ['original_io_shape','author_control_result_changes','closure','inverses']},ensure_ascii=False))
print(json.dumps({'closure':{k:v for k,v in closure.items() if k!='reachable_definitions'},'inverses':inverses,'io_count':len(observations),'io_first_shape':io_shape[:2]},ensure_ascii=False))

