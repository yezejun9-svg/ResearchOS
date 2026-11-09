import pathlib,json,hashlib,re,difflib
B=pathlib.Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_run_abandonment_source_v3_codex/6e97da15b65146e5a6ef73a4804c9d12")
O=pathlib.Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492")
R=pathlib.Path(r"D:/作品集/ResearchOS/research-os")
new_test=r"""// These five cases exercise the real profile checker with typed in-memory
// copies of a persisted manifest. They are checker coverage, not top-level
// AbandonPreparedQualification coverage: the production manifest trigger is
// intentionally left enabled and no persisted immutable JSON is changed.
func TestPreparedRunAbandonmentProfileCheckerRejectsMemoryManifestPins(t *testing.T) {
    cases:=[]struct{name string; change func(Object)}{
        {"profile_ref_mismatch",func(m Object){m["admission"].(map[string]any)["profile_ref"].(map[string]any)["id"]="different-profile"}},
        {"profile_hash_mismatch",func(m Object){m["admission"].(map[string]any)["profile_hash"]=Digest([]byte("different-profile-pin"))}},
        {"plan_pin_mismatch",func(m Object){m["admission"].(map[string]any)["permission"].(map[string]any)["plan_hash"]=Digest([]byte("different-plan-pin"))}},
        {"profile_body_mismatch",func(m Object){m["admission"].(map[string]any)["profile"].(map[string]any)["model"]="different-model"}},
        {"input_pin_mismatch",func(m Object){m["input_refs"]=Empty()}},
    }
    for _,case_:=range cases {
        t.Run(case_.name,func(t *testing.T){
            _,_,r,e:=preparedFixture(t)
            expectedKey:=preparedAssertCleanProfile(t,r,e)
            before:=preparedDatabaseSnapshot(t,r)
            tx,err:=r.f.db.Begin()
            if err!=nil{t.Fatal(err)}
            defer tx.Rollback()
            run,err:=load(tx,e.ProjectID,"Run",e.RunID)
            if err!=nil{t.Fatal(err)}
            task,err:=load(tx,e.ProjectID,"Task",e.TaskID)
            if err!=nil{t.Fatal(err)}
            dispatch,err:=runtimeDispatch(tx,e.ProjectID,e.RunID,e.Epoch)
            if err!=nil{t.Fatal(err)}
            persisted,ok:=dispatch["manifest"].(map[string]any)
            if !ok{t.Fatal("persisted manifest is not a typed object")}
            persistedHash:=Hash(persisted)
            // The same real checker must accept the persisted clean baseline.
            key,err:=r.f.s.preparedRunAbandonmentProfileUpload(tx,e,run,task,persisted)
            if err!=nil || key!=expectedKey{t.Fatalf("clean checker baseline failed: %s %v",key,err)}
            mutated,err:=Decode(Bytes(persisted))
            if err!=nil{t.Fatal(err)}
            case_.change(mutated)
            if Hash(persisted)!=persistedHash || Hash(mutated)==persistedHash{t.Fatal("fault injection did not isolate a changed in-memory copy")}
            _,err=r.f.s.preparedRunAbandonmentProfileUpload(tx,e,run,task,mutated)
            preparedAssertFault(t,err,409,"STATE_CONFLICT","preparation profile immutable binding differs")
            if err=tx.Rollback();err!=nil{t.Fatal(err)}
            if after:=preparedDatabaseSnapshot(t,r);after!=before{t.Fatal("read-only checker case changed fixture database")}
        })
    }
}

"""
def ref(p):
 p=pathlib.Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
h=json.loads((B/'HDF.json').read_text(encoding='utf-8'));m=json.loads((B/'MF.json').read_text(encoding='utf-8'))
assert ref(B/'HDF.json')['sha256']=='1e9d2bd0f67ef4a12906181efaa780fe2889f7fb335b30576147f40f62eae138'
assert ref(B/'MF.json')['sha256']=='cb9c9e0d8d1a30b35b5b22e6f3eb8b4ac949933e55f2e0798f8c9c8e8d1f9c28'
inputs=[ref(B/'HDF.json'),ref(B/'MF.json')]
for x in list(m['members'].values())+m['main_base_refs']+m['supporting_source_refs']:
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];inputs.append(a)
trigger=R/'migrations/sqlite/0017_runtime_dispatch.sql';inputs.append(ref(trigger))
trigger_text=trigger.read_text(encoding='utf-8')
assert 'BEFORE UPDATE OF project,run,epoch,dispatch_key,manifest,manifest_hash,prepared_at' in trigger_text
assert "RAISE(ABORT,'dispatch identity immutable')" in trigger_text
for rel,x in m['members'].items():
 if rel.startswith('candidate-root/') or rel.startswith('contracts/'):
  dest=O/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(pathlib.Path(x['path']).read_bytes())
