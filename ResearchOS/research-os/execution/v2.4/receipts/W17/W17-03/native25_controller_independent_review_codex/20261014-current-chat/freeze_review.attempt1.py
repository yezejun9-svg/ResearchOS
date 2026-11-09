import datetime as dt, hashlib, json, subprocess
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W17/W17-03/native25_controller_adaptation_codex/20261014-current-chat'
W=R/'.local/worktrees/schema24-to25-native-20261014'
def ref(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,value):
    with (E/name).open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

checks=json.loads((E/'checks.invocation.json').read_text(encoding='utf-8-sig'))
assert checks['actual_native_exit']==0
pins={name:ref(A/name) for name in ['root_native_pause_migration_controller.py','SOURCE_REPORT.json','manifest.json']}
assert pins['root_native_pause_migration_controller.py']['sha256']=='c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
assert pins['SOURCE_REPORT.json']['sha256']=='49b62b3b8fad2489b8d779ba22f5daee160e2d836be0d58e1ec63e98419ec3fa'
assert pins['manifest.json']['sha256']=='bafd6a40f11ddc8f757abb08a21b5f906b69a97cf7c63e1b20fc11c46734ef67'
members=json.loads((A/'manifest.json').read_bytes())['members']
assert len(members)==13
for item in members:assert ref(Path(item['path']))==item
commands=[]
for args in [['git','-C',str(W),'rev-parse','HEAD'],['git','-C',str(W),'status','--porcelain=v1']]:
    run=subprocess.run(args,capture_output=True)
    commands.append({'argv':args,'actual_native_exit':run.returncode,'stdout':run.stdout.decode(),'stderr':run.stderr.decode()})
    assert run.returncode==0
assert commands[0]['stdout'].strip()=='f80955594bdd0373ae1c961cd02ab6be96f2c196'
assert commands[1]['stdout']==''
write('harness-input-verification.json',{'commands':commands,'source_refs':[ref(W/p) for p in ['AGENTS.md','internal/domain/backup_pause_migration_windows_test.go','internal/recoveryauthority/pause_migration.go','internal/recoveryauthority/enrollment_windows.go','internal/recoveryauthority/migration.go']]})
write('diagnostic-history.json',{
    'purpose':'Preserve unsuccessful read-only discovery commands; no retries erased and no Native failure counter changed.',
    'entries':[
        {'ordinal':1,'actual_native_exit':1,'kind':'MEMORY_SEARCH_NO_MATCH','detail':'rg W17|Native25|Schema24|schema24 against MEMORY.md returned no relevant match; no memory fact used.'},
        {'ordinal':2,'actual_native_exit':1,'kind':'PARENT_PATH_SHORTHAND_NOT_FOUND','diagnostic_excerpt':'rg: D:/.local/worktrees/schema24-to25-native-20261014: IO error for operation on D:/.local/worktrees/schema24-to25-native-20261014: 系统找不到指定的路径。 (os error 3)','resolution':'git worktree list resolved the repository-local path; Root confirmed its earlier shorthand error.'},
        {'ordinal':3,'actual_native_exit':1,'kind':'REVIEWER_READ_RELATIVE_PATH_ERROR','diagnostic_excerpt':'Cannot find path execution/v2.4/receipts/W17/W17-03/native25_controller_adaptation_codex/20261014-current-chat/root_native_pause_migration_controller.py because it does not exist. Cannot index into a null array. rg: ops/recovery_enrollment: 系统找不到指定的文件。 (os error 2)','resolution':'Corrected controller read to absolute path; actual signer source located at internal/recoveryauthority/enrollment_windows.go. No file mutation or Native action in failed command.'}
    ],'excerpts_are_not_full_raw_transcripts':True,'independent_fixture_attempts':1,'independent_fixture_failures':0,
    'author_previous_failure':'Original inverse-count test failure remains in the unchanged 13-member author manifest.'})

