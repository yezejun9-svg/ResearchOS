from pathlib import Path
O=Path(__file__).resolve().parent
s=(O/'independent_controls.py').read_text(encoding='utf-8')
s=s.replace("'_jsonl','verify_refusal'}","'_jsonl','verify_refusal','verify_live_originals'}")
s=s.replace("kind=s.get('type')","""kind=s.get('type')
 if kind is None and 'allOf' in s:
  v={}
  for child in s['allOf']:
   made=minimal(child,g)
   if isinstance(made,dict):v.update(made)
  return v
 if kind is None and 'properties' in s:return {k:minimal(v,g) for k,v in s['properties'].items()}""")
extra="""
# A composite original-evidence guard control: all transport/event data are synthetic.
# _database is explicitly replaced only here with complete already schema-checked row objects.
# No DB bytes parsed, no SQL called; this does not establish runtime qualification.
def composite(active_run):
 blobs={}
 def ref(name,value,raw=False):
  b=value if raw else encode(value);r={'path':name,'sha256':hashlib.sha256(b).hexdigest()};blobs[name]=b;return r
 def raw(r):
  b=blobs[r['path']]
  if hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('REVIEWER_REF_HASH')
  return b
 doc=lambda r:json.loads(raw(r))
 ctx={'run_id':'composite-evidence'}
 producer=ref('producer',{'synthetic':True})
 scope={'argv':['synthetic-not-run'],'cwd':'D:/synthetic-composite','env_names':[],'initial_tool_input':{'cmd':'synthetic-not-run'},'producer_ref':producer}
 inv={**scope,'native_exit':0}
 closed={'actual_launcher_native_exit':0}
 pair={'tool':'exec_command','input':scope['initial_tool_input'],'result':{'exit_code':0,'output':encode(closed).decode()}}
 pairref=ref('pair',{'schema':'researchos.w05.original-tool-pair.v2','initial':pair,'terminal':copy.deepcopy(pair)})
 jobref=ref('job',{'schema':'researchos.w05.windows-job-original.v2','run_id':ctx['run_id'],'lane':'success','root_tool_pair_ref':pairref,'producer_ref':producer,'native_exit':0,'owned_processes_before':[],'owned_processes_after':[],'pending_requests_after':[],'launch_events':[],'job_closed':True,'cleanup_complete':True})
 dbref=ref('db-mocked-not-sql',b'SYNTHETIC_NOT_SQLITE',raw=True)
 jsonlref=ref('jsonl',stream(ev,dict(final,status='EXECUTION_REPORTED')),raw=True)
 witness={'schema':'researchos.w05.a04-whole-originals.v2','run_id':ctx['run_id'],'lane':'success','product_identity':identity,'root_tool_pair_ref':pairref,'windows_job_ref':jobref,'database_ref':dbref,'jsonl_ref':jsonlref}
 row={'id':'A04-01','lane':'success','product_identity':identity,'original_witness_ref':ref('witness',witness)}
 t=copy.deepcopy(task);t['active_run_id']=active_run
 objects={'Task':t,'TaskRun':run,'Artifacts':{'artifact-independent':artifact},'acceptance_count':0}
 ns['_database']=lambda rawbytes,ident:copy.deepcopy(objects)
 ns['ASSERTION_LANES']={'A04-01':'success'}
 return lambda:ns['verify_live_originals'](doc,raw,ctx,row,inv,scope),{'mocked_database_rows':objects,'real_sql_calls':0,'scope':scope,'invocation':inv,'context':ctx,'row':row,'raw_originals':{k:v.decode() for k,v in blobs.items()}}
for label,active,expect in [('current',identity['run_id'],'ACCEPTED'),('foreign','foreign-current-run','REFUSED')]:
 fn,inputs=composite(active)
 check('COMPOSITE_TASK_ACTIVE_RUN_'+label,expect,fn,inputs)
"""
s=s.replace("out={'schema':",extra+"\nout={'schema':")
s=s.replace("'independent-controls.json'","'independent-controls.v2.json'")
s=s.replace("'selected_functions':sorted(wanted)","'selected_functions':sorted(wanted),'composite_database_stub_controls':2,'fixture_correction':'Reviewer v1 generic constructor did not merge allOf required fields for ArtifactRef and permission payloads. v1 retained unchanged; v2 adds only constructor merge and two explicit composite controls.'")
with (O/'independent_controls.v2.py').open('xb') as f:f.write(s.encode())
print('NEW_V2_SOURCE_CREATED')

