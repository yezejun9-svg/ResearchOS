"""Pure source/AST preparation, no candidate module imports or execution."""
import ast,json,hashlib,difflib
from pathlib import Path
O=Path(__file__).resolve().parent
def need(x,m):
    if not x:raise RuntimeError(m)
def save(n,x):
    b=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
    with (O/n).open('xb') as f:f.write(b)
def revised(src,out,changes):
    raw=(O/src).read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode();edits=[]
    for a,b in changes:
        a=a.replace('\n',nl);b=b.replace('\n',nl);need(text.count(a)==1,'Unique source anchor '+a[:90]);text=text.replace(a,b,1);edits.append({'old':a,'new':b})
    new=text.encode();ast.parse(new);inverse=new
    for e in reversed(edits):need(inverse.count(e['new'].encode())==1,'Inverse anchor');inverse=inverse.replace(e['new'].encode(),e['old'].encode(),1)
    need(inverse==raw,'Whole inverse');save(out,new);save(out+'.edits.json',edits)
    return new,edits
revised('windows_debug_job_tree.future_images.proposed.py','windows_debug_job_tree.future_images.final.proposed.py',[
 ('if future_images is not None and not cleanup_mode:', 'if future_images is not None:'),
 ('                    if event.code == 5 and event.pid in processes:\n', '                    if may_continue and event.code == 5 and event.pid in processes:\n'),
 ('                    # Always release the received notification, even after capture failure.\n','                    # Opt-in failures release the notification only after successful owned-job termination.\n')])
