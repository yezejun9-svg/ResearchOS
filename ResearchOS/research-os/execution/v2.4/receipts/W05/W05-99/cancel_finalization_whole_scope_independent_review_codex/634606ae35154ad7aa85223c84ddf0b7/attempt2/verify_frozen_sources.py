from pathlib import Path
import json,hashlib,subprocess,datetime
NS=Path(__file__).resolve().parents[1]
ROOT=NS.parents[6]
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99'
HEAD='2cdb0d43d5a600eef13c8f1735946a9adf52d079'
folders=['cancel_finalization_design_revision_codex/246ac4e22a3c48fe8d86753b44a6cd78','cancel_finalization_udf_producer_supplement_codex/9d5612d4e27d43e09250867e88edcc9e']
entries=[]
commands=[]
for folder in folders:
    before=json.loads((BASE/folder/'input.before.json').read_bytes())
    after=json.loads((BASE/folder/'input.after.json').read_bytes())
    before_originals={k:v['original'] for k,v in before['files'].items()}
    assert before_originals==after['files'],folder
    for relative,record in before['files'].items():
        original=Path(record['original']['path'])
        assert original.is_relative_to(ROOT),str(original)
        assert 'codex-w0599-host-configuration-handler' not in original.parts
        raw=original.read_bytes()
        want=record['original']
        assert hashlib.sha256(raw).hexdigest()==want['sha256'] and len(raw)==want['bytes'],relative
        snapshot=NS/'sources'/folder.split('/')[0]/Path(relative)
        assert snapshot.read_bytes()==raw,relative
        entry={'relative':relative,'original':str(original),'sha256':want['sha256'],'bytes':len(raw),'original_current_same':True,'own_snapshot_same':True}
        if not relative.startswith(('.local/','execution/')):
            argv=['git','show',HEAD+':'+relative]
            proc=subprocess.run(argv,cwd=ROOT,capture_output=True)
            stem=NS/'commands'/f'frozen-git-{len(commands):03d}'
            stem.with_suffix('.stdout.raw').write_bytes(proc.stdout)
            stem.with_suffix('.stderr.raw').write_bytes(proc.stderr)
            result={'argv':argv,'cwd':str(ROOT),'actual_exit':proc.returncode,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest()}
            stem.with_suffix('.result.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
            commands.append(result)
            assert proc.returncode==0,relative
            assert proc.stdout==raw,relative
            entry['pinned_git_blob_same']=True
        else:
            entry['pinned_git_blob_same']=None
            entry['pin_basis']='Exact public source/dependency/receipt SHA from frozen authored before/after and own copy; no private path.'
        entries.append(entry)
result={'schema':'researchos.f08.independent-frozen-source-verification.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main_head':HEAD,'source_refs_checked':len(entries),'git_blob_checks':len(commands),'all_match':True,'handler_live_read':False,'entries':entries,'commands':commands,'SQL_test_compile_HTTP_model_paid':0}
(NS/'frozen-source-verification.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['entries','commands']},ensure_ascii=True))
