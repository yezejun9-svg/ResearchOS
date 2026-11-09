from pathlib import Path
import datetime,json,os,stat,types
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
s=json.loads((m.D/'resource-survey.json').read_bytes())

def attributes(path):
    try:info=path.lstat()
    except FileNotFoundError:return {'path':str(path),'exists':False}
    return {'path':str(path),'exists':True,'is_symlink':path.is_symlink(),'is_junction':path.is_junction(),'reparse':bool(getattr(info,'st_file_attributes',0)&0x400),'is_directory':stat.S_ISDIR(info.st_mode)}

caches={}
for selector,choice in s['choice']['selectors'].items():
    root=Path(choice['scratch_root'])/'gocache'
    ancestry=[attributes(parent) for parent in (root,*root.parents)]
    blocked=any(v.get('is_symlink') or v.get('is_junction') or v.get('reparse') for v in ancestry)
    counts={'files':0,'directories':0,'logical_file_bytes':0,'reparse_entries':[]}
    pending=[root] if root.is_dir() and not blocked else []
    while pending:
        directory=pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                info=entry.stat(follow_symlinks=False)
                if entry.is_symlink() or getattr(info,'st_file_attributes',0)&0x400:
                    counts['reparse_entries'].append(entry.path)
                elif stat.S_ISDIR(info.st_mode):
                    counts['directories']+=1;pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    counts['files']+=1;counts['logical_file_bytes']+=info.st_size
    caches[selector]={'path':str(root),'ancestor_metadata':ancestry,'traversal_blocked':blocked,'metadata_only':True,'file_contents_read':0,'modified_or_deleted':False,**counts}

new_base=Path(r'C:/Users/yqyyds/AppData/Local/ResearchOS/w09-native-v4')
result={'schema':'researchos.w09-cache-capacity-readonly-observation.v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_survey_ref':m.pin(m.D/'resource-survey.json'),'historical_private_caches':caches,'new_C_namespace_proposal_only':str(new_base),'new_C_base_ancestor_metadata':[attributes(p) for p in (new_base,*new_base.parents)],'existing_tool_input_directories':{name:attributes(path) for name,path in {'GOROOT':Path(s['choice']['common']['tool_refs']['go']['path']).parent.parent,'GOPATH_pkg_mod':m.R/'.local/gopath/pkg/mod'}.items()},'old_cache_content_revalidated':False,'old_qualified_unique_evidence_deleted':False,'Native_Go_SQL_model_dispatcher_TP_calls':0,'RootScope_or_lease_issued':False,'execution_grant':False,'formal_acceptance':False}
ref=m.write('cache-metadata.readonly.json',result)
print(json.dumps({'cache_metadata_ref':ref,'cache_logical_bytes':{k:v['logical_file_bytes'] for k,v in caches.items()},'cache_files':{k:v['files'] for k,v in caches.items()},'reparse_entries':{k:v['reparse_entries'] for k,v in caches.items()},'new_C_base_ancestors':result['new_C_base_ancestor_metadata'],'product_calls':0},ensure_ascii=False),flush=True)