revised('desktop_controller.proposed.py','desktop_controller.v2.proposed.py',[
 ("    allowed=resources['files']+[scope[k] for k in ['controller_ref','launcher_ref','authorization_verifier_ref','utility_ref','owned_helper_ref','debug_helper_ref']]\n",
  "    code_keys=['controller_ref','launcher_ref','authorization_verifier_ref','utility_ref','owned_helper_ref','debug_helper_ref',\n        'network_observer_ref','fixture_evaluator_ref','roster_ref','alias_roster_ref','alias_edits_ref','instrumented_test_ref','source_catalog_ref','builder_source_ref']\n    allowed=resources['files']+[scope[k] for k in code_keys]\n    need(resources['complete_public_roots_frozen'] is True, 'Actual complete public input closure required')\n"),
 ("    out=None;first=None;secondary=[];ledger=None;last=None;stage='ALLOCATE';native=0;rows=[]\n",
  "    out=None;first=None;secondary=[];ledger=None;last=None;stage='ALLOCATE';native=0;rows=[];allcases=[];current_case=None;http_total=0\n    need(scope['native_top_command_cap']==176 and scope['process_cap']<=2048, 'Exact declared top-level operation bound')\n"),
 ("                    last=r\n", "                    last=r\n                    if current_case is not None:\n                        current_case['native_exit']=r.get('actual_exit')\n                        current_case['state']='NATIVE_EXIT_OBSERVED' if r.get('actual_exit') is not None else 'STARTED_EXIT_UNKNOWN'\n                        current_case['owned_child_pid']=r.get('owned_child_pid')\n                        current_case['creation_time_100ns']=r.get('creation_time_100ns')\n"),
 ("        catalog=strict(verify(scope['source_catalog_ref']));need(catalog['commit']==SOURCE and catalog['files'],'New source catalogue')\n",
  "        catalog=strict(verify(scope['source_catalog_ref']));need(catalog['commit']==SOURCE and catalog['files'],'New source catalogue')\n        for item in catalog['files']:\n            p=safe(ROOT/item['path'],ROOT);need(pin(p)['sha256']==item['sha256'] and pin(p)['bytes']==item['bytes'],'Original current source pin')\n        ledger.add('original-current-source',[ROOT/x['path'] for x in catalog['files']])\n"),
 ("        for row in result['invocations']:need(row['exit']==0,'Nested builder command not successful')\n",
  "        expected_nested=['go-version','node-version','go-list','go-list-negative-fixture','go-build','negative-child-build','go-test-build','web-module-junction','react-build']\n        need([x['stdout'] for x in result['invocations']]==[x+'.stdout' for x in expected_nested],'Exact existing builder operation graph')\n        for row in result['invocations']:need(row['exit']==0,'Nested builder reported failure; timeout124 is not an observed OS native exit')\n"),
 ("        for row in work['WORK']+work['archives']:verify(row)\n",
  "        for row in work['WORK']+work['archives']:verify(row)\n        packages=[];decoder=json.JSONDecoder()\n        for label in ['go-list','go-list-negative-fixture']:\n            text=(receipts/(label+'.stdout')).read_text(encoding='utf-8',errors='strict');pos=0\n            while pos<len(text):\n                if text[pos].isspace():pos+=1;continue\n                package,pos=decoder.raw_decode(text,pos);packages.append(package)\n        graph_files=[]\n        for package in packages:\n            need(not package.get('Error') and not package.get('DepsErrors'),'Actual package graph error')\n            directory=Path(package.get('Dir',''))\n            for key in ['GoFiles','CgoFiles','CompiledGoFiles','IgnoredGoFiles','IgnoredOtherFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:\n                for name in package.get(key,[]):\n                    p=Path(name) if Path(name).is_absolute() else directory/name\n                    need(p.is_file(),'Missing actual graph member');need(str(p) in ledger.members or p.is_relative_to(build),'Unfrozen actual graph input');graph_files.append(pin(p))\n            if package.get('Module',{}).get('GoMod'):\n                p=Path(package['Module']['GoMod']);need(p.is_file() and str(p) in ledger.members,'Unfrozen actual module GoMod');graph_files.append(pin(p))\n        save(out/'actual-package-graph.json',{'packages':packages,'input_refs':graph_files})\n"),
 ("        ledger.add('fresh-build-graph-artifacts',inventory(build,junction,target)+inventory(receipts)+[Path(x['path']) for x in work['archives']])\n",
  "        ledger.add('fresh-build-graph-artifacts',inventory(build,junction,target)+inventory(receipts)+[Path(x['path']) for x in work['WORK']+work['archives']])\n"),
 ("            state['state']='STARTED';save(case/'started.json',state);ledger.check(stage+'-before')\n",
  "            current_case=state;state['state']='STARTED';save(case/'started.json',state);ledger.check(stage+'-before')\n"),
 ("if index<=162:argv=[node,'--test','--test-reporter=tap'", "if index<=162:argv=[node,'--require',scope['network_observer_ref']['path'],'--test','--test-reporter=tap'"),
 ("            save(case/'fixture-verdict.json',evaluation);state.update(state='QUALIFIED',qualified=True);rows.append(dict(state))\n",
  "            http_total+=evaluation['HTTP'];need(http_total<=390,'Original aggregate observed HTTP cap')\n            save(case/'fixture-verdict.json',evaluation);state.update(state='QUALIFIED',qualified=True);rows.append(dict(state))\n            current_case=None\n"),
 ("'rows':rows,'actual_native_top_commands':native,'source_acceptance':False})\n    return 1 if first else 0\n",
  "'rows':rows,'all_case_states':allcases,'actual_observed_HTTP_total':http_total,'actual_native_top_commands':native,'source_acceptance':False})\n            if time.monotonic()>deadline:\n                save(out/'tail-deadline.failure.json',{'first_error':first,'error':'Root inner deadline exceeded after final evidence IO','actual_native_exit':None})\n                return 1\n    return 1 if first else 0\n")])
for p in O.glob('*.py'):ast.parse(p.read_bytes())
print(json.dumps({'status':'SOURCE_IO_AST_ONLY','target_calls':0,'outputs':['desktop_controller.v2.proposed.py','windows_debug_job_tree.future_images.final.proposed.py']},ensure_ascii=False))