test_rel='candidate-root/internal/domain/prepared_run_abandonment_windows_test.go'
test=O/test_rel;old=test.read_text(encoding='utf-8')
start=old.index('func preparedChangeManifest(');end=old.index('func TestPreparedRunAbandonmentRejectsPreparationUploadAndPins(',start)
new=old[:start]+new_test+old[end:]
names=['profile_ref_mismatch','profile_hash_mismatch','plan_pin_mismatch','profile_body_mismatch','input_pin_mismatch']
for name in names:
 pattern=r'^        \{"'+re.escape(name)+r'","preparation profile immutable binding differs".*?^        \}\},\n'
 new,n=re.subn(pattern,'',new,count=1,flags=re.M|re.S);assert n==1,name
assert 'preparedChangeManifest' not in new and 'UPDATE runtime_dispatches SET manifest' not in new
assert 'DROP TRIGGER' not in new
suffix='// This test-only capability cannot be installed by an HTTP caller.'
assert new[new.index(suffix):]==old[old.index(suffix):]
old_group=old[end:old.index(suffix)]
expected_group=old_group
for name in names:
 expected_group,n=re.subn(r'^        \{"'+re.escape(name)+r'","preparation profile immutable binding differs".*?^        \}\},\n','',expected_group,count=1,flags=re.M|re.S);assert n==1
new_group=new[new.index('func TestPreparedRunAbandonmentRejectsPreparationUploadAndPins('):new.index(suffix)]
assert new_group==expected_group
assert len(re.findall(r'^        \{"[^"]+","',new_group,re.M))==7
assert len(re.findall(r'^        \{"[^"]+",func',new_test,re.M))==5
test.write_text(new,encoding='utf-8',newline='\n')
sources={};changed=[];unchanged=[];full=[];delta=[]
for rel,previous in h['source_refs'].items():
 p=O/rel;v3=pathlib.Path(previous['path']);a=v3.read_text(encoding='utf-8').splitlines(keepends=True);b=p.read_text(encoding='utf-8').splitlines(keepends=True)
 (changed if p.read_bytes()!=v3.read_bytes() else unchanged).append(rel)
 delta.extend(difflib.unified_diff(a,b,fromfile='v3/'+rel,tofile='v4/'+rel))
 target=pathlib.PurePosixPath(rel).relative_to('candidate-root');base=(R/target).read_text(encoding='utf-8').splitlines(keepends=True) if previous.get('base_sha256') else []
 full.extend(difflib.unified_diff(base,b,fromfile='a/'+str(target) if base else '/dev/null',tofile='b/'+str(target)))
 sources[rel]=dict(**ref(p),base_sha256=previous.get('base_sha256'),previous_ref={k:previous[k] for k in ['path','sha256','bytes']})
assert changed==[test_rel] and len(unchanged)==5
for name,body in [('source-diff.patch',''.join(full)),('v3-to-v4.diff.patch',''.join(delta))]:
 with (O/name).open('x',encoding='utf-8',newline='\n') as f:f.write(body)
for x in inputs:
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
put('base-refs.json',dict(input_refs=inputs,previous_HDF_ref=ref(B/'HDF.json'),previous_MF_ref=ref(B/'MF.json'),main_base_refs=m['main_base_refs'],source_refs=sources,dispatch_manifest_trigger_ref=ref(trigger),input_drift=0))
put('source-static-evidence.json',dict(schema='researchos.prepared-abandonment-v4-static-evidence.v1',source_files=6,changed_sources=changed,byte_identical_v3_sources=unchanged,contract_byte_identical_to_v3=True,production_guard_changes=0,production_trigger_changes=0,removed_unreachable_manifest_SQL_injection_helper=True,checker_only_case_names=names,checker_only_cases=5,retained_top_level_upload_and_marker_cases=7,retained_existing_success_authority_footprint_groups=True,clean_LIVE_unknown_cost_baseline_before_each_case=True,real_checker_clean_baseline_and_mutated_memory_call=True,typed_memory_copy_isolated_from_persisted_manifest=True,exact_fault_status_code_message=True,logical_DB_snapshot_unchanged_assertion=True,checker_cases_are_not_top_level_API_coverage=True,go_format_compile_test='NOT_RUN',Source_Native_SQL_provider_execution='NOT_RUN',new_failures=[],prior_failure_counters_unchanged=True,input_drift=0))
print(json.dumps(dict(source_refs=sources,changed_sources=changed,unchanged_count=len(unchanged),checker_only_cases=5,retained_top_level_cases=7,input_drift=0)))