report={
    'schema':'researchos.native25-controller-independent-source-review/1',
    'state':'SOURCE_ACCEPTED_LIMITED','at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'reviewer':'codex:/root/native25_controller_review','author':'codex:/root','independent_from_author':True,
    'model_selection':{'assigned_model':'gpt-6-astra','assigned_reasoning':'high','basis':'Parent task and project AGENTS.md architecture/security review policy','runtime_model_identity_independently_verified':False},
    'scope':'Only the exact Root-owned Native25 controller adaptation source gate. Static integration with the exact new harness plus unsigned synthetic controller tests. No actual Native execution acceptance.',
    'source_ref':pins['root_native_pause_migration_controller.py'],
    'author_report_ref':pins['SOURCE_REPORT.json'],'author_manifest_ref':pins['manifest.json'],
    'input_integrity':{'author_manifest_members_verified':13,'full_forward_replacement_groups_verified':14,'drift':False,'old_source_preserved':True,'new_harness_head':commands[0]['stdout'].strip(),'new_harness_clean':True},
    'findings':[],
    'reviewed_contracts':[
        {'contract':'Schema24-to25 protocol and executable integration','controller_lines':[37,216,244,321,367,369,372,564,612],'harness_lines':[434,801,804,824,831,842,849,856,874,908,926,965,1048], 'result':'Distinct config schemas, environment selector, exact test name, domain cwd, fixed current/consumed grant namespace, old SourceBackupProgram pin and use, release/grant sign kinds match actual Go source.'},
        {'contract':'No-tags compile provenance and frozen inputs','controller_lines':[227,236,244,255,257,266,269,292],'result':'Requires -c, one exact -o TestProgram, ./internal/domain, no -tags argv, build cwd/native closure/exit, empty inventory build_tag, actual-test-and-embed declaration, and every declared compiler/product member in FrozenInputs. Real inventory completeness and build environment remain a Root concrete-artifact review obligation.'},
        {'contract':'Root-owned lifetime and read guards','controller_lines':[171,321,341,348,371,385,410,420,471],'result':'One observed-owned helper call spans harness pauses with retained source guard until confirmed worker completion; cancellation and closure outcomes retained. Only static inspection and mocked lifecycle predicates were performed, not OS Job proof.'},
        {'contract':'Concrete Root approval, single signing attempt, separate publication','controller_lines':[525,598,612,625,633,663,682,687,710,715,741,755],'result':'Snapshots do not approve; approval checks exact public payload/config/case/ready/destination/signkind/current Job/native identities; consumed marker precedes signer call; sign API never publishes harness approval; separate publish decision binds reviewed signed bytes/receipt; final fixture release requires independent inspection flags and matching snapshot.'},
        {'contract':'Expired-grant changed handshake','controller_lines':[633,637,642,644],'harness_lines':[1027,1043,1063,1064,1065,1074],'result':'Initially valid grant must be at most 90 seconds for expired negative (ordinary at most 240); both sign and publish prechecks reject elapsed validity. Harness waits until expiry plus one second after signed-document approval. New signer validation therefore can run before expiration; no expired signing bypass was added.'},
        {'contract':'Isolated temp and strict bytes','controller_lines':[98,178,282,648],'harness_lines':[720,724,751,1176],'result':'Existing canonical D repository-local temp proof binds TEMP/TMP and excludes original trial/system paths; revised harness forwards isolated four-key environment. Real local JSON no-clobber and duplicate rejection tested; exact signed-wrapper bytes tested with dummy nonsignature string only.'}
    ],
    'validation':{'test_groups':7,'actual_native_exit':0,'raw_stdout_ref':ref(E/'checks.stdout.raw.txt'),'raw_stderr_ref':ref(E/'checks.stderr.raw.txt'),'invocation_ref':ref(E/'checks.invocation.json'),'test_source_ref':ref(E/'independent_checks.py'),'kind':'UNSIGNED_SYNTHETIC_WITH_EXPLICIT_MOCKS','mocked':['public module loading','controller context in approval/release tests','current phase in approval/release tests','held Job observations','native file identity values','read guard during synthetic fixture release'],'not_invoked':['serve','sign_reviewed','real harness','Root executable','Control executable','enrollment signer','broker']},
    'limits_and_remaining_gates':[
        'This accepts only the exact controller source hash. It grants no authority to invoke Native, provision or access keys, sign a payload, publish actual approvals, or migrate a database.',
        'Root must still review each fresh concrete config, old24 producer identity/release inputs, exact compiler inventory, actual no-tags Go build environment including GOFLAGS, successful build provenance, test executable pins, genuine loaded helpers, and source guards. Controller validates supplied public evidence; it does not independently regenerate compiler inventory or prove binary provenance.',
        'Every actual release/grant payload and signed result needs the existing separate Root decision. Synthetic snapshot/Job/native-ID mocks are not Windows isolation or authorization evidence.',
        'Fixture hold is subject to inherited finite deadlines: harness context 20 minutes, owned helper 1260 seconds, Go timeout 25 minutes. Independent Root inspection and explicit release must occur while held; hard kill/timeout cannot promise retained on-disk fixture or accepted completion.',
        'Real final fixture whole-row/schema inspection, Job/handle closure, Native rejection/positive/replay evidence and cleanup remain unexecuted in this review.',
        'Controller intentionally accepts the nine Native cases, not public-handoff-only, whose harness branch bypasses retained fixture cleanup review.'
    ],
    'private_keys_read':0,'signatures_created':0,'native_harness_runs':0,'real_product_database_reads':0,'real_product_database_writes':0,'provider_requests':0,
    'formal_increment':0,'formal_accepted_cases':'0/42','parent_tasks_open':22,
    'writes':'Only this new independent evidence directory plus one self-owned empty .local temp directory; the empty directory was removed with rmdir. No recursive delete, no full worktree/cache copy.',
    'diagnostic_history_ref':ref(E/'diagnostic-history.json'),
    'harness_verification_ref':ref(E/'harness-input-verification.json')
}
write('FINAL-report.json',report)
manifest={'schema':'researchos.native25-controller-independent-evidence-manifest/1','state':report['state'],'reviewer':report['reviewer'],'source_ref':report['source_ref'],'report_ref':ref(E/'FINAL-report.json'),'members':[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json'],'formal_increment':0}
write('manifest.json',manifest)
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json'),'members':len(manifest['members']),'state':report['state']},ensure_ascii=True))
