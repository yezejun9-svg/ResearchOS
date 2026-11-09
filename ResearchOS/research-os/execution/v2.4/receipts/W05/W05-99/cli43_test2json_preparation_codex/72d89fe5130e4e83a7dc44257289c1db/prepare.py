"""Pure source/AST preparation only. Never imports or runs proposed code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
R=ROOT/'execution/v2.4/receipts/W05/W05-99/cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078/runner.v6.proposed.py'
H=ROOT/'execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0/windows_debug_job_tree.py'
REV=ROOT/'execution/v2.4/receipts/W05/W05-99/cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317/review.json'
TOOL=ROOT/'.local/tools/go1.27.1/go/src/cmd/go/internal/tool/tool.go'
MAIN=ROOT/'.local/tools/go1.27.1/go/src/cmd/test2json/main.go'
def need(x,why):
    if not x: raise ValueError(why)
def pin(p):
    raw=Path(p).read_bytes()
    return {'path':str(Path(p).absolute()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,raw):
    (OUT/name).open('xb').write(raw)
def save(name,v): put(name,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
inputs=[pin(p) for p in [R,H,REV,TOOL,MAIN]]
need(inputs[0]['sha256']=='333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea','runner pin')
need(inputs[1]['sha256']=='8368debd47b8a1df7e4b8c6f11d28abdd7df49d8683ac755134d3877ca818e27','helper pin')
need(inputs[2]['sha256']=='3e4fe1b97b9a3a937ed2c557d240c91477e309c0e114d0549fbb4e83cce9dbcb','review pin')
need(inputs[3]['sha256']=='f56daeda08b9d783d74e4598114bc8e04aa22cafae1596205dbb1dc17026bb50','fixed Go source pin')
save('inputs.before.json',inputs)
for i,p in enumerate([R,H,REV,TOOL,MAIN]): put(str(i)+'-'+p.name+'.original.txt',p.read_bytes())

patches=[]
def revise(raw,old,new,label):
    nl='\r\n' if b'\r\n' in raw else '\n'
    old=old.replace('\r\n','\n').replace('\n',nl).encode('utf8')
    new=new.replace('\r\n','\n').replace('\n',nl).encode('utf8')
    need(raw.count(old)==1,'unique anchor '+label)
    patches.append({'label':label,'old':old.decode('utf8'),'new':new.decode('utf8')})
    return raw.replace(old,new,1)

r0=R.read_bytes();r=r0
r=revise(r,"need(images and len(images)<=62,'Finite compiler image list must leave two slots for the new test and CLI')",
 "need(images and len(images)<=61,'Finite compiler image list must leave three slots for test2json, test and CLI')",'three-dynamic-images-within-original64')
anchor="        cli=build/'researchos-cli.exe';test=build/'cli.test.exe'\n"
block="""        # Build the standard-library tool explicitly; never invoke go tool's implicit builder.
        tool_graph,_=run('go-list-test2json',[go,'list','-buildvcs=false','-mod=readonly','-compiled','-deps',
             '-json','-work','-x','cmd/test2json'],export,240,True,images,2048)
        tool_text=tool_graph.decode('utf-8',errors='strict');tool_idx=0;tool_packages=[]
        while tool_idx<len(tool_text):
            if tool_text[tool_idx].isspace(): tool_idx+=1;continue
            obj,tool_idx=decoder.raw_decode(tool_text,tool_idx);tool_packages.append(obj)
        need(tool_packages and all(p.get('Goroot') is True and not p.get('Error') and not p.get('DepsErrors')
             for p in tool_packages),'TEST2JSON_GRAPH_OUTSIDE_FROZEN_GOROOT_OR_ERROR')
        need(sum(p.get('ImportPath')=='cmd/test2json' and p.get('Name')=='main' for p in tool_packages)==1,
             'TEST2JSON_MAIN_GRAPH_MISSING_OR_AMBIGUOUS')
        tool_graph_files=[];tool_root=Path(compiler['GOROOT']).absolute()
        for p in tool_packages:
            need(not p.get('Module'),'TEST2JSON_UNEXPECTED_MODULE')
            for field in fields:
                for name in p.get(field,[]):
                    q=Path(name) if Path(name).is_absolute() else Path(p['Dir'])/name
                    q=q.absolute()
                    need(q.is_file() and q.resolve()==q and q.is_relative_to(tool_root)
                         and str(q) in ledger.members,'TEST2JSON_UNCATALOGUED_SOURCE: '+str(q))
                    tool_graph_files.append(q)
        save(out/'test2json-graph.actual.json',{'packages':tool_packages,
             'all_referenced_files':[pin(p) for p in sorted(set(tool_graph_files))],
             'only_existing_frozen_GOROOT_sources':True})
        ledger.add('test2json-actual-source-graph',tool_graph_files)
        tool_bin=safe(export/'bin',export)
        if not tool_bin.exists(): tool_bin.mkdir()
        need(tool_bin.is_dir(),'TEST2JSON_OUTPUT_PARENT_NOT_DIRECTORY')
        test2json=safe(tool_bin/'test2json.exe',export,True)
        save(out/'test2json-build.before.json',{'output_path':str(test2json),'output_absent':True,
             'WORK':[pin(p) for p in files(build/'gotmp')],'cache':[pin(p) for p in files(build/'gocache')]})
        ledger.check('test2json-before-build')
        run('build-test2json',[go,'build','-p=1','-mod=readonly','-buildvcs=false','-work','-x','-o',
             str(test2json),'cmd/test2json'],export,600,True,images,2048)
        need(test2json.is_file(),'TEST2JSON_BUILD_OUTPUT_MISSING')
        ledger.add('fresh-test2json-executable',[test2json])
        save(out/'test2json-build.after.json',{'test2json':pin(test2json),
             'WORK':[pin(p) for p in files(build/'gotmp')],'cache':[pin(p) for p in files(build/'gocache')],
             'fresh_build':True,'installed_or_old_tool_reused':False})
        ledger.check('test2json-after-build')
        cli=build/'researchos-cli.exe';test=build/'cli.test.exe'
