import concurrent.futures, datetime, hashlib, json, pathlib, subprocess, uuid

root = pathlib.Path(__file__).resolve().parents[7]
main = pathlib.Path('D:/作品集/ResearchOS/research-os')
receipts = pathlib.Path(__file__).resolve().parent.parent
out = receipts / ('handoff-' + uuid.uuid4().hex)
out.mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
def ref(p): return {'path': p.relative_to(root).as_posix(), 'sha256': sha(p)}
def invoke(name, args):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    r = subprocess.run(args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out/(name+'.stdout')).write_bytes(r.stdout)
    (out/(name+'.stderr')).write_bytes(r.stderr)
    save(name+'.invocation.json', dict(actualargv=args,cwd=str(root),started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=r.returncode))
    return r

paths = ['internal/domain/'+name for name in ['backup_upgrade.go','backup_migration.go','backup.go','store.go','backup_configuration_upgrade.go','backup_configuration_upgrade_test.go','backup_host_configuration.go','backup_host_configuration_test.go','contracts/client.protocol.schema.json','contracts/client.protocol.domain.schema.json']]
foundation = ['migrations/sqlite/0023_host_model_configuration.sql'] + ['internal/domain/'+n for n in ['client_configuration.go','client_configuration_test.go','client_command_identity.go','client_command_identity_test.go']]
head = invoke('git-head',['git','rev-parse','HEAD']).stdout.decode().strip()
status = invoke('git-status',['git','status','--porcelain=v1'])
changed = invoke('git-diff-names',['git','diff','--name-only']).stdout.decode().splitlines()
assert set(changed) <= set(paths), changed
diff = invoke('git-diff-check',['git','diff','--check'])
assert diff.returncode == 0
gofmt = main/'.local/tools/go1.27.1/go/bin/gofmt.exe'
fmt = invoke('gofmt-check',[str(gofmt),'-l',*[str(root/p) for p in paths if p.endswith('.go')]])
assert fmt.returncode == 0 and not fmt.stdout
source_rows=[]
for p in paths:
    original = subprocess.run(['git','show','HEAD:'+p],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    target=out/'source_snapshots'/p
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((root/p).read_bytes())
    source_rows.append(dict(path=p, before_sha256=hashlib.sha256(original.stdout).hexdigest() if original.returncode==0 else None, after_sha256=sha(root/p), bytes=(root/p).stat().st_size,snapshot=ref(target)))
save('source.before_after.json',source_rows)
guards=[]
for p in foundation:
    original=subprocess.run(['git','show','fef0ee2d56351e74ceed11b0b37d3f87e9c83494:'+p],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    guards.append(dict(path=p, git_commit='fef0ee2d56351e74ceed11b0b37d3f87e9c83494',sha256=sha(root/p),unchanged=original==(root/p).read_bytes()))
assert all(x['unchanged'] for x in guards)
protected=['internal/domain/backup_queue_upgrade.go','internal/domain/backup_recovery.go','internal/domain/backup_command_queue.go','internal/domain/backup_command_queue_test.go','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json']
protected += [p.relative_to(root).as_posix() for p in (root/'migrations/sqlite').glob('*.sql')]
for p in sorted(set(protected)):
    original=subprocess.run(['git','show','HEAD:'+p],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    guards.append(dict(path=p,git_commit=head,sha256=sha(root/p),unchanged=original==(root/p).read_bytes()))
assert all(x['unchanged'] for x in guards)
assert not list((root/'migrations/sqlite').glob('0024*'))
save('protected_sources.json',guards)

run_rows=[]
for directory in sorted(receipts.glob('closure-*')):
    if not (directory/'result.json').is_file(): continue
    result=json.loads((directory/'result.json').read_text('utf8'))
    events=[]
    for line_number,line in enumerate((directory/'test.stdout').read_text('utf8',errors='replace').splitlines(),1):
        try: row=json.loads(line)
        except ValueError: continue
        if row.get('Test') and row.get('Action') in ['pass','fail','skip']:
            events.append(dict(test=row['Test'],action=row['Action'],line=line_number))
    run_rows.append(dict(directory=directory.name,result=result,invocation=ref(directory/'test.invocation.json'),stdout=ref(directory/'test.stdout'),stderr=ref(directory/'test.stderr'),source_before=ref(directory/'source_before.json'),source_after=ref(directory/'source_after.json'),counts={action:sum(x['action']==action for x in events) for action in ['pass','fail','skip']},top_level_pass=sum(x['action']=='pass' and '/' not in x['test'] for x in events),assertions=events))
save('all_actual_runs.json',run_rows)
focused=receipts/'closure-1bdf02a977c9459cb024a3e803593c64'
fullcli=receipts/'closure-a2594db073c34772889321d4d20c8a20'
hardpin=receipts/'closure-61315ea6c5a04739b32a7e394fe3d25d'
vectors=[json.loads((d/'source_after.json').read_text('utf8')) for d in [focused,fullcli,hardpin]]
assert vectors[0]==vectors[1]==vectors[2]
vector=vectors[0]
def resolve(k):
    prefix,path=k.split(':',1)
    return {'repo':root,'main':main}.get(prefix,pathlib.Path())/path
def verify(item):
    k, expected=item
    p=resolve(k)
    actual=sha(p) if p.is_file() else 'MISSING'
    return dict(path=k,expected=expected,actual=actual) if actual!=expected or actual=='MISSING' else None
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    drift=[x for x in pool.map(verify,vector.items()) if x]
save('current_compiled_closure_audit.json',dict(inputs=len(vector),drift=drift,source_vectors=[ref(d/'source_after.json') for d in [focused,fullcli,hardpin]],checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
assert not drift, drift[:5]

failures=[]
for row in run_rows:
    if row['result']['exit'] or row['counts']['fail']:
        failures.append(dict(run=row['directory'],actual_exit=row['result']['exit'],failures=[x for x in row['assertions'] if x['action']=='fail'],invocation=row['invocation'],stdout=row['stdout'],classification='KNOWN_UNCHANGED_SCHEMA22_HARDPIN_OPEN' if row['directory']==hardpin.name else 'PRESERVED_ORIGINAL_FAILURE_NOT_ERASED'))
save('failure_origins.final.json',dict(original_first_file=ref(pathlib.Path(__file__).resolve().parent/'failure_origins.first.json'),actual_test_failures=failures,expected_negative_build=ref(receipts/'mirror-compile-negative-b7c0582714774bc694c8c19e15f26962/invocation.json') if (receipts/'mirror-compile-negative-b7c0582714774bc694c8c19e15f26962/invocation.json').exists() else None,tool_read_diagnostic={'chunk_id':'1968e2','actual':'rg read two nonexistent guessed test filenames; no source writes; actual existing tests discovered using rg glob','product_failure':False},apply_patch_original_diagnostic_limit='First-file retrospective diagnostics retain known tool messages. A PTY chunk was not produced for apply_patch and is not fabricated here; original conversation tool output remains the original record.'))
save('audit_summary.json',dict(status='EXECUTOR_CANDIDATE_NOT_ACCEPTANCE',head=head,exact_source_count=len(paths),source_changed_names=changed,foundation_unchanged=True,compiled_current_drift=drift,fullcli_counts=next(x['counts'] for x in run_rows if x['directory']==fullcli.name),focused_counts=next(x['counts'] for x in run_rows if x['directory']==focused.name),hardpin_counts=next(x['counts'] for x in run_rows if x['directory']==hardpin.name),run_count=len(run_rows)))
print(out)
print(json.dumps(json.loads((out/'audit_summary.json').read_text('utf8')),ensure_ascii=False))
