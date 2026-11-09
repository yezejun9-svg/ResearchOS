"""Seal readonly source mapping. Does not import or execute inspected candidate code."""
import hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(n,v):
 p=O/n
 with p.open('xb') as f:f.write(enc(v))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
if sys.argv[1]=='audit':
 entries={}
 for p in sorted(O.glob('read-*.json')):
  for x in json.loads(p.read_bytes()):
   entries[(x['path'],x['sha256'])]=x
 checks=[]
 for x in entries.values():
  p=Path(x['path']);snap=Path(x['snapshot']);now=ref(p);s=ref(snap)
  checks.append({**x,'after_sha256':now['sha256'],'after_bytes':now['bytes'],'same':now['sha256']==x['sha256'] and now['bytes']==x['bytes'] and s['sha256']==x['sha256'] and s['bytes']==x['bytes']})
 bad=[x for x in checks if not x['same']]
 put('input-integrity.json',{'schema':'researchos.readonly-input-integrity.v1','input_count':len(checks),'drift_count':len(bad),'complete_original_snapshots':True,'checks':checks})
 report={'schema':'researchos.w05.a04-producer-semantic-interface-map.v1','status':'READONLY_INTERFACE_MAP' if not bad else 'READONLY_INTERFACE_MAP_WITH_SOURCE_DRIFT','author_id':'codex:/root/command_queue_impl','lanes':['A04-03/recovery','A04-04/W05-H08','A04-05/W05-P01','A04-06/W05-U02'],'map_ref':ref(O/'producer-semantic-interface-map.md'),'input_integrity_ref':ref(O/'input-integrity.json'),'original_tools_ref':ref(O/'original-tool-io.json'),'original_input_supplement_ref':ref(O/'original-tool-io-input-supplement.json'),'new_actual_tool_failure_count':1,'failure_ref':ref(O/'failure.origin.8a0dfa.json'),'already_reported_to_root':True,'root_count_at_failure_report':668,'fixed_cut':645,'native_unknown':None,'main_writes':0,'old_source_writes':0,'canonical_writes':0,'candidate_execution_count':0,'go_calls':0,'sql_calls':0,'cli_calls':0,'native_target_calls':0,'sdk_calls':0,'model_calls':0,'network_calls':0,'git_calls':0,'independent_review':None,'source_acceptance':False,'runtime_qualification':False,'formal_case_accepted_delta':0,'all_four_lanes_remain':'OPEN','observed_db_abi_gaps':['Main Run versus A04 TaskRun','Mutable Task/Run content_hash may be SQL NULL'],'snapshot_correction':'Standalone session.snapshot is EVENT_RESYNC_REQUIRED, not initial success; keep fail-closed rejection. Initial snapshot is in operations.result.','frozen_assertions_changed':False}
 put('report.json',report)
 handoff={'schema':'researchos.readonly-interface-handoff.v1','status':report['status'],'report_ref':ref(O/'report.json'),'map_ref':report['map_ref'],'input_integrity_ref':report['input_integrity_ref'],'original_tools_ref':report['original_tools_ref'],'original_input_supplement_ref':report['original_input_supplement_ref'],'failure_ref':report['failure_ref'],'input_count':len(checks),'drift_count':len(bad),'qualification':'NONE','next_action':'Root may review design and separately authorize Source changes; current task stops.','target_execution_authority':None,'no_model_grant':True}
 put('handoff.json',handoff)
 print(json.dumps({'status':report['status'],'input_count':len(checks),'drift_count':len(bad),'handoff_ref':ref(O/'handoff.json'),'report_ref':ref(O/'report.json'),'map_ref':ref(O/'producer-semantic-interface-map.md'),'failure_ref':ref(O/'failure.origin.8a0dfa.json')},ensure_ascii=False))
elif sys.argv[1]=='manifest':
 rows=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
 put('manifest.json',{'schema':'researchos.readonly-audit-manifest.v1','files':rows,'file_count':len(rows),'self_excluded':True,'terminal_tool_observation':'external original manifest sealing input/result; no self-referential seal'})
 print(json.dumps({'manifest_ref':ref(O/'manifest.json'),'file_count':len(rows),'handoff_ref':ref(O/'handoff.json'),'report_ref':ref(O/'report.json'),'map_ref':ref(O/'producer-semantic-interface-map.md')},ensure_ascii=False))
else:raise ValueError('unknown seal stage')