"""
r=revise(r,anchor,block,'explicit-tool-graph-and-fresh-build')
r=revise(r,"allwork+allcache+archives+[cli,test])","allwork+allcache+archives+[cli,test,test2json])",'full-compiled-artifact-ledger')
r=revise(r,"'cli':pin(cli),'testexe':pin(test),'same_round':True", "'cli':pin(cli),'testexe':pin(test),'test2json':pin(test2json),'same_round':True",'compiled-closure-tool-pin')
r=revise(r,"        ledger.check('compiled-before-first-case')", "        run('buildinfo-test2json',[go,'version','-m',str(test2json)],export,30,True,images,4)\n        ledger.check('compiled-before-first-case')",'tool-buildinfo-before-first-case')
r=revise(r,"argv=[go,'tool','test2json','-t','-p'","argv=[str(test2json),'-t','-p'",'direct-pinned-tool-argv')
r=revise(r,"510,True,images+[pin(cli),pin(test)],16,ee)","510,True,images+[pin(cli),pin(test),pin(test2json)],16,ee)",'finite-case-image-set')
r=revise(r,"            if ledger:\n", "            if 'test2json' in locals():\n                try: save(out/'test2json-artifact.finally.json',{'output_path':str(test2json),\n                    'exists':test2json.exists(),'file':pin(test2json) if test2json.is_file() else None,\n                    'partial_if_failed':first is not None})\n                except BaseException as e: secondary.append({'stage':'test2json-partial-artifact','error':repr(e)})\n            if ledger:\n",'tool-output-failure-inventory')
rp=list(patches);patches=[]
h0=H.read_bytes();h=h0
h=revise(h,"        'events': [], 'modules': [], 'exit_event_observed': False,", "        'events': [], 'modules': [], 'exit_event_observed': False,\n        'rejected_load_facts': [], 'bounded_rejected_load_facts': 1,",'first-rejected-load-bounded-diagnostic')
anchor="        def capture_file(raw_handle, event_code, image_base, process_id):\n"
block="""        def reject_load(fact, expected_pin, reason):
            # Preserve only facts already read from this event's actual hFile.
            # This never authorizes the load, performs extra IO, or appends a qualified module.
            if not debug['rejected_load_facts']:
                proc=processes[fact['pid']]
                generation=next(i+1 for i,p in enumerate(generations) if p is proc)
                debug['rejected_load_facts'].append({**fact,'process_generation':generation,
                    'expected_pin':expected_pin,'rejection_reason':reason,
                    'qualified_module':False,'diagnostic_only':True})
            raise RuntimeError(reason)

        def capture_file(raw_handle, event_code, image_base, process_id):
