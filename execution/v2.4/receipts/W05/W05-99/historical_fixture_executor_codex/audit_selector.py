from pathlib import Path
import json,hashlib,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=ROOT/'internal/domain/backup_upgrade_test.go';before=(HERE/'original_backup_upgrade_test.go.txt').read_bytes();lines=before.splitlines(keepends=True)
prefix=b''.join(lines[:974]);suffix=b''.join(lines[981:]);after=source.read_bytes()
assert after.startswith(prefix) and after.endswith(suffix)
assert sha(source)=='46fd30bba4b2ab2f3438bae151592090ba693a841fde21d71689f42dab7838a4'
raw=(HERE/'valid-artifact/stdout.raw').read_text(encoding='utf-8');events=[json.loads(l) for l in raw.splitlines()];text=''.join(e.get('Output','') for e in events)
assertions=[json.loads(l.split('W17_UPGRADE_ASSERTION ',1)[1]) for l in text.splitlines() if 'W17_UPGRADE_ASSERTION ' in l]
required={'REAL-PROGRAM-13-STARTUP-REJECTED','REAL-CLI-UPGRADE','NEW-PROCESS-HISTORICAL-SCHEMA-VALIDATED-new14','NEW-PROCESS-HISTORICAL-SCHEMA-VALIDATED-original13','REAL-PRODUCT-14-AUTHENTICATED-READ'}
assert required.issubset({a['assertion_id'] for a in assertions}) and assertions and all(a['status']=='PASS' for a in assertions)
report=read(HERE/'selector-report.json');assert report['status']=='PASS' and report['source_vector_equal']
write(HERE/'selector-final-audit.json',{'classification':report['classification'],'status':'PASS_SCOPED_SELECTOR_WITH_EXPECTED_NEGATIVE_REFUSALS','source_sha256':sha(source),'scope_exterior_bytes_preserved':True,'actual_original_assertions':assertions,'required_original_assertion_ids':sorted(required),'original_assertion_count':len(assertions),'assertion_parser_correction':'Initial selector-report.json looked for W17_ASSERTION and left original_assertions empty. This audit parses actual W17_UPGRADE_ASSERTION from unchanged raw; no rerun or source change. Initial report retained.','valid_test':{'exit':0,'pass':1,'fail':0,'skip':0},'negative_tests':[{'name':'missing-artifact','actual_exit':1,'expected_refusal':'historical schema14 artifact read:'},{'name':'wrong-hash-artifact','actual_exit':1,'expected_refusal':'historical schema14 artifact hash mismatch'}],'compilation_and_contract_inputs':report['dependency_count'],'source_vector_equal':True,'source_head_before_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'Q10_closed':False,'four_original_main_failures_retained':True,'formal_or_parent_acceptance':False})
files=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='selector-receipt-manifest.json']
write(HERE/'selector-receipt-manifest.json',{'files':files})
print(json.dumps({'source_sha256':sha(source),'assertions':len(assertions),'final_audit_sha256':sha(HERE/'selector-final-audit.json'),'receipt_files':len(files)},indent=2))
