"""Finite meaningful Source controls. The runtime orchestration is never called."""
from contextlib import contextmanager
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

N=Path(__file__).resolve().parent
GUARD=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,x):
    p=N/name
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
    return pin(p)
raw=GUARD.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and len(raw)==11404
gm=types.ModuleType('old21_control_guard');exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
guards=[];checks=[]
@contextmanager
def held(refs,name):
    g=gm.SourceReadGuard(total_cap=512*1024*1024)
    try:g.acquire(refs);yield g
    finally:
        primary=sys.exc_info()[0];a=g.close();guards.append(save(name+'.guard.closed.json',a))
        if primary is None:assert a['verification']=='PASSED' and a['closed'] is True and a['retained_handles_count']==0 and a['errors']==[]
def module(raw,path,name):
    m=types.ModuleType(name);exec(compile(raw,path,'exec'),m.__dict__);return m
def check(name,ok):
    checks.append({'id':name,'passed':bool(ok),'evidence_class':'AUTHOR_PURE_SOURCE_CONTROL_NOT_RUNTIME'})
    if not ok:raise AssertionError(name)
def reject(name,call,code):
    try:call()
    except (builder.BoundaryError,base.BoundaryError,common.BuildBoundaryError) as e:check(name,str(e)==code)
    else:check(name,False)
