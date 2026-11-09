"""Pure file/hash receipt sealer. Imports no sqlite, executes no process or SQL.
Requires already completed controller/outer files; never reads a live namespace.
"""
import sys
sys.dont_write_bytecode=True
import argparse, json, re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from controller_common import file_ref,verify,raw_json,no_alias,write_json,Stop,require_job,CANDIDATE,BASE,check_closed_evidence,validate_grant
from controller import test_facts

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-root',required=True);ap.add_argument('--result-sha256',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--spec-sha256',required=True);a=ap.parse_args()
 root=no_alias(a.run_root)
 if not re.fullmatch('run-[0-9a-f]{32}',root.name):raise Stop('Exact completed nonce namespace only')
 resultref=file_ref(root/'result.json');spec_ref=file_ref(a.spec)
 if resultref['sha256']!=a.result_sha256 or spec_ref['sha256']!=a.spec_sha256:raise Stop('Final result/spec digest mismatch')
 result=raw_json((root/'result.json').read_bytes());spec=raw_json(Path(a.spec).read_bytes())
 outer=raw_json((root.with_name(root.name+'-outer')/'completion.json').read_bytes());require_job(outer['owned_result'])
 if result['source']!=CANDIDATE or result['base']!=BASE or result.get('first_error') or result.get('finalization_error'):raise Stop('Incomplete/faulted controller result')
 rows=result['results']
 if len(rows)!=49 or [x['id'] for x in rows]!=[x['id'] for x in spec['roster']]:raise Stop('Roster omissions/order mismatch')
 started=raw_json((root/'started.json').read_bytes())
 grant,signed_spec,expected_root=validate_grant(started['grant_ref']['path'],started['grant_ref']['sha256'])
 if expected_root!=root or grant['spec_ref']!=spec_ref or signed_spec!=spec:raise Stop('Seal authority/spec/run substitution')
 holds=[];scenario_pass=0;actual_leaf=0
 for row,planned in zip(rows,spec['roster']):
  if row['state']=='NOT_RUN_RESOURCE_HOLD':
   required=planned['requires_resource']
   if not required or not any(grant['resources'][k] is False for k in required) or row['requirements']!=required or row['actual_native_exit'] is not None:raise Stop('Unjustified resource HOLD')
   holds.append(row);continue
  if row['state']!='PASS_OBSERVED_PENDING_REVIEW' or row['actual_native_exit']!=0:raise Stop('Unqualified result row')
  verify(row['invocation_ref']);verify(row['stdout_ref']);verify(row['stderr_ref'])
  facts=test_facts(Path(row['stdout_ref']['path']).read_bytes(),row['selector'],planned['expected_records'])
  if facts!=row['facts']:raise Stop('Declared facts differ from raw Go records')
  scenario_pass+=1;actual_leaf+=len(facts['actual_leaf_records'])
  for pin in row['closed_copy_refs']:verify(pin)
  if planned['new'] and planned['file'].startswith('internal/domain/'):
   case=Path(row['closed_copy_refs'][0]['path']).parent
   if check_closed_evidence(case,planned)!=row['closed_copy_refs']:raise Stop('Closed file evidence changed')
 for p in sorted((root/'native').glob('*/invocation.json')):
  entry=raw_json(p.read_bytes());verify(entry['stdout_ref']);verify(entry['stderr_ref'])
  native=entry['actual_native_exit']
  require_job(entry['owned_result'],True)
  if type(native) is not int or native!=0 or native!=entry['owned_result']['actual_exit']:raise Stop('Native exit fact mismatch')
 for row in raw_json((root/'inputs.final.json').read_bytes()):verify(row['ref'])
 # A new direct child only; never mutate raw inputs or old seal.
 seal=root/'sealed-readonly';seal.mkdir(exist_ok=False)
 summary={'schema':'researchos.w09.finite-evidence-seal.v1','result_ref':resultref,'spec_ref':spec_ref,'scenario_rows':49,'scenario_rows_with_actual_pass':scenario_pass,'actual_leaf_records':actual_leaf,'holds':holds,'source_acceptance':False,'formal_increment':0,'status':'EVIDENCE_ASSEMBLED_WITH_HOLDS' if holds else 'EVIDENCE_ASSEMBLED_PENDING_NONAUTHOR_REVIEW','SQL_reads_in_sealer':0,'processes_started_in_sealer':0,'old_six_domain_DB_exports':'NOT_AVAILABLE_BY_FROZEN_SOURCE_DESIGN'}
 write_json(seal/'summary.json',summary)
 pins=[]
 for p in root.rglob('*'):
  if p.is_file() and not p.is_relative_to(seal):pins.append(file_ref(p))
 write_json(seal/'manifest.json',{'members':pins,'member_count':len(pins),'old_files_mutated':False})
if __name__=='__main__':main()
