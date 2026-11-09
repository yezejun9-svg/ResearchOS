import ast,difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_json_identity_revision_codex/90e455115bf34f81bd29e601debf511a")
h=json.loads((B/'handoff.json').read_bytes());oh=json.loads(Path(h['basis_source_handoff_ref']['path']).read_bytes());inv=json.loads(Path(h['inverse_ref']['path']).read_bytes())
checks=[]
for item in inv['entries']:
 before=Path(item['before_ref']['path']).read_bytes();after=Path(item['after_ref']['path']).read_bytes()
 bt,at=ast.parse(before),ast.parse(after);bn={n.name:n for n in bt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};an={n.name:n for n in at.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed=[k for k in bn if k not in an or ast.dump(bn[k],include_attributes=False)!=ast.dump(an[k],include_attributes=False)]
 row={'target':item['target'],'before_pin_match':hashlib.sha256(before).hexdigest()==item['before_ref']['sha256'] and len(before)==item['before_ref']['bytes'],'after_pin_match':hashlib.sha256(after).hexdigest()==item['after_ref']['sha256'] and len(after)==item['after_ref']['bytes'],'restore_before':''.join(difflib.restore(item['ndiff'],1)).encode()==before,'restore_after':''.join(difflib.restore(item['ndiff'],2)).encode()==after,'exact_copy':before==after,'changed_definitions':changed,'added_definitions':sorted(set(an)-set(bn)),'deleted_definitions':sorted(set(bn)-set(an))}
 checks.append(row)
 if item['target']=='execution/v2.4/formal_profile_w05.py':
  def literal_nodes(tree):
   return {n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
  bassign,aassign=literal_nodes(bt),literal_nodes(at)
  closure_byte_unchanged=ast.get_source_segment(before.decode(),bassign['PUBLIC_SCHEMAS'])==ast.get_source_segment(after.decode(),aassign['PUBLIC_SCHEMAS'])
  schema=ast.literal_eval(aassign['PUBLIC_SCHEMAS'].value)
  all_existing_assignments_byte_unchanged=all(k in aassign and ast.get_source_segment(before.decode(),v)==ast.get_source_segment(after.decode(),aassign[k]) for k,v in bassign.items())
  added_assignments=sorted(set(aassign)-set(bassign))
  cap=an['verify_capture_bundle'];end=cap.body[-1]
  selector_always_open=isinstance(end,ast.Raise) and isinstance(end.exc,ast.Call) and end.exc.args[0].value=='OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED'
  gates=ast.literal_eval(aassign['GATES'].value)
  four_open=any(isinstance(n,ast.Constant) and n.value=='_ACTUAL_PRODUCER_SEMANTIC_DECODER_REQUIRED' for n in ast.walk(an['verify_live_originals']))
  unchanged_related={name:ast.get_source_segment(before.decode(),bn[name])==ast.get_source_segment(after.decode(),an[name]) for name in ['_database','_jsonl','_event_schema','_schema_value','verify_capture_bundle','_root_pair','_grant_original']}
 if item['target']=='ops/ci/runtime_w05_live.py':
  oldpin=oh['source_pins']['execution/v2.4/formal_profile_w05.py']['sha256'].encode();newpin=h['source_pins']['execution/v2.4/formal_profile_w05.py']['sha256'].encode()
  runtime_pin_only=before.count(oldpin)==2 and before.replace(oldpin,newpin)==after
failure=json.loads((B/'failure-origin.9691d9.json').read_bytes());io=json.loads((B/'original-tool-io.json').read_bytes())
def nested_dicts(x):
 if isinstance(x,dict):
  yield x
  for y in x.values():yield from nested_dicts(y)
 elif isinstance(x,list):
  for y in x:yield from nested_dicts(y)
failure_original_match=any(x==failure['original_result'] for x in nested_dicts(io))
author=json.loads(Path(h['controls_ref']['path']).read_bytes())
author_summary={k:v for k,v in author.items() if k not in ['results','inputs','fixtures','raw_originals'] and not isinstance(v,(dict,list))}
out={'schema':'researchos.a04-json-identity-independent-static-audit.v1','inverses':checks,'profile_exact_three_changed':checks[0]['changed_definitions']==['verify_live_originals','verify_refusal','_database_row'],'profile_exact_two_helpers':checks[0]['added_definitions']==['_current_run','_same_json'],'schema_definition_count':sum(len(x) for x in schema.values()),'schema_closure_byte_unchanged':closure_byte_unchanged,'all_existing_assignments_byte_unchanged':all_existing_assignments_byte_unchanged,'added_assignments':added_assignments,'runtime_two_pin_replacements_only':runtime_pin_only,'unchanged_related_guards':unchanged_related,'six_selectors':['A04',*gates],'last_statement_unconditional_open':selector_always_open,'four_semantic_decoders_open':four_open,'author_failure_677':{'origin_ref':h['new_tool_failure_origin_refs'][0],'original_io_result_matches':failure_original_match,'outer_exit':failure.get('actual_outer_exit'),'metadata_python_exit':failure.get('actual_python_exit'),'native_product_exit':failure.get('actual_native_product_exit'),'has_original_input_result':set(failure)>= {'original_input','original_result'},'missing_IDS_traceback':"NameError: name 'IDS' is not defined" in failure['original_result']['output']},'author_controls_summary':author_summary,'author_failed_script_and_v2_diff':list(difflib.unified_diff((B/'source_controls.py').read_text(encoding='utf-8').splitlines(),(B/'source_controls.v2.py').read_text(encoding='utf-8').splitlines())),'author_controls_reexecuted':False,'SQL_calls':0,'full_candidate_imports':0}
with (O/'static-audit.json').open('xb') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps(out,ensure_ascii=False))