try:
    initial=[pin(N/x) for x in ['old21_builder.py','contract.json','input-manifest.json','frozen-source-manifest.json','source-preparation.json','offline-module-static-map.json']]+[pin(GUARD)]
    with held(initial,'controls_metadata') as g:
        contract=json.loads(g.get_buffer(str(N/'contract.json')))
        manifest=json.loads(g.get_buffer(str(N/'input-manifest.json')))
        inventory=json.loads(g.get_buffer(str(N/'frozen-source-manifest.json')))
        prep=json.loads(g.get_buffer(str(N/'source-preparation.json')))
        offline=json.loads(g.get_buffer(str(N/'offline-module-static-map.json')))
        extras=[contract['common_builder_ref'],contract['base_helper_ref']]+[o['ref'] for o in inventory['objects']]+prep['guard_audit_refs']
        with held(extras,'controls_source_inputs') as xg:
            builder=module(g.get_buffer(str(N/'old21_builder.py')),str(N/'old21_builder.py'),'old21_builder_source_controls')
            common=module(xg.get_buffer(contract['common_builder_ref']['path']),contract['common_builder_ref']['path'],'old21_common_source_controls')
            base=module(xg.get_buffer(contract['base_helper_ref']['path']),contract['base_helper_ref']['path'],'old21_base_source_controls')
            request={'case_id':'a'*32,'output_root':contract['output_parent']+'/old21-build-'+'a'*32}
            plan=builder.compile_request(contract,request,base);paths=plan['paths']
            check('exact-nine-Go-only-phases',len(plan['phases'])==9 and all(p['argv'][0]==contract['go_ref']['path'] for p in plan['phases']))
            check('control-backup-target-order',[p['target'] for p in plan['phases']]==[None]+['control']*4+['backup']*4)
            check('two-distinct-build-programmes',{p['argv'][-2] for p in plan['phases'] if p['kind']=='build'}=={paths['control_program'],paths['backup_program']})
            check('no-bootstrap-product-call-projected',all('--bootstrap-owner' not in p['argv'] and p['argv'][0] not in (paths['control_program'],paths['backup_program']) for p in plan['phases']))
            check('both-export-and-work-retained',all('-export' in p['argv'] for p in plan['phases'] if p['kind']=='export') and all('-x' in p['argv'] and '-work' in p['argv'] for p in plan['phases'] if p['kind']=='build'))
            for label,update,code in [('json-authority',{'approved':True},'REQUEST_FIELDS_INVALID'),('path-escape',{'output_root':'D:/outside'},'OUTPUT_SCOPE_ESCAPE'),('case-bool',{'case_id':True},'CASE_ID_INVALID'),('case-uppercase',{'case_id':'A'*32},'CASE_ID_INVALID')]:
                reject('request-'+label,lambda update=update:builder.compile_request(contract,{**request,**update},base),code)
            for label,update,code in [('wrong-schema',{'schema_version':22},'SOURCE_CONTRACT_INVALID'),('bool-schema',{'schema_version':True},'SOURCE_CONTRACT_INVALID'),('wrong-commit',{'source_commit':'a'*40},'HISTORICAL_COMMIT_TREE_REQUIRED'),('wrong-tree',{'source_tree':'b'*40},'HISTORICAL_COMMIT_TREE_REQUIRED')]:
                reject('contract-'+label,lambda update=update:builder.compile_request({**contract,**update},request,base),code)
            for s in ['../escape','/absolute','file:ads','folder//file','folder\\file','CON','folder/COM1.txt','end.','null\x00']:
                reject('relative-path-'+repr(s),lambda s=s:common.relative_file(s),'RELATIVE_FILE_INVALID')
            env=common.environment(contract,paths)
            check('offline-deterministic-environment',all(env[k]==v for k,v in {'GOPROXY':'off','GOSUMDB':'off','GOENV':'off','GOWORK':'off','GOTOOLCHAIN':'local','CGO_ENABLED':'0','GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1'}.items()))
            check('unique-no-shared-cache',env['GOCACHE']==paths['gocache'] and env['GOMODCACHE']==paths['module_cache'] and 'GOCACHEPROG' not in env)
            check('no-ambient-credentials','GOPRIVATE' in env and env['GOPRIVATE']=='' and not any(k.startswith('RESEARCHOS_') for k in env))
            check('explicit-no-fabricated-vcs','-buildvcs=false' in env['GOFLAGS'] and '-mod=readonly' in env['GOFLAGS'])
            objects=builder.validate_source_manifest(contract,manifest,inventory,base,common)
            check('exact-original272-object-set',len(objects)==272)
            check('all272-original-Git-SHA1-SHA256-bytes',builder.validate_blob_bytes(objects,xg.get_buffer))
            check('only-new-candidate-tree-membership',builder.source_membership(contract,objects,base))
            def altered_sql(old,new):
                inv=copy.deepcopy(inventory);o=next(o for o in inv['objects'] if o['git_path'].startswith('migrations/sqlite/'+old))
                o['git_path']=o['git_path'].replace('/'+old,'/'+new);o['ref']['path']=o['ref']['path'].replace('/'+old,'/'+new)
                return inv
            reject('max21-insufficient-ledger-hole',lambda:builder.validate_source_manifest(contract,manifest,altered_sql('0003_','0000_'),base,common),'EXACT_CONTIGUOUS_1_TO_21_REQUIRED')
            reject('SQL22-prohibited',lambda:builder.validate_source_manifest(contract,manifest,altered_sql('0003_','0022_'),base,common),'EXACT_CONTIGUOUS_1_TO_21_REQUIRED')
            reject('original-addon-mandatory',lambda:builder.validate_source_manifest(contract,manifest,altered_sql('next_v24_sessions.sql','unrelated.sql'),base,common),'ORIGINAL_SESSION_ADDON_REQUIRED')
            wrong=copy.deepcopy(inventory);wrong['objects'][0]['ref']['path']='D:/outside/file.go'
            reject('object-path-escape',lambda:builder.validate_source_manifest(contract,manifest,wrong,base,common),'SOURCE_OBJECT_PATH_ESCAPE')
            wrong=copy.deepcopy(inventory);wrong['objects'][1]=copy.deepcopy(wrong['objects'][0])
            reject('object-duplicate',lambda:builder.validate_source_manifest(contract,manifest,wrong,base,common),'SOURCE_OBJECT_DUPLICATE')
            wrong=copy.deepcopy(contract);wrong['runtime_source_refs']['migrations/sqlite/next_v24_sessions.sql']['sha256']='0'*64
            reject('addon-byte-drift',lambda:builder.validate_source_manifest(wrong,manifest,inventory,base,common),'ORIGINAL_RUNTIME_BYTE_PINS_REQUIRED')
            wrong=copy.deepcopy(contract);wrong['public_bootstrap_source_refs']['internal/domain/store.go']['sha256']='0'*64
            reject('public-bootstrap-source-drift',lambda:builder.validate_source_manifest(wrong,manifest,inventory,base,common),'PUBLIC_BOOTSTRAP_SOURCE_PIN_MISMATCH')
            wrong=copy.deepcopy(manifest);next(i for i in wrong['items'] if i['kind']=='module')['ref']['path']='D:/outside/module.go'
            reject('module-resource-path-escape',lambda:builder.validate_source_manifest(contract,wrong,inventory,base,common),'RESOURCE_INPUT_PATH_ESCAPE')
            first=next(iter(objects));wrongobj=copy.deepcopy(objects[first]);wrongobj['git_blob']='0'*40
            reject('original-Git-blob-mismatch',lambda:builder.validate_blob_bytes({first:wrongobj},xg.get_buffer),'HISTORICAL_GIT_BLOB_MISMATCH')
            reject('truncated-blob-rejected',lambda:builder.validate_blob_bytes({first:objects[first]},lambda p:xg.get_buffer(p)[:-1]),'HISTORICAL_BLOB_SHA256_MISMATCH')
            fake=lambda p:{'path':p,'sha256':'1'*64,'bytes':10}
            binding={'input_manifest_ref':contract['input_manifest_ref'],'source_review_ref':fake('D:/synthetic-source-control/review.json'),'resource_qualification_ref':fake('D:/synthetic-source-control/qualification.json'),'runtime_manifest_ref':fake('D:/synthetic-source-control/runtime.json'),'outer_host_binding_ref':fake('D:/synthetic-source-control/host.json'),'source_author':builder.AUTHOR,'reviewer_actor':'codex:/root/source_control_reviewer'}
            check('typed-resource-binding-shape-only',builder.validate_resource_binding(binding,contract,base)==binding)
            reject('self-review-prohibited',lambda:builder.validate_resource_binding({**binding,'reviewer_actor':builder.AUTHOR},contract,base),'INDEPENDENT_NONAUTHOR_SOURCE_REVIEW_REQUIRED')
            reject('unrelated-resource-manifest',lambda:builder.validate_resource_binding({**binding,'input_manifest_ref':fake('D:/other/manifest.json')},contract,base),'RESOURCE_MANIFEST_BINDING_MISMATCH')
            reject('resource-JSON-approval-extra',lambda:builder.validate_resource_binding({**binding,'approved':True},contract,base),'QUALIFIED_RESOURCE_BINDING_REQUIRED')
            reject('missing-live-scope',lambda:builder.require_live_scope(None),'LIVE_ROOT_SCOPE_REQUIRED')
            reject('JSON-live-scope-prohibited',lambda:builder.require_live_scope({'actor':'Root'}),'LIVE_ROOT_SCOPE_REQUIRED')
            reject('incomplete-live-interface',lambda:builder.require_live_scope(object()),'ROOT_SCOPE_INTERFACE_REQUIRED')
            observation={'actual_exit':0,'timed_out':False,'error':None,'owned_child_pid':111,'creation_time_100ns':(1<<63)+123,'resumed':True,'job_cleanup':dict(unnamed_exclusive_job=True,kill_on_job_close_configured=True,assigned_before_resume=True,job_idle_confirmed=True,primary_exit_confirmed=True,handles_closed=True,active_processes_last_observed=0,errors=[])}
            check('uint64-FILETIME-kept-exact',common.validate_owned(observation,base) and json.loads(json.dumps(observation))['creation_time_100ns']==(1<<63)+123)
            reject('float-FILETIME-rejected',lambda:common.validate_owned({**observation,'creation_time_100ns':float(1<<63)},base),'CHILD_CREATION_FILETIME_NOT_OBSERVED')
            reject('uint64-overflow-rejected',lambda:common.validate_owned({**observation,'creation_time_100ns':1<<64},base),'FILETIME_EXACT_UINT64_REQUIRED')
            reject('bool-exit-rejected',lambda:common.validate_owned({**observation,'actual_exit':False},base),'PUBLIC_CHILD_FAILED')
            for target,package in builder.TARGETS.items():
                main=builder.ntpath.join(paths['frozen_main'],*package.split('/'),'main.go');mod=builder.ntpath.join(paths['frozen_main'],'go.mod')
                refs=[fake(main),fake(mod)]
                p={'ImportPath':contract['module_path']+'/'+package,'Name':'main','Dir':builder.ntpath.dirname(main),'GoFiles':['main.go'],'Module':{'Path':contract['module_path'],'Main':True,'GoMod':mod},'Export':builder.ntpath.join(paths['gocache'],'aa','1'*64+'-d'),'BuildID':'SYNTHETIC_SOURCE_CONTROL_ONLY'}
                closure=builder.declared_closure([p],refs,paths,contract,base,common,target,True)
                check(target+'-target-closure',len(closure['input_refs'])==2 and len(closure['exports'])==1)
                reject(target+'-unfrozen-input',lambda p=p,refs=refs,target=target:builder.declared_closure([{**p,'GoFiles':['missing.go']}],refs,paths,contract,base,common,target,False),'DECLARED_BUILD_INPUT_NOT_FROZEN')
                reject(target+'-shared-export-prohibited',lambda p=p,refs=refs,target=target:builder.declared_closure([{**p,'Export':'D:/shared/gocache/file-d'}],refs,paths,contract,base,common,target,True),'EXPORT_NOT_IN_FRESH_GOCACHE')
                reject(target+'-cross-target-identity',lambda p=p,refs=refs,target=target:builder.declared_closure([p],refs,paths,contract,base,common,'backup' if target=='control' else 'control',False),'TARGET_MAIN_PACKAGE_MISSING')
                meta=('D:/synthetic/program.exe: go1.27.1\n\tpath\t'+contract['module_path']+'/'+package+'\n'+''.join('\tbuild\t'+s+'\n' for s in ['CGO_ENABLED=0','GOOS=windows','GOARCH=amd64','GOAMD64=v1','-trimpath=true'])).encode()
                check(target+'-metadata-shape',builder.verify_binary_metadata(meta,contract,target))
                reject(target+'-wrong-binary-package',lambda meta=meta,target=target:builder.verify_binary_metadata(meta,contract,'backup' if target=='control' else 'control'),'BINARY_PACKAGE_IDENTITY_MISMATCH')
                reject(target+'-fake-vcs-rejected',lambda meta=meta,target=target:builder.verify_binary_metadata(meta+b'\tbuild\tvcs.revision=fake\n',contract,target),'UNEXPECTED_EMBEDDED_VCS_IDENTITY')
            check('eight-missing-zips-mapped-statically',offline['missing_zip_count']==8 and len(offline['modules'])==19 and all(m['ziphash_matches_frozen_go_sum'] and not m['partial_present'] for m in offline['modules']))
            check('no-offline-runtime-qualification-claim',offline['result']=='STATIC_RESOURCE_MAPPING_ONLY' and offline['module_cache_copied_this_round'] is False)
            for r in prep['guard_audit_refs']:
                a=json.loads(xg.get_buffer(r['path']));check('preparation-guard-closed-'+Path(r['path']).name,a['closed'] is True and a['retained_handles_count']==0 and a['errors']==[] and a['verification']=='PASSED')
            tree=ast.parse(g.get_buffer(str(N/'old21_builder.py')))
            function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_registered_build')
            names={n.func.id for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
            attrs={n.func.attr for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
            check('runtime-uses-OwnedJobs-and-required-live-gates',{'run_owned','require_registered','require_resources','require_phase'}<=attrs)
            check('no-current-Main-inventory-call','main_inventory' not in attrs and 'main_inventory' not in names)
            check('single-explicit-guard-close-call-site',sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='close' for n in ast.walk(function))==1)
            check('guard-close-under-finally',any(isinstance(n,ast.Try) and any(isinstance(k,ast.Call) and isinstance(k.func,ast.Attribute) and k.func.attr=='close' for stmt in n.finalbody for k in ast.walk(stmt)) for n in ast.walk(function)))
            check('no-subprocess-or-SQL-imports',not any(isinstance(n,ast.Import) and any(k.name.split('.')[0] in ('subprocess','sqlite3') for k in n.names) for n in ast.walk(tree)))
            check('no-top-level-runtime-entry-call',not any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='run_registered_build' for n in tree.body))
    result={'schema':'researchos.old21-builder-author-source-controls.v1','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'guard_audit_refs':guards,'execution_branch_called':False,'Go_calls':0,'Native_product_children':0,'SQL_calls':0,'subprocess_calls':0,'synthetic_controls_are_not_runtime_qualification':True,'independent_review':'PENDING_NONAUTHOR'}
    r=save('source-controls.json',result);print(json.dumps({'source_controls_ref':r,'passed':result['passed'],'failed':result['failed'],'guard_audit_refs':guards,'runtime_branch_called':False},ensure_ascii=False))
except BaseException as e:
    save('source-controls.failure.json',{'type':type(e).__name__,'message':str(e),'script_ref':pin(Path(__file__)),'argv':sys.argv,'checks':checks,'guard_audit_refs':guards,'original_ordinal':None,'Root_assignment_required':True,'Go_exit':None,'Native_exit':None,'SQL_calls':0,'subprocess_calls':0,'automatic_retry':False})
    raise
