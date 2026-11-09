import os,json,hashlib,re
from pathlib import Path
N=Path(__file__).parent
R=N.parent.parent
reads={}
def need(v,m):
    if not v:raise RuntimeError(m)
def key(p):return os.path.normcase(os.path.normpath(str(Path(p).absolute())))
def pin(p):
    p=Path(p);b=p.read_bytes();d={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};reads[key(p)]=d;return d
def load(p,expected=None):
    p=Path(p);b=p.read_bytes();d={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    if expected:need(d['sha256']==expected['sha256'] and d['bytes']==expected['bytes'],'PIN '+str(p))
    reads[key(p)]=d;return json.loads(b)
def save(name,v):
    with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
scopepath=R/'integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/scope_registration.json'
s=load(scopepath);c=load(s['compiler_resources_ref']['path'],s['compiler_resources_ref']);rt=load(s['runtime_resources_ref']['path'],s['runtime_resources_ref'])
base=R/'f08_driver18_execution_preparation_codex/d8a13bae58b341d8b28c0092527df4fc'
contract=load(base/'resource-and-authority-contract.json');fixed=load(base/'fixed-inputs.json')
h=load(R/'f08_driver18_execution_revision_preparation_codex/fb328e152ae54da6b4be24cbc3b94ece/handoff.json')
for field in ['controller_ref','scope_ref']:
    rr=h[field];pp=pin(rr['path']);need(pp['sha256']==rr['sha256'] and pp['bytes']==rr['bytes'],'V3_PIN')
fl=load(fixed['fork_lock_ref']['path'],fixed['fork_lock_ref']);ol=load(fixed['original_lock_ref']['path'],fixed['original_lock_ref']);fh=load(fixed['fork_handoff_ref']['path'],fixed['fork_handoff_ref'])
mirror=load(R/'f08_sqlite_mirror_zip_resource_codex/fc99cb027905472881ba5de3ecd6df84/handoff.json')
load(mirror['audit_ref']['path'],mirror['audit_ref']);load(mirror['report_ref']['path'],mirror['report_ref'])
for field in ['fork_mod_ref','consumer_mod_ref','old_mod_ref','fork_sum_ref']:
    p=pin(fixed[field]['path']);need(p['sha256']==fixed[field]['sha256'],'MODULE_PIN')
cat={key(row['path']):row for row in c['files']}
cache=Path(c['GOMODCACHE']);deps=contract['direct_dependencies_from_actual_go_mod']|contract['indirect_dependencies_from_actual_go_mod']
rows=[];copies=[];readmods=[];missing=[];unlisted=[]
def metadata(m,v):
    root=cache/'cache/download'/m/'@v'
    observed=[]
    for ext in ['.mod','.info','.ziphash','.zip']:
        p=root/(v+ext);present=p.is_file();r=cat.get(key(p))
        current=None
        if present and ext!='.zip':current=pin(p)
        if current and r:need(current['sha256']==r['sha256'] and current['bytes']==r['bytes'],'METADATA_DRIFT '+str(p))
        observed.append({'suffix':ext,'path':str(p),'exists':present,'selected_ref':r,'current_small_metadata_ref':current,'payload_rehashed':False if ext=='.zip' else present})
        if current:copies.append({'relative_path':p.relative_to(cache).as_posix(),'ref':current,'source':'current small metadata, selected membership separately recorded'})
    return observed
for mod,version in deps.items():
    root=cache/(mod+'@'+version);prefix=key(root)+os.sep
    selected=[v for k,v in cat.items() if k.startswith(prefix)]
    names=[];aliases=[]
    if root.is_dir():
        for here,dirs,files in os.walk(root,followlinks=False):
            for name in dirs+files:
                p=Path(here)/name
                if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:aliases.append(str(p))
            need(not aliases,'REPARSE_MODULE '+str(root))
            names.extend(str(Path(here)/f) for f in files)
    actualkeys={key(p) for p in names};selectedkeys={key(p['path']) for p in selected}
    extra=sorted(actualkeys-selectedkeys);absent=sorted(selectedkeys-actualkeys)
    modfile=root/'go.mod';modref=None;modtext=None
    if modfile.is_file():modref=pin(modfile);modtext=modfile.read_text(encoding='utf8',errors='strict');readmods.append({'module':mod,'version':version,'ref':modref,'raw_text':modtext})
    knownversions=sorted(p.name for p in root.parent.iterdir() if p.name.startswith(root.name.split('@')[0]+'@')) if root.parent.is_dir() else []
    row={'module':mod,'version':version,'role':'direct' if mod in contract['direct_dependencies_from_actual_go_mod'] else 'indirect','actual_source_root':str(root),'exists':root.is_dir(),'current_membership_count':len(names),'selected_file_count':len(selected),'selected_refs_content_rehashed':False,'current_not_in_selected':extra,'selected_not_on_disk':absent,'actual_available_versions':knownversions,'go_mod_ref':modref,'download_metadata':metadata(mod,version),'source_membership_equal':actualkeys==selectedkeys and bool(names)}
    rows.append(row)
    if not row['exists']:missing.append({'module':mod,'version':version,'path':str(root),'reason':'NO_EXTRACTED_SOURCE_AT_REQUIRED_VERSION'})
    unlisted+=extra
    copies.extend({'relative_path':Path(r['path']).relative_to(cache).as_posix(),'ref':{k:r[k] for k in ('path','sha256','bytes')},'source':'inherited selected catalog; file bytes not rehashed in this read-only map'} for r in selected)
sqlmetadata=metadata('modernc.org/sqlite','v1.60.1')
# Only destination metadata is included for sqlite, never source files: controller copies pristine lock first.
need(not any(x['relative_path'].startswith('modernc.org/sqlite@') for x in copies),'PRISTINE_OVERWRITE')
copykeys=[x['relative_path'].casefold() for x in copies];need(len(copykeys)==len(set(copykeys)),'COPY_DEST_DUPLICATE')
source_original_keys={key(x['path']) for x in ol['files']};selected_orig=source_original_keys & set(cat)
source_root=str(Path(ol['files'][0]['path']).parents[len(Path(ol['files'][0]['relative_path']).parts)-1])
go_path=Path(c['GOROOT'])/'bin/go.exe';go=cat.get(key(go_path));need(go is not None,'GO_REF')
py=s['python_ref'];need(any(key(r['path'])==key(py['path']) and r['sha256']==py['sha256'] for r in rt['files']),'PYTHON_IN_RUNTIME')
save('dependency-map.json',{'declared_count':len(deps),'dependencies':rows,'missing_required_source':missing,'additional_current_files_not_in_selected':unlisted,'method':'Read sealed selected metadata; enumerate only 11 explicit module roots without content rehash; pin exact go.mod and small .mod/.info/.ziphash. Not an actual Go resolution graph.'})
save('offline-copy-map.proposed.json',{'not_a_resource_catalog':True,'authorization':False,'files':copies,'sqlite_metadata':sqlmetadata,'mirror_zip_optional_mapping':{'relative_path':'cache/download/modernc.org/sqlite/@v/v1.60.1.zip','ref':mirror['archive_ref'],'source':'existing public mirror original raw, inherited verified pin; not rehashed now','requires_future_files_membership':True},'pristine_source_separate':fixed['original_lock_ref'],'fork_source_separate':fixed['fork_lock_ref'],'do_not_copy_or_overwrite':'modernc.org/sqlite@v1.60.1/** by offline_modcache_copies','missing_modules':missing})
save('dependency-go-mod-evidence.json',readmods)
save('resource-shape-map.json',{'not_a_binding_or_grant':True,'compiler_basis_ref':s['compiler_resources_ref'],'runtime_basis_ref':s['runtime_resources_ref'],'files':{'algorithm':'Root selects/deduplicates inherited public GoRoot files, approved runtime images/Python inputs, exact11 deps plus necessary offline metadata and all new driver controls. Add any currently missing dependency resources only with explicit new pins. Verify same path collisions have identical sha/bytes.','compiler_basis_count':len(c['files']),'runtime_basis_count':len(rt['files']),'rehashed_whole_tree':False,'no_reuse_of_actual_CLI_compile_graph':True},'go':go,'python':py,'GOROOT':c['GOROOT'],'compiler_images':c['compiler_images'],'offline_modcache_copies_map_ref':pin(N/'offline-copy-map.proposed.json'),'split_source':{'fork':{'lock_ref':fixed['fork_lock_ref'],'files':len(fl['files']),'destination':'fresh work/fork; then one new test overlay'},'pristine':{'lock_ref':fixed['original_lock_ref'],'files':len(ol['files']),'selected_catalog_membership_count':len(selected_orig),'destination':'fresh work/modcache/modernc.org/sqlite@v1.60.1','never_override':True}},'runtime_limit':'1250 is sealed CLI metadata coverage, not a new driver execution closure. Replace/add driver controller/launcher/gate/Root wrappers actual refs; Python __file__/__cached__/loaded DLL still needs future actual point-in-time validation.','OPEN':['Missing declared source dependencies shown by dependency-map; no network attempted.','Actual transitive selected versions and compiler source graph, WORK/archive/generated/exes all NOT_RUN.','Driver-specific runtime controls/authority adapter/Root scope grants absent.','Offline cache metadata closure beyond declared11 requires actual pinned go graph; no claim complete based only on directory presence.','I17 unchanged OPEN_NOT_AUTHORIZED.'],'source_adoption':False,'SQL24_permission':False})
save('inputs.before.json',list(reads.values()))
after=[]
for r in list(reads.values()):
    p=Path(r['path']);b=p.read_bytes();nr={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};need(nr==r,'READ_INPUT_DRIFT');after.append(nr)
save('inputs.after.json',after)
print(json.dumps({'dependencies':[{'module':x['module'],'exists':x['exists'],'current':x['current_membership_count'],'selected':x['selected_file_count'],'extras':len(x['current_not_in_selected']),'absent':len(x['selected_not_on_disk'])} for x in rows],'missing':missing,'offline_copy_entries':len(copies),'new_input_metadata_pins':len(after),'whole_tree_rehashed':False},ensure_ascii=False))
