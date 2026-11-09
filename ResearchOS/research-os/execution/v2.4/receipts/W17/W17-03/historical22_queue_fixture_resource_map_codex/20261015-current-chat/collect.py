"""Read-only historical22 resource inventory; writes only this receipt."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
REPORT=ROOT/'execution/v2.4/receipts/W05/W05-99/backup_regression_resource_readonly_codex/9e4a05cf0d514cfcacd6cfd74acdb609/resource-report.json'
TARGET_FREEZE=ROOT/'execution/v2.4/receipts/W05/W05-99/main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab/programs.freeze.json'
BASELINE=ROOT/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat'
COMMIT='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
TREE='458e375ec2be0b989bb9b9e3d487f969e3c62966'

def ref(path):
    path=Path(path)
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def check_pin(item):
    path=Path(item['path'])
    got=ref(path)
    if got['bytes']!=item['bytes'] or got['sha256']!=item['sha256']:
        raise RuntimeError('resource drift '+str(path))
    return got

def git_probe(oid):
    env=dict(os.environ,GIT_NO_REPLACE_OBJECTS='1')
    argv=['git','-c','maintenance.auto=false','-c','gc.auto=0','cat-file','-t',oid]
    p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
    return {'argv':argv,'cwd':str(ROOT),'exit':p.returncode,
            'stdout':p.stdout.decode(errors='replace').strip(),
            'stderr':p.stderr.decode(errors='replace').strip()}

def main():
    original=json.loads((OLD/'git_source.json').read_bytes())
    assert original['commit']==COMMIT and len(original['files'])==502
    archive=(OLD/'git-archive.stdout').read_bytes()
    assert hashlib.sha256(archive).hexdigest()==original['archive_sha256']
    members={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
        for item in tar:
            if item.isfile():
                members[item.name]=hashlib.sha256(tar.extractfile(item).read()).hexdigest()
    assert members==original['files']
    source=OLD/'frozen_source'
    source_files={p.relative_to(source).as_posix():ref(p) for p in source.rglob('*') if p.is_file()}
    assert set(source_files)==set(original['files'])
    for name,pin in original['files'].items():
        assert source_files[name]['sha256']==pin
    selected=['go.mod','go.sum','internal/domain/client_protocol.go',
        'internal/domain/client_protocol_queue_control.go','internal/domain/backup_queue_upgrade.go',
        'internal/domain/backup_queue_upgrade_test.go','migrations/sqlite/0021_research_pending_windows.sql',
        'migrations/sqlite/0022_client_command_queue.sql','migrations/sqlite/next_v24_sessions.sql',
        'internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json',
        'apps/control/main.go','ops/backup/main.go']
    source_pins={name:source_files[name] for name in selected}
    numbered=sorted((source/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql'))
    assert len(numbered)==22 and numbered[-1].name.startswith('0022_')
    assert not (source/'migrations/sqlite/0023_host_model_configuration.sql').exists()
    assert 'client_command_identities' not in (source/'internal/domain/client_protocol.go').read_text(encoding='utf-8')
    oldbuild=json.loads((OLD/'result.json').read_bytes())
    assert oldbuild['commit']==COMMIT and oldbuild['input_count']==5922 and oldbuild['source_drift'] is False
    vector=json.loads((OLD/'source_before.json').read_bytes())
    assert vector==json.loads((OLD/'source_after.json').read_bytes()) and len(vector)==5922
    mod_inputs=[]
    for name,digest in vector.items():
        if '\\gopath\\pkg\\mod\\' in name.lower() and name.lower().endswith('.mod'):
            item=ref(name)
            assert item['sha256']==digest
            mod_inputs.append(item)
    assert len(mod_inputs)==18
    tool=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
    tool_ref=ref(tool)
    assert tool_ref['sha256']==next(v for k,v in vector.items() if k.lower().endswith('go1.27.1\\go\\bin\\go.exe'))
    report=json.loads(REPORT.read_bytes())
    resources=report['env']
    old_control=check_pin(resources['RESEARCHOS_CONFIGURATION_OLD_CONTROL'])
    target=check_pin(resources['RESEARCHOS_CONFIGURATION_TARGET_PROGRAM'])
    old_root=resources['RESEARCHOS_CONFIGURATION_OLD_ROOT']
    checked_root=[check_pin(item) for item in old_root['members']]
    assert len(checked_root)==27 and old_root['numbered_sql_count']==22
    assert ref(OLD/'old22-control.exe')==old_control
    assert oldbuild['programs']['old22-control.exe']==old_control['sha256']
    old_backup=ref(OLD/'old22-backup.exe')
    assert oldbuild['programs']['old22-backup.exe']==old_backup['sha256']
    assert any(p['path']==target['path'] and p['sha256']==target['sha256'] for p in json.loads(TARGET_FREEZE.read_bytes()))
    gomod=(source/'go.mod').read_text(encoding='utf-8')
    requirements=[]
    for line in gomod.splitlines():
        match=re.match(r'\s*([\w.\-/]+)\s+(v\S+)',line)
        if match: requirements.append({'module':match.group(1),'version':match.group(2)})
    proofs={'commit':git_probe(COMMIT),'tree':git_probe(TREE)}
    assert proofs['commit']['exit']==0 and proofs['commit']['stdout']=='commit'
    assert proofs['tree']['exit']!=0
    build_inputs={name:ref(OLD/name) for name in [
        'build.py','environment.json','git-archive.invocation.json','git_source.json',
        'go-list.invocation.json','go-list.stdout','source_before.json','source_after.json',
        'old22-control.exe.build.invocation.json','old22-backup.exe.build.invocation.json','result.json']}
    future={
      'candidate_test_file':'internal/domain/backup_configuration_upgrade_test.go',
      'isolated_historical_helper_file':'internal/domain/active_queue_fixture_child_test.go (new file only in a separately copied source22 fixture build)',
      'method':'In the isolated pinned source22 package, use queueUpgradeFixture and upgradeQueueMigration with 0022 plus next_v24_sessions, then its own ClientService.Execute to admit goal.start, session.send and control commands. Export a closed SQLite source22 fixture and a structured receipt; the current candidate test opens that fixture and performs 22-to23 UpgradeLocal plus recovery invariant checks.',
      'must_prove':['historical helper built from the 502 pinned source files plus exactly one declared test-only overlay; compile inputs and helper executable hashed',
       'source fixture SQL max numbered version=22, client_command_identities table absent, no schema23 SQL added',
       'public v2 commands accepted by source22 ClientService.Execute with actual idempotency, queue, control and receipt rows; no new-current Service on source22',
       'closed pre-upgrade SQLite hash and row inventory; post-upgrade23 queue, Run, effect and idempotency invariants with no extra external dispatch',
       'single fresh candidate test native exit and raw output, source guards, no skip; preserve original T3 and Main4f baseline failures'],
      'do_not_assume':['old22-control administration binary alone seeds the required active public queue',
       'missing Git tree can be restored from the local Git object store',
       'source22 archive is a complete Git tree rather than the selected 502-file compile inventory']}
    out={'schema':'researchos.historical22-active-queue-resource-map/1',
      'status':'READ_ONLY_RESOURCES_MAPPED_FIXTURE_BUILD_PENDING',
      'historical_commit':COMMIT,'historical_tree':TREE,'git_object_probes':proofs,
      'archive':{**ref(OLD/'git-archive.stdout'),'format':'tar','selected_file_count':len(members),
                 'manifest_archive_sha256':original['archive_sha256'],'tar_matches_manifest':True},
      'archive_manifest':{**ref(OLD/'git_source.json'),'file_count':len(original['files'])},
      'existing_frozen_source':{'root':str(source),'file_count':len(source_files),
                                'matches_archive_manifest':True,'selected_pins':source_pins},
      'source22_schema':{'numbered_sql_count':len(numbered),'last':numbered[-1].name,
                         'schema23_sql_present':False,'client_command_identities_in_old_client_protocol':False},
      'original_build':{'result':ref(OLD/'result.json'),'inputs':build_inputs,
          'source_vector_count':len(vector),'source_before_after_equal':True,
          'historical_build_status':oldbuild['status'],
          'build_argv':[json.loads((OLD/(name+'.build.invocation.json')).read_bytes())['actualargv']
              for name in ('old22-control.exe','old22-backup.exe')]},
      'go_and_modules':{'go_executable':tool_ref,'go_mod':ref(source/'go.mod'),
          'go_sum':ref(source/'go.sum'),'module_requirements':requirements,
          'module_mod_files_live_verified':mod_inputs,
          'historical_input_vector':ref(OLD/'source_before.json'),
          'historical_go_list':ref(OLD/'go-list.stdout'),
          'compiler_vector_paths':len(vector),
          'full_5922_vector_current_revalidation':'PENDING_FRESH_BUILD; only 502 source, Go exe and 18 module .mod files were reread in this task'},
      'reusable_programs':{'old22_control':old_control,'old22_backup':old_backup,
          'frozen_source22_release_root':{'path':old_root['root'],
               'member_count':len(checked_root),'numbered_sql_count':22,
               'manifest_sha256_from_prior_report':old_root['manifest_sha256'],
               'members':checked_root},
          'target23_backup':target,'prior_resource_report':ref(REPORT),
          'target_program_freeze':ref(TARGET_FREEZE)},
      'observed_failure_refs':{'combined_T3':ref(BASELINE/'T3-domain-backup.json'),
          'Main4f_baseline':ref(BASELINE/'T3B-main4f-active-queue.json'),
          'historical_pins_retest':ref(BASELINE/'T3R-historical-pins.json')},
      'minimum_fixture_repair':future,
      'effects':{'source_writes':0,'archive_extractions':0,'new_worktrees':0,
                 'git_object_writes':0,'product_data_reads':0,'formal_increment':0}}
    HERE.mkdir(parents=True,exist_ok=True)
    with (HERE/'RESOURCE-MAP.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps({'resource_map':ref(HERE/'RESOURCE-MAP.json'),
                      'source_files':len(source_files),'module_mods':len(mod_inputs),
                      'missing_tree_exit':proofs['tree']['exit']},ensure_ascii=False))

if __name__=='__main__': main()
