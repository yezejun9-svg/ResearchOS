import hashlib,json
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
OLD=MAIN/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
SRC=MAIN/'.local/resources/historical22-active-queue-helper-20261015'
DB=MAIN/'.local/builds/historical22-active-queue-helper-20261015/closed-source22-05.sqlite'
record=json.loads((OUT/'closed-source22-05.json').read_text(encoding='utf-8'))
expected=json.loads((OLD/'source_after.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
drift=[]; translated=0
for name,want in expected.items():
    if '\\frozen_source\\' in name:
        path=SRC/Path(name.split('\\frozen_source\\',1)[1])
        translated+=1
    else:path=Path(name)
    if not path.is_file() or sha(path)!=want:
        drift.append({'input':name,'resolved':str(path),'expected':want,'actual':sha(path) if path.is_file() else None})
pins=json.loads((MAIN/'execution/v2.4/receipts/W17/W17-03/historical22_queue_fixture_resource_map_codex/20261015-current-chat/SOURCE-PINS-502.json').read_text(encoding='utf-8'))
pin_drift=[]
for item in pins['files']:
    p=SRC/item['relative_path']
    if not p.is_file() or p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:
        pin_drift.append(item['relative_path'])
helper=SRC/'internal/domain/active_queue_fixture_child_test.go'
exe=MAIN/'.local/builds/historical22-active-queue-helper-20261015/historical22-active-queue-05.test.exe'
dbsha=sha(DB)
result={'prior_compiler_vector':str(OLD/'source_after.json'),'prior_vector_count':len(expected),'translated_source_inputs':translated,'vector_drift':drift,'source_502_drift':pin_drift,'source_502_count':len(pins['files']),'helper_source_sha256':sha(helper),'test_exe_sha256':sha(exe),'closed_db_sha256':dbsha,'closed_db_record_match':record['db_sha256']=='sha256:'+dbsha,'old_git_tree_available':False}
(OUT/'final-input-verification-02.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('prior_vector_count','translated_source_inputs','source_502_count','helper_source_sha256','test_exe_sha256','closed_db_sha256','closed_db_record_match')},ensure_ascii=False))
print('vector_drift',len(drift),'pin_drift',len(pin_drift))
raise SystemExit(0 if not drift and not pin_drift and result['closed_db_record_match'] else 1)
