import ast,json,hashlib,collections
from pathlib import Path
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli43-public-resources-selected-r324';OLD=P/'integration_codex/cli43-public-resources-15ccd02e325b4d0e9384d66bb2a9d924'
RUN=P/'cli43_root_binding_preparation_revision_codex/1496044d76eb4a919217533814612807/current43_runner.v4.proposed.py'
checks=[];inputs={}
def ck(n,x):
 checks.append({'check':n,'passed':bool(x)})
 if not x:raise RuntimeError(n)
def read(p):
 p=Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if str(p) in inputs:ck('same document '+str(p),inputs[str(p)]==r)
 inputs[str(p)]=r;return b
def ref(p):read(p);return inputs[str(p)]
def verify(r):
 p=Path(r['path']);p=p if p.is_absolute() else R/p;b=read(p);ck('pin '+str(p),len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def doc(p):return json.loads(read(p))
def save(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
for p,h in [(N/'manifest.json','0837f7dee7707dc69abbb5ad8539497d8d48180d3e3c2f9c3d4202a56f8f347d'),(N/'selection-audit.json','700ef3eaf32b98da1d396ef34832eafbfd93d49764225ebaf994ee79c506654f'),(OLD/'manifest.json','421a6f850e2a1ce6a5b85210c74329775eaa373732bfda081f1e2770a07ee00a')]:ck('Root doc pin',ref(p)['sha256']==h)
m=doc(N/'manifest.json');ck('selected manifest3',m['count']==len(m['entries'])==3)
for r in m['entries']:verify(r)
a=doc(N/'selection-audit.json');full=json.loads(verify(a['parent_inventory_ref']));s=json.loads(verify(a['compiler_resources_ref']));pm=doc(OLD/'manifest.json')
parent_audit_rows=[r for r in pm['entries'] if Path(r['path']).name=='audit.json'];ck('unique parentaudit',len(parent_audit_rows)==1)
pa=json.loads(verify(parent_audit_rows[0]));ck('parent metadata stable observation',pa['before_refs']==pa['after_refs'] and pa['before_after_drift']==0)
ck('actual graph remains unknown',full['actual_compile_graph'] is None and s['actual_compile_graph'] is None and a['actual_compile_graph'] is None)
fr={r['path']:r for r in full['files']};sr={r['path']:r for r in s['files']}
ck('unique full/selected',len(fr)==len(full['files'])==34311 and len(sr)==len(s['files'])==22138)
ck('full bytes counts',sum(r['bytes'] for r in fr.values())==a['full_bytes']==994852151)
ck('selected bytes counts',sum(r['bytes'] for r in sr.values())==a['selected_bytes']==849797680)
ck('all selected original exact dictionaries',all(fr.get(k)==v for k,v in sr.items()))
go,mods,git=[Path(x['path']) for x in full['complete_public_roots']]
expected={};omit=collections.Counter()
for k,r in fr.items():
 p=Path(k);wanted=False
 if p.is_relative_to(go):
  rel=p.relative_to(go).parts;wanted=len(rel)==1 or rel[0] in ('src','bin','pkg','lib')
 elif p.is_relative_to(mods):
  rel=p.relative_to(mods).parts;wanted=len(rel)==1 or rel[0]!='cache' or p.suffix.lower()!='.zip'
 elif p.is_relative_to(git):
  rel=p.relative_to(git).parts;wanted=len(rel)==1 or any(p.is_relative_to(git/q) for q in ('cmd','mingw64/bin','mingw64/libexec/git-core','usr/bin','usr/share/locale'))
 if wanted:expected[k]=r
 else:
  for kind,root in [('go',go),('modules',mods),('git',git)]:
   if p.is_relative_to(root):omit[kind+':'+p.relative_to(root).parts[0]]+=1;break
ck('independent selection reconstructed',sr==expected)
ck('nine compiler images all selected exact',len(s['compiler_images'])==9 and all(sr.get(r['path'])==r for r in s['compiler_images']))
ck('same tool roots',all(s[k]==full[k] for k in ['GOROOT','GOPATH','GOMODCACHE','compiler_images','source_commit']))
root_union={}
for root in s['complete_public_roots']:
 p=Path(root['path']);original=[r for k,r in fr.items() if Path(k).is_relative_to(p)];original.sort(key=lambda r:r['path'].casefold())
 ck('full chosen directory '+str(p),original==root['files']);root_union.update({r['path']:r for r in root['files']})
ck('explicit332 complete selected union',len(s['explicit_metadata_files'])==332 and {**root_union,**{r['path']:r for r in s['explicit_metadata_files']}}==sr)
ck('12 recursive roots',len(s['complete_public_roots'])==12)
ck('no selected zip-download payloads',not any(Path(k).is_relative_to(mods/'cache') and Path(k).suffix.lower()=='.zip' for k in sr))
ck('empty locale accurate snapshot',not any(Path(k).is_relative_to(git/'usr/share/locale') for k in fr))
runner=read(RUN).decode();ast.parse(read(N/'derive.py'));ast.parse(runner)
ck('runner pin',ref(RUN)['sha256']=='d938098ed2820f3275ce1453bee8d0abfdcc36e1e0236f9da6f9c6f9da1bc0b4')
ck('membership before Go and each case',"need(actual == r['files'], 'Immutable compiler root membership changed')" in runner and "'Compiler root membership drift before case'" in runner)
ck('same ordering comparator',"key=lambda p: str(p).casefold()" in runner)
ck('offline explicit Go settings',all(x in runner for x in ["'GOTOOLCHAIN':'local'","'GOENV':'off'","'GOPROXY':'off'","'GOSUMDB':'off'","'CGO_ENABLED':'0'","'GOWORK':'off'"]))
ck('freshgraph ignored+embed captured',all(x in runner for x in ['IgnoredGoFiles','IgnoredOtherFiles','CompiledGoFiles','XTestEmbedFiles','Uncatalogued Go input','Uncatalogued module metadata','Uncatalogued archive']))
ck('derivation accurately no membership claim',s['membership_remeasured_in_this_derivation'] is False and a['resource_bytes_read_here']==0 and a['execution_authorized'] is False)
for r in list(inputs.values()):verify(r)
summary={'checks':len(checks),'failed':sum(not c['passed'] for c in checks),'descriptor_or_source_files_read':len(inputs),'original_inventory_rows':34311,'selected_rows':22138,'selected_bytes':849797680,'dropped_rows':len(fr)-len(sr),'selected_recursive_roots':12,'explicit_metadata':332,'actual_resource_member_bytes_read':0,'actual_recursive_membership_remeasured':False,'native_target_calls':0,'AST_parses':2}
save('audit.json',{'checks':checks,'input_refs':list(inputs.values()),'summary':summary,'omitted_counts':dict(omit)})
save('review.json',{'schema':'researchos.cli43-public-resource-selection-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'SELECTOR_STATIC_REVIEWED_CONDITIONAL_ON_FRESH_GRAPH_AND_RUNTIME_BINDING','requested_changes':[],'actual_execution_authorized':False,'source_acceptance':False,'formal_increment':0,'selected_manifest_ref':ref(N/'manifest.json'),'selection_audit_ref':ref(N/'selection-audit.json'),'compiler_resources_ref':ref(N/'compiler-resources.json'),'full_inventory_manifest_ref':ref(OLD/'manifest.json'),'full_inventory_ref':a['parent_inventory_ref'],'runner_ref':ref(RUN),'audit_ref':ref(O/'audit.json'),'findings':['No omission found in reasonably predictable Go source/tool inputs under current offline CGO-disabled Windows-amd64 plan: entire src/bin/pkg/lib, all extracted modules, root metadata and all nonZIP cache metadata are retained; all9 compiler images retain exact original rows.','12 selected recursive trees contain every original sealed member of each selected directory.332 explicit metadata rows plus those trees exactly equal22138 selected original dictionaries. No historical Go graph, executable or cache was used to infer membership.','Go api/doc/misc/test distribution,11 module download ZIP payloads, and nonselected Git directories are omitted. This is a limited selection, not the entire Git library/share tree; selected usr/share/locale had no entries in original full snapshot. Do not describe omitted Git locales/libraries as independently closed.','Current source/export catalog, new owned WORK/cache/testmain/importcfg/archive outputs and OS/PE runtime are separate obligations. Their inclusion is not proved by this compiler catalog.'],'mandatory_scope_conditions':['Bind exact selected descriptor SHA a653e0d4a5307718d5dc375564c9efc129b2a95994e0d92fc9884c929195d9fc and original421a6 manifest in actual futureRoot scope; resource-ref change changes scopeSHA and requires corresponding controller review/registration/grant, no oldscope substitution.','Before anyGo, rehash all selected member bytes and compare actual recursive membership/order to all12 root inventories. Explicit metadata must also be pinned. Unknown or changed input stops; no auto supplementation/retry.','Keep GOTOOLCHAINlocal/GOENVoff/GOWORKoff/GOPROXYoff/GOSUMDBoff/CGO0 and isolated freshGOCACHE/GOTMPDIR. A missing extracted package or need for ZIP/network is a prerequisite stop requiring newscope.','Capture actual fresh -compiled -deps -test -work -x graph including ignored/platform/embed/module inputs; new owned generated/testmain/importcfg/link/archive/exes must be frozen beforecase and all three observed phases preserved.','Review future PE/OS runtime catalog separately against exact executable paths. This selection does not prove Git/Python/Go hFile/DLL lifecycle or omitted dynamically needed resources; strict unknown-image/input rejection remains required.','Keep original3300/3600 deadlines;849797680 bytes repeatedlyhashed does not prove timefit. Runtime cost/timing remain unknown until authorized execution.','Only two held leaves remain intended; no widening to fullCLI/formal or reuse of oldfailure outcomes.'],'checks_summary':summary,'new_failure_origins':[],'status':'STOPPED'})
print(json.dumps({'output':str(O),'review':ref(O/'review.json'),'summary':summary},ensure_ascii=False))