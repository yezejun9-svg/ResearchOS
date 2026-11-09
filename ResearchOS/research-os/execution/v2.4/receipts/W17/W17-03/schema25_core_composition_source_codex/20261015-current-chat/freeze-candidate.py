"""Freeze the exact53 source candidate and bounded test evidence for independent review."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/作品集/ResearchOS/research-os')
SOURCE=ROOT/'.local/worktrees/schema25-core-composition-20261015'
HERE=Path(__file__).resolve().parent
MAP=ROOT/'execution/v2.4/receipts/W17/W17-03/composition_map_independent_codex/20261015-current-chat/COMPOSITION-MAP.json'
SCOPE=ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp492/four-branch-source-composition-scope.json'
BASE='4f4023c956f84d65743f39ce77d6c8899a21ada1'
HEAD='2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02'
TREE='ad73440fdc98416687a75a8cb3ff23eff2cb0253'

def git(*args):
    return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd=SOURCE)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}

def save(name,value):
    path=HERE/name
    if path.exists(): raise RuntimeError('already frozen '+name)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')
    return ref(path)

def main():
    plan=json.loads(MAP.read_bytes())
    scope=json.loads(SCOPE.read_bytes())
    if git('rev-parse','HEAD').decode().strip()!=HEAD or git('rev-parse','HEAD^{tree}').decode().strip()!=TREE:
        raise RuntimeError('candidate identity changed')
    if git('status','--porcelain=v1','--untracked-files=all').strip():
        raise RuntimeError('candidate worktree not clean')
    changed=git('diff','--name-only',BASE,HEAD).decode().splitlines()
    if changed!=sorted(scope['bounded_builder_scope']['source_paths']):
        raise RuntimeError('candidate diff outside exact53')
    git('diff','--check',BASE,HEAD)
    protected={r['path']:r['main'] for r in plan['main']['protected']}
    expected={**scope['bounded_builder_scope']['expected_final_blobs'],**protected}
    for rel, pin in expected.items():
        path=SOURCE/rel
        if not path.is_file() or path.stat().st_size!=pin['bytes'] or sha(path)!=pin['sha256']:
            raise RuntimeError('source guard '+rel)
    raw=git('ls-tree','-r','-z',HEAD)
    tree=[]
    for entry in raw.split(b'\0'):
        if not entry: continue
        meta,path=entry.split(b'\t',1)
        mode,kind,oid=meta.decode().split(' ')
        tree.append({'path':path.decode('utf-8'),'mode':mode,'kind':kind,'object':oid})
    tree_ref=save('candidate-full-tree.json',{'schema':'researchos.schema25-combined-full-tree/1',
        'head':HEAD,'tree':TREE,'entries':tree,'entry_count':len(tree),'formal_increment':0})
    inputs=[]
    for stage in plan['stages']:
        inputs.append({'stage':stage['name'],'base':stage['base'],'head':stage['head'],
                       'files':[{'path':f['path'],'action':f['action'],
                                 'expected_before':f['expected_before'],'candidate':f['candidate']}
                                for f in stage['files']]})
    inputs_ref=save('source-input-inventory.json',{'schema':'researchos.schema25-combined-source-inputs/1',
        'scope':ref(SCOPE),'map':ref(MAP),'ordered_inputs':inputs,
        'final_53':scope['bounded_builder_scope']['expected_final_blobs'],
        'protected_main_10':protected,'formal_increment':0})
    patch=git('diff','--binary','--no-ext-diff','--no-textconv',BASE,HEAD)
    patch_file=HERE/'candidate-source.patch'
    patch_file.write_bytes(patch)
    patch_ref=ref(patch_file)
    labels=[]
    for path in sorted(HERE.glob('T*.json')):
        row=json.loads(path.read_bytes())
        if 'native_exit' in row:
            labels.append({'label':row['label'],'receipt':ref(path),'native_exit':row['native_exit'],
                           'top_level':row.get('go_test_top_level'),'source_drift':row.get('source_guard_drift',row.get('source_drift'))})
    evidence=[]
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.name!='FINAL.json':
            evidence.append({'name':path.name,**ref(path)})
    save('FINAL.json',{'schema':'researchos.schema25-four-branch-source-candidate-final/1',
        'at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'status':'LOCAL_SOURCE_CANDIDATE_FOR_INDEPENDENT_REVIEW',
        'source_base':BASE,'source_commit':HEAD,'source_tree':TREE,
        'worktree':str(SOURCE),'exact_changed_paths':changed,
        'changed_count':len(changed),'protected_main_count':len(protected),
        'full_tree':tree_ref,'source_input_inventory':inputs_ref,'patch':patch_ref,
        'tests':labels,
        'outstanding':[{'id':'T3-baseline-active-queue','state':'OPEN_BASELINE_FIXTURE_FAILURE',
            'detail':'Main4f and candidate both fail identical missing client_command_identities in historical source22 fixture.'},
            {'id':'T8','state':'OUT_OF_SCOPE','detail':'No signing, original-data migration, package, deployment, or formal case acceptance.'}],
        'evidence_files':evidence,'formal_increment':0})
    print(json.dumps({'source_commit':HEAD,'source_tree':TREE,'exact53':len(changed),
                      'tree_entries':len(tree),'evidence_files':len(evidence)},ensure_ascii=False))

if __name__=='__main__': main()