"""
h=revise(h,anchor,block,'diagnostic-from-already-hashed-fact')
h=revise(h,"                    raise RuntimeError('Actual loaded module outside frozen runtime universe')",
 "                    reject_load(fact,module_pins.get(image_key(path_buffer.value)),\n                                'Actual loaded module outside frozen runtime universe')",'unknown-module-before-rejection')
h=revise(h,"                        raise RuntimeError('Actual CREATE_PROCESS file path/bytes outside pinned executable set')",
 "                        reject_load(fact,image_pins.get(loaded_image_key),\n                                    'Actual CREATE_PROCESS file path/bytes outside pinned executable set')",'unknown-image-before-rejection')
h=revise(h,"                        raise RuntimeError('Primary image mismatch')",
 "                        reject_load(fact,expected_image,'Primary image mismatch')",'primary-image-mismatch-diagnostic')
hp=list(patches)
for raw,base,changes,name in [(r,r0,rp,'runner.v7.proposed.py'),(h,h0,hp,'windows_debug_job_tree.diagnostic.proposed.py')]:
    restored=raw
    for p in reversed(changes):
        need(restored.count(p['new'].encode('utf8'))==1,'unique inverse '+p['label'])
        restored=restored.replace(p['new'].encode('utf8'),p['old'].encode('utf8'),1)
    need(restored==base,'inverse wholebyte '+name)
    ast.parse(raw.decode('utf8'),filename=name)
    put(name,raw)
    put(name+'.diff',''.join(difflib.unified_diff(base.decode('utf8').splitlines(True),raw.decode('utf8').splitlines(True),fromfile='pinned-original',tofile=name)).encode('utf8'))
save('exact-transformations.json',{'runner':rp,'helper':hp})
def functions(raw):
    tree=ast.parse(raw.decode('utf8'))
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
rf0,rf1=functions(r0),functions(r);hf0,hf1=functions(h0),functions(h)
need(all(rf0[k]==rf1[k] for k in rf0 if k!='main'),'unrelated runner function drift')
need(hf0['runtime_resource_paths']==hf1['runtime_resource_paths'],'runtime inventory drift')
tail="            current_case['fixture_observation']='STARTED'"
need(r0.decode('utf8').split(tail,1)[1].split('    except BaseException as e:',1)[0]==r.decode('utf8').split(tail,1)[1].split('    except BaseException as e:',1)[0],'business qualifier bytes drift')
tree=ast.parse(r.decode('utf8'))
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run']
labels=[n.args[0].value if isinstance(n.args[0],ast.Constant) else '<two-case-loop>' for n in calls]
need(len(calls)==13 and labels.count('<two-case-loop>')==1,'native static call count')
need(len(calls)+1==14,'full-success-path native count')
save('static-audit.json',{'candidate_execution':False,'AST_parse':2,'wholebyte_inverse':True,
 'unchanged_runner_top_level_functions':[k for k in rf0 if k!='main'],'unchanged_helper_runtime_inventory':True,
 'business_qualifier_suffix_bytes_identical':True,'native_call_sites':labels,'full_success_native_calls':14,
 'native_cap':16,'compiler_call_timeout':600,'case_timeout':510,'inner_soft_deadline':3300,'outer_timeout':3600,
 'Job_active_process_limit':16,'compiler_total_process_cap':2048,'case_total_process_cap':16,
 'image_cap':64,'static_compiler_image_limit_narrowed_from':62,'static_compiler_image_limit':61,
 'diagnostic_record_limit':1,'helper_no_new_file_read':True,'cases_status':['NOT_RUN','NOT_RUN'],
 'Go_SQL_Node_SDK_HTTP_model_helper_DLL_execution':0})
after=[pin(p) for p in [R,H,REV,TOOL,MAIN]]
need(after==inputs,'public input drift')
save('inputs.after.json',after)
print(json.dumps({'output':str(OUT),'runner':pin(OUT/'runner.v7.proposed.py'),'helper':pin(OUT/'windows_debug_job_tree.diagnostic.proposed.py'),'inputs':len(inputs),'drift':0,'AST_only':True},ensure_ascii=False))
