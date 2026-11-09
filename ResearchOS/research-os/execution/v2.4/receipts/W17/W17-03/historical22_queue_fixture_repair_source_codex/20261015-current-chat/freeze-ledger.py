import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
items=[
 ('build-helper','build-helper.invocation.json','FAIL','unused before variable in historical helper; preserved compiler error'),
 ('build-helper','build-helper-02.invocation.json','PASS','historical helper compiled after using before invariant'),
 ('run-helper','run-helper-01.invocation.json','PASS','historical public commands generated first closed22 DB'),
 ('candidate','candidate-active.invocation.json','FAIL','candidate compile found unused time import'),
 ('candidate','candidate-active2.invocation.json','FAIL','UPGRADE_PATH_OVERLAP: fixture DB parent contained Go TEMP'),
 ('candidate','candidate-active3.invocation.json','FAIL','fixture original DB bytes changed after opening in prior run; introduced exact per-test byte copy'),
 ('run-helper','run-helper-02.invocation.json','PASS','fresh immutable historical DB after prior candidate opened original'),
 ('candidate','candidate-active4.invocation.json','FAIL','historical t.TempDir workspace removed when child exited'),
 ('build-helper','build-helper-03.invocation.json','PASS','helper compiled with stable workspace fixture path'),
 ('run-helper','run-helper-03.invocation.json','PASS','historical fixture generated with stable WorkspaceBinding path'),
 ('candidate','candidate-active5.invocation.json','FAIL','UPGRADE_OPERATIONAL_SHAPE: Project path differed from WorkspaceBinding'),
 ('build-helper','build-helper-04.invocation.json','PASS','helper compiled with Project and WorkspaceBinding path rewrite'),
 ('run-helper','run-helper-04.invocation.json','PASS','historical fixture generated with both path rewrites'),
 ('candidate','candidate-active6.invocation.json','FAIL','UPGRADE_OPERATIONAL_ROW: Project content_hash stale after fixture path rewrite'),
 ('build-helper','build-helper-05.invocation.json','PASS','helper compiled with content hashes recalculated for two fixture operational rows'),
 ('run-helper','run-helper-05.invocation.json','PASS','final historical closed22 fixture generated'),
 ('candidate','candidate-active7.invocation.json','PASS','ActiveQueueRecovery passed with final immutable historical fixture'),
 ('candidate','candidate-adjacent.invocation.json','PASS','Frozen22ProgramLock and NativeCLI passed with 29 pinned historical resources'),
]
entries=[]
for kind,name,status,note in items:
    p=OUT/name
    assert p.is_file(),name
    data=json.loads(p.read_text(encoding='utf-8'))
    exit_code=data.get('native_exit')
    assert (exit_code==0)==(status=='PASS'),name
    entry={'kind':kind,'record_path':str(p),'record_sha256':sha(p),'native_exit':exit_code,'status':status,'diagnosis_or_result':note}
    if kind=='build-helper':
        prefix=name.replace('.invocation.json','')
        for suffix in ('stdout','stderr'):
            raw=OUT/f'{prefix}.{suffix}.raw'
            assert raw.is_file(),raw
            entry[suffix]={'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size}
    elif kind=='candidate':
        prefix=name.replace('.invocation.json','')
        for suffix in ('stdout','stderr'):
            raw=OUT/f'{prefix}.{suffix}.raw'
            assert raw.is_file(),raw
            entry[suffix]={'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size}
    else:
        prefix=name.replace('.invocation.json','')
        for suffix in ('stdout','stderr'):
            raw=OUT/f'{prefix}.{suffix}.raw'
            assert raw.is_file(),raw
            entry[suffix]={'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size}
    entries.append(entry)
result={'schema':'researchos.historical22-fixture-append-only-attempt-ledger.v1','attempt_count':len(entries),'failed_count':sum(e['status']=='FAIL' for e in entries),'passed_count':sum(e['status']=='PASS' for e in entries),'prior_T3_failed_groups_retained_in_original_receipt':True,'prior_T3_failed_groups':['TestConfigurationUpgradeActiveQueueRecovery','TestConfigurationUpgradeFrozen22ProgramLock','TestConfigurationUpgradeNativeCLI'],'entries':entries,'formal_increment':0}
(OUT/'FAILURE-LEDGER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(result['attempt_count'],result['failed_count'],result['passed_count'])
