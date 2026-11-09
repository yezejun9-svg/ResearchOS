from pathlib import Path
import subprocess,hashlib
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
OLD=OUT.parents[1]/'desktop_managed_qualification_client_review_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012'
BUILD=WT/'.local/managed-client-repair-v2-bound-final'
replacements={
 'desktop_managed_qualification_client_codex/':'desktop_managed_qualification_client_repair_v2_codex/',
 'w05-desktop-managed-qualification-client-20261012':'w05-desktop-managed-qualification-client-repair-v2-20261012',
 'managed-client-bound-final3':'managed-client-repair-v2-bound-final',
 'fc350c97cddbf7d54e37b88ece25b0e8be8f1d87':'956225e98e17c1d9e15d4787fe4dd366a687d2e4',
 '31579e9e4c48d9e16719c3d78ea1eca8f9a161156ee64d6856f5bf8083ca2620':'d7294e8a5b4dec3b1f6c60545bcad506a5d2d0efb7253d4d27318c99c596d315',
 'f8024bfb5d835d5cf9b9584970988e6c818b413e5362d592166c518faea81617':'fdf4e87c764888799f1bf01a8042cd6d0792a1b1a9c237b92296e66f50df2874',
}
for name in ['prepare.py','run_checks.py','fixture-support.mjs','qualification-entry.html','qualification-entry.jsx','lifecycle-dom.mjs']:
    text=(OLD/name).read_text(encoding='utf-8')
    for before,after in replacements.items():text=text.replace(before,after)
    if name=='prepare.py':
        extra="""
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
assert not subprocess.check_output(['git','status','--short','-uno'],cwd=WT).strip()
cumulative=subprocess.check_output(['git','diff','--name-only','1c17662c4e4cc7058cd1d045ae0d55d9f75c3633',CANDIDATE],cwd=WT,text=True).splitlines()
assert len(cumulative)==8
for name in cumulative:
    raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{name}'],cwd=WT)
    expected=hashlib.sha256(raw).hexdigest()
    check('cumulative-source',WT/name,expected)
    if (BUILD/name).is_file():check('cumulative-bound-source',BUILD/name,expected)
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
"""
        text=text.replace("descriptor=read(APP/'resources/client-wire/descriptor.json')",extra+"\ndescriptor=read(APP/'resources/client-wire/descriptor.json')")
    if name=='run_checks.py':
        start=text.index("if label=='default-smoke':")
        end=text.index("elif label=='ui-v5-regression':",start)
        text=text[:start]+"if label=='boundary':args=[node,'--test',str(OUT/'bound-boundary.test.mjs')]\n"+text[end:]
    if name=='fixture-support.mjs':
        text=text.replace("statusState='QUALIFIED_PURPOSE_AUTHORIZED',consumed=true","statusState='QUALIFIED_PURPOSE_AUTHORIZED',consumed=true,serial=0,lastId=null,holdOperation=null,held=null")
        text=text.replace("const now=Date.now(),requestBody={request_id:'req-'+name,project_id:'project-1',session_id:'session-1',model_config_ref:'model-1'", "if(request.operation==='PREPARE'){serial++;lastId='req-'+name+'-'+serial}\n  const now=Date.now(),requestBody={request_id:lastId,project_id:request.project_id,session_id:request.session_id,model_config_ref:request.model_config_ref")
        text=text.replace("expiresSoon?59800:1000","expiresSoon&&serial===1?59800:1000").replace("expiresSoon?200:58000","expiresSoon&&serial===1?200:58000")
        text=text.replace("request_id:'req-'+name,request_hash:requestHash,state:statusState","request_id:lastId,request_hash:requestHash,state:statusState")
        text=text.replace("setImmediate(()=>{const raw=Buffer.from(JSON.stringify(frame));frames.push({direction:'fixture_to_desktop',raw:raw.toString()});manager.onLine(raw)})", "const deliver=()=>{const raw=Buffer.from(JSON.stringify(frame));frames.push({direction:'fixture_to_desktop',raw:raw.toString()});manager.onLine(raw)}\n  if(request.operation===holdOperation)held=deliver;else setImmediate(deliver)")
        text=text.replace("return {manager,scope,frames,dir,discoveryFile,discovery,", "return {manager,scope,frames,dir,discoveryFile,discovery,hold:op=>holdOperation=op,release:()=>{const send=held;held=null;send?.()},")
    (OUT/name).write_text(text,encoding='utf-8')
test=(WT/'tests/ui/desktop/desktop-management-boundary.test.mjs').read_text(encoding='utf-8')
for name in ['desktop-management.js','ipc.js']:
    test=test.replace('../../../apps/desktop/main/lib/'+name,(BUILD/'apps/desktop/main/lib'/name).as_posix())
(OUT/'bound-boundary.test.mjs').write_text(test,encoding='utf-8')
print('Prepared independent verification and bound test harness; no candidate files written.')
