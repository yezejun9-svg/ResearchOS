"""One-shot Source preparation. No subprocess/Go/SQL/product calls."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types

N=Path(__file__).resolve().parent
R=Path(r'D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
D=B/'schema21_original_resource_discovery_source_codex/discovery-20261010-01'
F=B/'fresh_main23_programme_builder_source_codex/main23b-20261009-01'
FR=B/'fresh_main23_programme_builder_independent_source_review_codex/src-review-20261009-01'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
COMMIT='f6e4a0ed54d697c7214a75743cd1b83dc3685ddb'
TREE='9696c3a456a4786cbb5518c75ead66e6d8120a83'
AUTHOR='codex:/root/native_temp_independent_review'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=sha(b),bytes=len(b))
def write_bytes(p,b,readonly=False):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    if readonly:os.chmod(p,stat.S_IREAD)
    return dict(path=p.as_posix(),sha256=sha(b),bytes=len(b))
def save(name,x):return write_bytes(N/name,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def fixed(p,h,n):return dict(path=p.as_posix(),sha256=h,bytes=n)

guard_ref=fixed(GUARD,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
# Exact-pinned bootstrap import is the sole prerequisite to opening its read guard.
raw=GUARD.read_bytes();assert len(raw)==guard_ref['bytes'] and sha(raw)==guard_ref['sha256']
gm=types.ModuleType('old21_author_guard');exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
audits=[]
@contextmanager
def held(refs,name):
    g=gm.SourceReadGuard(total_cap=512*1024*1024)
    try:
        g.acquire(refs);yield g
    finally:
        primary=sys.exc_info()[0]
        a=g.close(); ar=save(name+'.guard.closed.json',a);audits.append(ar)
        if primary is None:assert a['verification']=='PASSED' and a['closed'] is True and a['retained_handles_count']==0 and a['errors']==[]

metadata=[guard_ref,
 fixed(D/'HDF.json','113bdd61162aa5b44653cd302d2e977aceb73aeda75a08764e74bb4d23e9918c',3223),
 fixed(D/'MF.json','574fa8c2a217c4d2247e197b3e1bc07812241011ef86f4c127ab9bff566b443e',30523),
 fixed(D/'discovery-report.json','7f46350ad34c4e7fb32fb853f356a58311bd9e7910c36de68ff1bc17c2dd5d2a',6618),
 fixed(D/'root-build-input-scope.json','abe364a16d67818cf2f06e809d8c94b985215d54ad8bb32abf22afa12c2ed1f2',279003),
 fixed(D/'source-object-inventory.json','3ca1c75fa246ed2cbc455e167cf9aff953058b57899fb1db9fad58949cdb27d6',284166),
 fixed(D/'git-commands.actual.json','4554784f6c99cecf4cb62668351593576df4e3bb47722f09a59a982b0a739309',7355),
 fixed(F/'HDF.json','7b1b949afd7d3508e0a93171b51413229dda9aac755f2de9f9262b1dcaf259df',3571),
 fixed(F/'MF.json','cdca73c276b042c3773d27d5fd226e8e50ac120e3d0327bb31f9b6d134a08f08',3415),
 fixed(F/'contract.json','0ef3a33c4b483e8a265ba63125aff5790cdf79c666cb12fed2fbb23906ac69f7',8172),
 fixed(F/'main23_builder.py','8696b8f25d9ae7becdd89ec6d4964bd7a3d5660461c91f5d4e0d2c6f92f28659',24907),
 fixed(F/'input-manifest.json','f9854d072706eaf8dedaf0463b319a1b9f6cb7baefa7e55740d29d812942a3b8',5486601),
 pin(FR/'source-decision.json'),pin(FR/'HDF.json'),pin(FR/'MF.json'),pin(N/'old21_builder.py')]
try:
    with held(metadata,'metadata') as g:
        read=lambda p:json.loads(g.get_buffer(str(p)))
        dc=read(D/'root-build-input-scope.json');di=read(D/'source-object-inventory.json');dr=read(D/'discovery-report.json')
        fc=read(F/'contract.json');fm=read(F/'input-manifest.json');review=read(FR/'source-decision.json')
        assert dc['source_commit']==COMMIT and dc['source_tree']==TREE
        assert review['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and review['independent_non_author'] is True and review['review_author']!=AUTHOR
        assert review['author_builder_ref']==next(x for x in metadata if x['path']==(F/'main23_builder.py').as_posix())
        assert review['author_input_manifest_ref']==next(x for x in metadata if x['path']==(F/'input-manifest.json').as_posix())
        selected=dc['control_backup_and_runtime_union'];assert len(selected)==272
        candidate=next(x for x in di if x['commit']==COMMIT);assert candidate['tree']==TREE and candidate['domain_new_installs_session_addon'] is True
        commands=read(D/'git-commands.actual.json');batch_record=[x for x in commands if '--batch' in x['argv']][-1]
        with held([batch_record['stdout'],batch_record['stdin']],'historical_blob_input') as bg:
            batch=bg.get_buffer(batch_record['stdout']['path']);request=bg.get_buffer(batch_record['stdin']['path']).decode().splitlines()
            data={};pos=0
            for obj,requested in zip(candidate['source_objects'],request,strict=True):
                end=batch.index(b'\n',pos);oid,kind,length=batch[pos:end].decode().split();length=int(length);pos=end+1
                b=batch[pos:pos+length];pos+=length+1
                assert kind=='blob' and oid==requested==obj['git_blob'] and len(b)==obj['bytes'] and sha(b)==obj['sha256']
                assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
                data[obj['git_path']]=b
            assert pos==len(batch)
            objects=[];historical_items=[]
            for obj in selected:
                name=obj['git_path'];assert not name.startswith('/') and ':' not in name and '\\' not in name and all(x not in ('','..','.') for x in name.split('/'))
                b=data[name];assert sha(b)==obj['sha256'] and len(b)==obj['bytes']
                r=write_bytes(N/'frozen_source'/name,b,readonly=True)
                objects.append({**obj,'ref':r});historical_items.append({'kind':'historical_source','relative_path':name,'ref':r})
        frozen_ref=save('frozen-source-manifest.json',{'schema':'researchos.old21-original-frozen-source.v1','source_commit':COMMIT,'source_tree':TREE,'objects':objects,'source_scope_ref':next(x for x in metadata if x['path']==(D/'root-build-input-scope.json').as_posix()),'source_inventory_ref':next(x for x in metadata if x['path']==(D/'source-object-inventory.json').as_posix()),'original_git_batch_ref':batch_record['stdout'],'blob_algorithm':'git SHA1 over blob header plus complete original bytes; independent SHA256 and byte length for every file','qualification':'MATERIALIZED_SOURCE_ONLY_NOT_BUILT_OR_PROGRAMME_QUALIFIED'})
        reused=[x for x in fm['items'] if x['kind'] in ('module','toolchain')]
        resources=[x['ref'] for x in reused]+[fc['base_helper_ref'],fc['owned_job_ref'],fc['toolchain_lock_ref']]
        with held(resources,'module_tool_resources') as rg:
            lock=json.loads(rg.get_buffer(fc['toolchain_lock_ref']['path']))
            assert sha(rg.get_buffer(fc['go_ref']['path']))==lock['tools']['go']['sha256']==fc['go_ref']['sha256']
            versions=dict(re.findall(r'^\s*([a-zA-Z0-9./_-]+)\s+(v\S+)',data['go.mod'].decode(),re.M))
            assert versions==fc['module_versions'] and len(versions)==19 and re.search(r'^go 1\.27\.1$',data['go.mod'].decode(),re.M)
            module_root=R/'.local/gopath/pkg/mod';module_index={x['relative_path']:x for x in reused if x['kind']=='module'}
            module_mapping=[];sums=data['go.sum'].decode().splitlines()
            for module,version in versions.items():
                prefix=module+'@'+version
                expected=next(x.split()[2] for x in sums if x.split()[:2]==[module,version])
                rows={suffix:module_index['cache/download/'+module+'/@v/'+version+suffix]['ref'] for suffix in ['.mod','.info','.ziphash']}
                assert rg.get_buffer(rows['.ziphash']['path']).decode().strip()==expected
                assert prefix+'/go.mod' in module_index
                partial=module_root/'cache/download'/module/'@v'/(version+'.partial');zipfile=partial.with_suffix('.zip')
                assert not partial.exists()
                module_mapping.append({'module':module,'version':version,'expanded_directory':(module_root/prefix).as_posix(),'selected_source_files':sum(x.startswith(prefix+'/') for x in module_index),'expanded_go_mod_ref':module_index[prefix+'/go.mod']['ref'],'cache_metadata_refs':rows,'zip_present':zipfile.is_file(),'partial_present':False,'ziphash_matches_frozen_go_sum':True})
            cache_path=Path(fc['goroot'])/'src/cmd/go/internal/modfetch/cache.go';cache_ref=next(x['ref'] for x in reused if x['ref']['path']==cache_path.as_posix())
            cache_raw=rg.get_buffer(cache_ref['path']).decode()
            assert 'func DownloadDir(' in cache_raw and 'ziphash file is missing' in cache_raw and 'not completely extracted' in cache_raw
            imports=sorted(set(candidate['external_imports']));coverage=[]
            for imp in imports:
                module=max((m for m in versions if imp==m or imp.startswith(m+'/')),key=len)
                directory=module+'@'+versions[module]+imp[len(module):]
                names=[p for p in module_index if Path(p).parent.as_posix()==directory and p.endswith('.go') and not p.endswith('_test.go')]
                coverage.append({'import':imp,'module':module,'version':versions[module],'selected_non_test_go_files':names,'present_in_reused_source_manifest':bool(names)})
            assert all(x['present_in_reused_source_manifest'] for x in coverage)
            cache_facts=save('offline-module-static-map.json',{'schema':'researchos.old21-offline-module-source-map.v1','modules':module_mapping,'missing_zip_count':sum(not x['zip_present'] for x in module_mapping),'direct_external_package_coverage':coverage,'locked_go_download_dir_source_ref':cache_ref,'conditions':'DownloadDir checks expanded dir, absence of .partial and presence of .ziphash. Existing .zip archives are not required by that path. Exact selected .mod/.info/ziphash and frozen go.sum are included.','result':'STATIC_RESOURCE_MAPPING_ONLY','limits':'No Go list/build executed. Selected source is sparse; actual compiler/tag/embed/transitive closure must fit pre-held refs, otherwise stop. Cache metadata existence and ziphash text are not a runtime or official module-content qualification.','module_cache_copied_this_round':False,'toolchain_copied_this_round':False})
        items=historical_items+reused
        manifest_ref=save('input-manifest.json',{'schema':'researchos.old21-builder-frozen-inputs.v1','source_commit':COMMIT,'source_tree':TREE,'items':items,'frozen_source_manifest_ref':frozen_ref,'reused_resource_manifest_ref':review['author_input_manifest_ref'],'reused_resource_review_ref':next(x for x in metadata if x['path']==(FR/'source-decision.json').as_posix()),'offline_static_map_ref':cache_facts,'counts':{k:sum(x['kind']==k for x in items) for k in ['historical_source','module','toolchain']},'bytes':{k:sum(x['ref']['bytes'] for x in items if x['kind']==k) for k in ['historical_source','module','toolchain']},'shared_GOCACHE_inputs':0,'actual_compiler_closure':'NOT_RUN_PENDING_ROOT'})
        byname={x['git_path']:x['ref'] for x in objects}
        runtime={n:byname[n] for n in candidate['runtime_paths']}
        public_names=['apps/control/main.go','internal/domain/store.go','internal/domain/client_session_fence.go','internal/store/sqlite.go','ops/backup/main.go','go.mod','go.sum']
        contract={'schema':'researchos.old21-programme-builder-contract.v1','status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION','source_author':AUTHOR,'builder_ref':next(x for x in metadata if x['path']==(N/'old21_builder.py').as_posix()),'schema_version':21,'source_commit':COMMIT,'source_tree':TREE,'historical_source_root':(N/'frozen_source').as_posix(),'historical_source_file_count':len(objects),'module_source_root':module_root.as_posix(),'module_path':fc['module_path'],'module_versions':versions,'goroot':fc['goroot'],'go_ref':fc['go_ref'],'toolchain_lock_ref':fc['toolchain_lock_ref'],'common_builder_ref':review['author_builder_ref'],'common_source_review_ref':next(x for x in metadata if x['path']==(FR/'source-decision.json').as_posix()),'base_helper_ref':fc['base_helper_ref'],'source_guard_ref':guard_ref,'owned_job_ref':fc['owned_job_ref'],'input_manifest_ref':manifest_ref,'frozen_source_manifest_ref':frozen_ref,'runtime_source_refs':runtime,'public_bootstrap_source_refs':{n:byname[n] for n in public_names},'output_parent':(B/'integration_codex').as_posix(),'exact_output_basename':'old21-build-<32lowerhex>','request_fields':['case_id','output_root'],'entry':'old21_builder.run_registered_build(contract_ref, request_ref, live_root_scope)','Root_caller_interface':['require_registered(contract_ref, request_ref, source_author=...)','require_resources(contract_ref, input_manifest_ref)','require_phase(phase, request_ref, output_root)','receipt_context()'],'Root_mandatory_boundary':['Actual live owner/scope/current lease and registration; no JSON authority','Independent non-author review of exact old21 Source HDF/MF/builder/contract/frozen source and resource manifest','Caller bootstrap holds leaf, contract, helper, source guard and owned job before entry','Qualified Python, loaded-native DLL, Go1.27.1 toolchain and child loader/resource closure held through last Job and guard close','require_resources returns exact Source review, resource qualification, runtime manifest and actual outer host binding refs, with independent reviewer actor','Full original Root host call/output captured losslessly, including integer FILETIME; source-only mocked observations cannot satisfy actual host binding','Every phase revalidates live lease and unchanged resource binding, including complete phase','Root preserves returned failure state if local publication fails, captures outer full IO, assigns ordinal, and does not retry automatically'],'resource_binding_keys':['input_manifest_ref','source_review_ref','resource_qualification_ref','runtime_manifest_ref','outer_host_binding_ref','source_author','reviewer_actor'],'phases':['prepare','go-version','control-declared','control-export','control-build','control-inspect','backup-declared','backup-export','backup-build','backup-inspect','complete'],'Go_child_process_limit':9,'product_program_execution_limit':0,'SQL_execution_limit':0,'go_environment_policy':'Inherited FB allowlist, offline modules, fixed windows/amd64/v1 CGO0, GOTOOLCHAIN local, GOENV/GOWORK off, -mod=readonly -trimpath -buildvcs=false; unique empty GOCACHE, no shared cache copied.','module_copy_policy':'Future actual builder makes only pinned sparse module-source/metadata copy under owned output; this Source preparation copies no cache/toolchain. Additional empty .lock files only.','source_policy':'Exact original Git blob+SHA256+bytes for every historical source; exact272-file membership, original consecutive1..21 SQL plus session addon and public bootstrap source pins; never read current Main Source.','process_policy':'Pinned OwnedJobs suspended primary assigned before resume, exact integer PID/FILETIME, Job idle and handles closed. Descendant individual exit values remain null.','guard_policy':'Each acquired guard has one explicit serialized close in finally, audit retained with closed true and zero retained handles; no automatic retry. Existing guard may internally unwind a failed acquire.','program_outputs':['old21-control.exe','old21-backup.exe'],'qualification':'Build candidates only; qualification_ref=null until different-author actual provenance review. No historical formal release or old21 Case claim.','public_bootstrap_future_contract':{'command':['<qualified-old21-control.exe>','--bootstrap-owner','--credential-file','<new-scope-private-owner-output>'],'cwd':'<matching-frozen-original-old21-source-root>','environment':{'RESEARCHOS_DATA_DIR':'<new-isolated-data-root>'},'numbered_migrations':list(range(1,22)),'session_addon':'migrations/sqlite/next_v24_sessions.sql','session_fence':'installClientSessionFence(ctx, tx, false) in domain.New before same transaction commit','admin_exits_before_http_and_runtime_coordinator':True,'executed_this_round':False},'branch_local_open':['old21 actual build and independent programme qualification','old21 public bootstrap/backup/restore and database schema observations','21to22 product route compatibility and formal old21 Case'],'active_TP':False,'runtime_grant':False,'formal_acceptance':False,'source_self_acceptance':False,'Root_failure_counter_owner':'codex:/root','Root_counter_last_reported':1066}
        save('contract.json',contract)
        save('source-adaptation.json',{'from_accepted_builder':review['author_builder_ref'],'prior_independent_review_ref':contract['common_source_review_ref'],'changes':['Historical f6e4a0 source-only candidate replaces current Main inventory; no Main source calls','Dual control/backup target projections and metadata/closure checks, nine bounded Go children','Exact Git object+SHA256 validation and all1..21 SQL/addon/publicbootstrap refs','Live require_resources and actual host binding required before any case creation and each phase','Raw stream/result retention handles a thrown OwnedJobs call without replacing primary failure','All runtime guards explicitly closed once in final reverse-order serialization'],'reused_pure_functions':['relative_file','below','environment','validate_owned','parse_json_stream','tree_refs','assert_pins','copy_inputs','verify_frozen_inventory'],'not_called_from_reused_builder':['run_registered_build','main_inventory','compile_request','declared_closure','verify_binary_metadata'],'new_source_author':AUTHOR,'independent_reviewer':'PENDING_DIFFERENT_SOURCE_AUTHOR','execution_branch_called':False})
    save('source-preparation.json',{'status':'SOURCE_PREPARED_PENDING_SOURCE_CONTROLS_AND_INDEPENDENT_REVIEW','metadata_refs':metadata,'guard_audit_refs':audits,'historical_source_files':len(objects),'module_files':len([x for x in reused if x['kind']=='module']),'toolchain_files':len([x for x in reused if x['kind']=='toolchain']),'missing_zip_count':sum(not x['zip_present'] for x in module_mapping),'Go_calls':0,'subprocess_calls':0,'Native_product_children':0,'SQL_calls':0,'runtime_branch_called':False,'writes_only':N.as_posix()})
    print(json.dumps({'contract_ref':pin(N/'contract.json'),'frozen_source_manifest_ref':frozen_ref,'input_manifest_ref':manifest_ref,'guard_audit_refs':audits,'historical_source_files':len(objects),'missing_zip_count':sum(not x['zip_present'] for x in module_mapping),'Go_Native_SQL_subprocess_calls':0},ensure_ascii=False))
except BaseException as e:
    save('source-preparation.failure.json',{'type':type(e).__name__,'message':str(e),'script_ref':pin(Path(__file__)),'argv':sys.argv,'guard_audit_refs':audits,'original_ordinal':None,'Root_assignment_required':True,'Go_exit':None,'Native_exit':None,'SQL_calls':0,'subprocess_calls':0,'automatic_retry':False})
    raise
