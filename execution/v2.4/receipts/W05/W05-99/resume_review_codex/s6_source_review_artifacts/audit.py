import hashlib, json, subprocess, difflib
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WORK=ROOT/'.local/worktrees/codex-w0599-command-queue'
REL=Path('execution/v2.4/receipts/W05/W05-99/queue_executor_codex')
REC=WORK/REL
HEAD='da7400e96aa1ce27ebb95a4b5c3a03d2b1d3d6f9'
BASE='fbf661c142a98db72d273204615a9b20641b3cc3'
def digest(raw): return hashlib.sha256(raw).hexdigest()
def sha(path): return digest(path.read_bytes())
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def git(*args): return subprocess.check_output(['git','-C',str(WORK),*args])
def ref(path): return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}
result={'candidate':HEAD,'base':BASE,'status':git('status','--porcelain').decode()}
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert result['status'].strip() in ('','?? '+(REL/'current-control-build/control.exe').as_posix())
source=load(REC/'source_after.json')['files']
for entry in source: assert sha(WORK/entry['path'])==entry['sha256']
assert len(source)==33
result['source_vector']=source
changed=git('diff','--name-only',BASE,HEAD).decode().splitlines()
source_changed=[name for name in changed if not name.startswith('execution/')]
assert set(source_changed)=={entry['path'] for entry in source}
names=git('ls-tree','-r','--name-only',HEAD,'--',REL.as_posix()).decode().splitlines()+source_changed
batch=subprocess.run(['git','-C',str(WORK),'cat-file','--batch'],input=''.join(HEAD+':'+name+'\n' for name in names).encode(),capture_output=True,check=True).stdout
position=0;blobs=[]
for name in names:
    end=batch.index(b'\n',position); header=batch[position:end].split();length=int(header[2]);position=end+1
    blob=batch[position:position+length];position+=length+1
    assert blob==(WORK/name).read_bytes(),name
    blobs.append({'path':name,'sha256':digest(blob),'bytes':len(blob)})
result['git_blobs']=blobs
manifest=load(REC/'receipt_manifest.json')
for entry in manifest['files']:
    assert sha(REC/entry['path'])==entry['sha256'],entry['path']
result['receipt_manifest_checked']=len(manifest['files'])
result['receipt_manifest']=ref(REC/'receipt_manifest.json')
result['runs']=[]
finals={'final-cli','final-current-matrix','final-sdk','current-control-startup'}
for entry in load(REC/'run_index.json'):
    folder=REC/entry['run']
    for name,expected in entry['files'].items():
        assert sha(folder/name)==expected['sha256'],str(folder/name)
    stdout=folder/('stdout.raw' if (folder/'stdout.raw').exists() else 'stdout.jsonl')
    raw=stdout.read_text(encoding='utf-8-sig')
    counts={'pass':[],'fail':[],'skip':[]}
    for line in raw.splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if row.get('Action') in counts and row.get('Test'): counts[row['Action']].append(row['Test'])
    for action in counts:
        assert counts[action]==entry.get(action+'_events',[]),(entry['run'],action)
    item={'run':entry['run'],'result':ref(folder/'result.json'),'stdout':ref(stdout),'stderr':ref(folder/'stderr.raw'),'actual_exit':entry['result']['exit_code'],'counts':{key:len(value) for key,value in counts.items()},'fail':counts['fail'],'skip':counts['skip']}
    if entry['run'] in finals:
        before=load(folder/'inputs.json');after=load(folder/'inputs-after.json')
        assert before==after
        mismatches=[]
        for inp in before:
            path=Path(inp['path']);path=path if path.is_absolute() else WORK/path
            if sha(path)!=inp['sha256']: mismatches.append(inp['path'])
        if mismatches:
            assert entry['run']=='current-control-startup' and mismatches==['internal/domain/runtime_command_queue_windows_test.go'],(entry['run'],mismatches)
            old=next(inp for inp in before if inp['path']==mismatches[0])
            assert digest(git('show','49e1d2b5:'+mismatches[0]))==old['sha256']
        command=load(folder/'command.json')
        assert sha(Path(command['exe']))==command['exe_sha256']
        bundle=Path(command['environment']['RESEARCHOS_MU_BUNDLE'])
        assert sha(bundle)==command['bundle_sha256']
        item.update({'input_count':len(before),'inputs_equal':True,'current_mismatches':mismatches,'command':ref(folder/'command.json'),'tool_sha256':command['exe_sha256'],'bundle_sha256':sha(bundle),'node_counts':entry.get('node_counts')})
    result['runs'].append(item)

scope=load(ROOT/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_legacy_target_fixture_scope_amendment.json')
protected={}
for path,spans in scope['minimal_diff_bounds'].items():
    before=(REC/(Path(path).name+'.before_target_scope')).read_bytes();after=(WORK/path).read_bytes()
    intervals=[(item['start_byte'],item['end_byte_exclusive']) for item in spans]
    if path==scope['new_helper_insertion']['path']:
        at=scope['new_helper_insertion']['byte_offset'];intervals.append((at,at))
    for op,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if op!='equal': assert any(x<=a and b<=y for x,y in intervals),(path,op,a,b)
    offset=0
    for segment in scope['protected_existing_bytes'][path]['segments']:
        raw=before[segment['start_byte']:segment['end_byte_exclusive']]
        assert digest(raw)==segment['sha256'];offset=after.index(raw,offset)+len(raw)
    protected[path]={'registered_spans_only':True,'protected_segments':len(scope['protected_existing_bytes'][path]['segments']),'sha256':digest(after)}
raw=(WORK/'apps/cli/cli_stream_test.go').read_bytes();suffix=raw[raw.index(b'// Only these composition tests resolve a project Goal binding.'):]
assert digest(suffix)=='9ce153cb99d2252c694665411a71d0ce8c8fce424796e177d99ccd12ad4be862'
protected['S5_suffix']={'sha256':digest(suffix),'bytes':len(suffix)}
result['protected_scope']=protected
result['report']=ref(REC/'execution_report.json')
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit':ref(OUT/'audit.json'),'source_paths':len(source),'git_blobs':len(blobs),'runs':len(result['runs']),'receipt_manifest_files':len(manifest['files'])}))
