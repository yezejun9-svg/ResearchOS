"""Resolve two original-format parser ambiguities without rerunning a command."""
import hashlib,json,re,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):assert pin(r['path'])==r;return Path(r['path']).read_bytes()
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
initial=json.loads((N/'prepared-root-input-decision.json').read_bytes());q=json.loads(read(initial['qualification_ref']));w=json.loads(read(initial['witness_ref']));prior=json.loads(read(initial['actual_SourceGuard_ref']))
rows={r['ordinal']:r for r in q['rows']}
refs=[{k:e[k] for k in ('path','sha256','bytes')} for e in prior['entries']]+[pin(__file__),pin(N/'prepared-root-input-decision.json'),initial['checks_ref'],initial['findings_ref'],initial['actual_SourceGuard_ref']]
unique={}
for ref in refs:read(ref);unique[ref['path'].casefold()]=ref
gp=next(r for r in unique.values() if r['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and r['bytes']==11404)
gm=types.ModuleType('seed996_format_closeout_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024);guard.acquire(list(unique.values()))
try:
 d982=json.loads(read(rows[982]['origin_ref']));r982=d982['original_tool_io']['outer_result']
 assert r982['chunk_id']=='ddd584' and r982['exit_code']==1 and d982['actual_outer_exit']==d982['actual_python_exit']==1
 assert 'ROOT_SOURCE_PYTHON_EXIT=1' in r982['output'].splitlines() and 'archive_continuation_observations.root.py' in d982['original_tool_io']['original_call']['input']
 assert rows[982]['actual_outer_exit']==rows[982]['actual_python_exit']==1 and rows[982]['actual_native_exit'] is None
 d988=json.loads(read(rows[988]['origin_ref']));r988=d988['output'];cmd988=d988['input']['cmd']
 assert r988['chunk_id']=='1b770f' and type(r988['exit_code']) is int and r988['exit_code']==1
 assert cmd988.startswith("@'\n") and re.search(r"\n'@ \| & 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3\.14-64/python\.exe' -I -S -B -X utf8 -$",cmd988)
 assert r988['output'].rstrip().endswith('KeyError: 0') and 'Traceback (most recent call last):' in r988['output']
 assert rows[988]['actual_outer_exit']==rows[988]['actual_python_exit']==1 and rows[988]['actual_native_exit'] is None
 add=save('original-format-resolution.json',dict(schema='researchos.seed996-original-format-resolution.v1',original982=dict(origin_ref=rows[982]['origin_ref'],qualified_selector=rows[982]['origin_selector'],resolved_result_pointer='original_tool_io.outer_result',chunk_id='ddd584',outer_exit=1,python_marker='ROOT_SOURCE_PYTHON_EXIT=1',reason='The wrapper also records an earlier successful Get-Content command. The explicit outer_result field selects the original failed Python invocation; sibling output is not another value of this invocation.'),original988=dict(origin_ref=rows[988]['origin_ref'],qualified_selector=rows[988]['origin_selector'],resolved_result_pointer='output',chunk_id='1b770f',outer_exit=1,python_exit_qualification='Direct final PowerShell pipeline invokes only the pinned Python interpreter, with no later shell command; original uncaught KeyError terminates that interpreter. No separate printed numeric marker is claimed.',python_exit=1,native_exit=None),superseded_parser_checks=['original_format_numeric_evidence_982','original_format_numeric_evidence_988'],original_qualification_bytes_changed=False,original_failure_increment=0,commands_rerun=False))
 original_checks=json.loads(read(initial['checks_ref']));resolved=[]
 for c in original_checks['checks']:
  c=dict(c)
  if c['name'] in ('original_format_numeric_evidence_982','original_format_numeric_evidence_988'):c['passed']=True;c['format_resolution_ref']=add
  assert c['passed'] is True;resolved.append(c)
 binding=json.loads(read(w['capture_binding_ref']));raw=read(w['actual_host_capture_ref']);parts=[]
 with Path(binding['source_audit_path']).open('rb') as f:
  for offset,size in zip(binding['source_line_offsets'],binding['source_line_bytes']):f.seek(offset);parts.append(f.read(size))
 assert b''.join(parts)==raw and [hashlib.sha256(b).hexdigest() for b in parts]==binding['original_line_sha256']
 cr=save('prepared-root-input-checks.final.json',dict(schema='researchos.cp370-prepared-root-input-checks.final.v1',checks=resolved,checks_count=len(resolved),prior_checks_ref=initial['checks_ref'],original_format_resolution_ref=add,root_actual_ranges_rechecked=True,rows_complete_966_to_995=True,all_30_original_qualifications_verified=True,formal_acceptance=False,parent_acceptance=False,activation_grant=False))
finally:
 closure=guard.close();gr=save('sourceguard.final-closeout.json',closure)
assert closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors']
fr=save('findings.final.json',dict(blocking_count=0,findings=[],format_parser_limitations_resolved_ref=add))
d=dict(initial);d.update(decision='PREPARED_ROOT_SEED_INPUTS_VERIFIED_NONAUTHORITATIVE',checks_ref=cr,findings_ref=fr,actual_SourceGuard_ref=gr,prior_SourceGuard_ref=initial['actual_SourceGuard_ref'],initial_diagnostic_decision_ref=pin(N/'prepared-root-input-decision.json'),original_format_resolution_ref=add,retained_handles_count=0)
dr=save('prepared-root-input-final-decision.json',d)
for ref in unique.values():read(ref)
mf=save('MF.json',dict(schema='researchos.cp370-prepared-root-input-independent-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hr=save('HDF.json',dict(schema='researchos.cp370-prepared-root-input-independent-handoff.v1',decision=d['decision'],actor_id=d['actor_id'],actor_role=d['actor_role'],manifest_ref=mf,decision_ref=dr,checks_ref=cr,findings_ref=fr,qualification_ref=d['qualification_ref'],witness_ref=d['witness_ref'],actual_SourceGuard_ref=gr,prior_SourceGuard_ref=initial['actual_SourceGuard_ref'],retained_handles_count=0,checks=d['checks'],original_ordinals=[966,995],Root_next_original=996,phase='SEED',activation_grant=False,registrar_SourceAccepted=False,formal_acceptance=False,parent_acceptance=False,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=[],STOP=True,FINAL=True))
print(json.dumps(dict(handoff_ref=hr,manifest_ref=mf,decision_ref=dr,checks_ref=cr,findings_ref=fr,guard_ref=gr,held_refs=len(unique),checks=len(resolved),new_original_failures=[]),ensure_ascii=False))
