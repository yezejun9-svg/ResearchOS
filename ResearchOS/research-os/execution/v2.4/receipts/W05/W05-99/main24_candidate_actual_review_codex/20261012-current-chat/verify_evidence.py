import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/w05-main24-public-20261012'
DATA=WT/'execution/v2.4/receipts/W05/W05-99/public23_to24_candidate_integration_codex/candidate-20261012-01'
def ref(p):
    p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(n,o): (OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(r):
    actual=ref(r['path']);checks.append({'expected':r,'actual':actual,'match':r['sha256'].removeprefix('sha256:')==actual['sha256'] and r['bytes']==actual['bytes']})
observations={}
for name in ['build-observations','test-observations','product-observations']:
    obj=read(DATA/(name+'.json'));observations[name]=obj
    rows=obj if isinstance(obj,list) else obj['observations']
    for row in rows:
        for k in ['stdout','stderr','binary']:
            if isinstance(row.get(k),dict):check(row[k])
locked=read(WT/'execution/toolchains/locked.json');go=locked['tools']['go'];actual_go=ref(go['path']);assert go['sha256']==actual_go['sha256']
buildinfo=[]
for p in [WT/'.local/main24-candidate.exe']+[pathlib.Path(x['binary']['path']) for x in observations['build-observations']]:
    cmd=[go['path'],'version','-m',str(p)]
    cp=subprocess.run(cmd,capture_output=True)
    name=p.stem+'.buildinfo.stdout.txt';(OUT/name).write_bytes(cp.stdout)
    settings={}
    for l in cp.stdout.decode().splitlines():
        if l.startswith('\tbuild\t') and '=' in l: k,v=l.split('\tbuild\t',1)[1].split('=',1);settings[k]=v
    buildinfo.append({'argv':cmd,'exit':cp.returncode,'binary':ref(p),'stdout':ref(OUT/name),'settings':settings,'native_platform_qualifiable':settings.get('-trimpath')=='true' and settings.get('CGO_ENABLED')=='0' and settings.get('GOOS')=='windows' and settings.get('GOARCH')=='amd64'})
binding=read(DATA/'binding.candidate-copy.json')
check(binding['producer_stdout']);check(binding['producer_observation'])
old_observation=read(binding['producer_observation']['path']);argv=old_observation['argv']
historical_db=pathlib.Path(argv[argv.index('--db')+1]);historical_backup=pathlib.Path(argv[argv.index('--out')+1])
preservation=[]
for old,new in [(historical_db,DATA/'source23-copy/researchos.sqlite')]+[(historical_backup/n,DATA/'backup23-copy'/n) for n in ['manifest.json','state.sqlite.enc','portable.json.enc','command-queue.json.enc']]:
    a,b=ref(old),ref(new);preservation.append({'historical':a,'copy':b,'byte_identical':a['sha256']==b['sha256'] and a['bytes']==b['bytes']})
tests=[]
for row in observations['test-observations']:
    raw=pathlib.Path(row['stdout']['path']).read_text(encoding='utf-8-sig')
    tests.append({'label':row['label'],'exit':row['exit'],'top_level_passes':[l for l in raw.splitlines() if l.startswith('--- PASS:')],'has_fail':'--- FAIL:' in raw,'result_pass':'\nPASS\n' in raw})
oracle=read(OUT/'sqlite-oracle.json')
empty_business={n:oracle['states']['source23-copy']['tables'].get(n,{}).get('count') for n in ['domain_objects','runtime_dispatches','client_command_queue','runtime_prepared_abandonments']}
write('evidence-checks.json',{'schema':'researchos.independent-main24-evidence-checks.v1','actor':'codex:/root/w05_migration_review','reference_checks':checks,'all_reference_checks_pass':all(c['match'] for c in checks),'go_tool':actual_go,'buildinfo':buildinfo,'test_results':tests,'preservation':preservation,'all_historical_copies_byte_identical':all(c['byte_identical'] for c in preservation),'actual_input_business_counts':empty_business,'original_database_opened':False,'original_database_read_method':'byte hash only; no SQLite connection','private_key_read_or_hashed':False,'product_commands_replayed':False,'native_success_prefix_replayed':False})
print(json.dumps({'reference_checks':len(checks),'all_pass':all(c['match'] for c in checks),'historical_preservation':all(c['byte_identical'] for c in preservation),'test_top_level_passes':{t['label']:len(t['top_level_passes']) for t in tests},'actual_input_business_counts':empty_business,'native_binaries_have_trimpath':all(b['native_platform_qualifiable'] for b in buildinfo[2:])},ensure_ascii=False,indent=2))
