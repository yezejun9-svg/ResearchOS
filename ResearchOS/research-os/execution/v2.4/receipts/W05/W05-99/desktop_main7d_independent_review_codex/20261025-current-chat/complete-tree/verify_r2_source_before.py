import hashlib,json,pathlib,subprocess
E=pathlib.Path(__file__).parent
A=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_native_codex/20261025-current-chat/complete-tree/build-01')
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
freeze=json.loads((E/'r2-fixed-inputs/source-freeze-02.json').read_bytes())
raw=(A/'source.before.json').read_bytes()
before=json.loads(raw)
assert before['head']==freeze['base_commit'] and before['tree']==freeze['base_tree']
assert len(before['files'])==freeze['source_input_count']==591
assert before['digest']==freeze['source_snapshot_digest']
assert hashlib.sha256(json.dumps(before['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==before['digest']
for row in before['files']:
    p=W/row['path']; data=p.read_bytes()
    assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
    if row['candidate_delta']: assert row['sha256']==freeze['seven_file_hashes'][row['path']]['sha256']
def git(*args): return subprocess.run(['git','--no-optional-locks','-C',str(W),*args],capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().strip()==freeze['base_commit']
assert git('show','-s','--format=%T','HEAD').decode().strip()==freeze['base_tree']
changed=set()
for args in [('diff','--name-only','-z'),('diff','--cached','--name-only','-z'),('ls-files','--others','--exclude-standard','-z')]:
    changed.update(x.decode('utf-8') for x in git(*args).split(b'\0') if x)
assert sorted(changed)==freeze['candidate_delta']
assert raw==(A/'source.before.json').read_bytes()
with (E/'r2-fixed-inputs/build-source.before.json').open('xb') as out:out.write(raw)
result={'status':'MATCH','checked_actual_source_files':591,'source_digest':before['digest'],'head':before['head'],'tree':before['tree'],'only_changed_paths':sorted(changed),'source_before_sha256':hashlib.sha256(raw).hexdigest(),'mode':'READ_ONLY_NO_BUILD_NO_NATIVE'}
(E/'R2-source-before-independent-check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
