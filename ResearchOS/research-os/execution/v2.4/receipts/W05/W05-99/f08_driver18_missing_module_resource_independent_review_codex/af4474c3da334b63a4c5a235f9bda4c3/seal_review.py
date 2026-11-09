import ast,hashlib,json,re
from pathlib import Path
N=Path(__file__).parent
S=N.parent.parent/'f08_driver18_missing_module_resource_codex/062143fda9fb442fbdbc104f6d865833'
C=Path('D:/作品集/ResearchOS/research-os/.local/gopath/pkg/mod')
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
ast.parse(Path(__file__).read_bytes())
rows=[];pins=[]
for label in ['pprof','fileutil']:
    p=S/label/'module/go.mod';pins.append(pin(p));inside=False
    for i,line in enumerate(p.read_text(encoding='utf8').splitlines(),1):
        line=line.split('//',1)[0].strip()
        if line=='require (':inside=True;continue
        if line==')':inside=False;continue
        value=line[len('require '):] if line.startswith('require ') else line if inside else ''
        parts=value.split()
        if len(parts)!=2:continue
        mod,ver=parts;root=C/(mod+'@'+ver);md=[]
        for suffix in ['.mod','.info','.ziphash']:
            q=C/'cache/download'/mod/'@v'/(ver+suffix);rr=pin(q) if q.is_file() else None
            if rr:pins.append(rr)
            md.append({'path':str(q),'exists':q.is_file(),'ref':rr})
        rows.append({'declared_by':label,'declaration_source_ref':pins[0] if label=='pprof' else pin(p),'line':i,'module':mod,'version':ver,'source_root':str(root),'source_present':root.is_dir(),'metadata':md,'actual_required_package_or_MVS_selection':None})
save('declared-dependency-offline-delta.complete.json',{'rows':rows,'parser':'Explicit require block and single-line require grammar; no execution of Go resolver','replaces_incomplete_first_metadata_projection':'declared-dependency-offline-delta.json omitted single-line require clauses; original retained, no target executed or native error','interpretation':'Exact older declared versions may be superseded by root sqlite higher requirements; absence here is not asserted actual MVS failure.'})
save('supplemental-inputs.json',{'before':pins,'after':[pin(Path(r['path'])) for r in pins],'drift':[r for r in pins if pin(Path(r['path']))!=r]})
r=json.loads((N/'review.json').read_bytes());r['dependency_delta_ref']=pin(N/'declared-dependency-offline-delta.complete.json');r['initial_review_ref']=pin(N/'review.json');r['metadata_projection_correction']='Final includes all five declarations across both modules; original JSON audit omitted single-line requires. Checksum/member verdict unchanged.'
save('review.final.json',r)
save('tool-observations.json',{'tools':[{'chunk':'b0534f','outer_exit':0,'native_exit':None,'diagnostic':'Manifest key inventory was members, initial get(files,[]) display0 is not used as count.'},{'chunk':'713373','outer_exit':0,'native_exit':None},{'chunk':'df38ab','outer_exit':0,'native_exit':None},{'chunk':'59ab69','outer_exit':0,'native_exit':None},{'chunk':'c807c5','outer_exit':0,'python_native_exit':0,'invocation_ref':pin(N/'review.invocation.json'),'stdout_ref':pin(N/'review.stdout.raw'),'stderr_ref':pin(N/'review.stderr.raw')}],'new_origins':[],'target_executed':False})
save('handoff.json',{'schema':'researchos.driver18-missing-module-resource-independent-handoff.v1','actor':'codex:/root/command_queue_impl','decision':r['decision'],'writer':'STOPPED','review_ref':pin(N/'review.final.json'),'source_handoff_ref':r['source_handoff_ref'],'source_manifest_ref':r['source_manifest_ref'],'explicit_supplement_ref':r['explicit_nonmanifest_supplement_ref'],'dependency_delta_ref':r['dependency_delta_ref'],'checks_ref':pin(N/'checks.json'),'tool_observations_ref':pin(N/'tool-observations.json'),'checks':3609,'failed_checks':0,'ZIP_members_verified':292,'actual_review_python_native_exit':0,'actual_target_calls':0,'requested_changes':[],'new_origins':[],'open':['Driver-specific actual Go graph/runtime closure/grants','Declared offline transitive module selection','Independent upstream sumdb signature authentication'],'source_acceptance':False,'formal_increment':0,'read_only':True})
files=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
save('manifest.json',{'members':files,'self_excluded':True})
print(json.dumps({'review':pin(N/'review.final.json'),'handoff':pin(N/'handoff.json'),'manifest':pin(N/'manifest.json'),'listed':len(files),'declared_dependency_rows':len(rows),'absent_declared_sources':[x['module']+'@'+x['version'] for x in rows if not x['source_present']]},ensure_ascii=False))
