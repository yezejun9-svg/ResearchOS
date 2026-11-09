"""Byte/hash/tree comparison only, using sealed raw Git output; never executes Git."""
import hashlib,json,pathlib,ast
P=pathlib.Path(__file__).resolve().parent;S=P.parents[1]/'desktop_exact15_integration_preparation_codex/f5ac31fcc8884b43ba7d25fc4fc75735'
def obj(n):return json.loads((S/n).read_bytes())
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
 with (P/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def tree(n):
 out={}
 for line in (S/'git'/n).read_bytes().split(b'\0'):
  if line:
   h,p=line.split(b'\t',1);m,k,b=h.decode().split();out[p.decode('utf-8')]={'mode':m,'kind':k,'blob':b}
 return out
b=tree('tree-base.stdout.raw');d=tree('tree-desktop.stdout.raw');sh=tree('tree-shared.stdout.raw');cli=tree('tree-cli.stdout.raw');parent=tree('tree-cli-parent.stdout.raw');exact=obj('exact15.json');scope=obj('scope.final.v2.proposed.json');logical=obj('logical43-tree.json')
names=[x['path'] for x in exact];blob_checks=[]
for x in exact:
 row={'path':x['path'],'before_git_matches':b.get(x['path'])==x['before_git'],'after_git_matches':d.get(x['path'])==x['after_git']}
 for kind in ['before','after']:
  r=x['before_blob_ref'] if kind=='before' else x['final_blob_ref']
  if r is None:continue
  body=pathlib.Path(r['path']).read_bytes();row[kind+'_SHA']=hashlib.sha256(body).hexdigest()==x[kind+'_sha256'];row[kind+'_bytes']=len(body)==x[kind+'_bytes'];row[kind+'_Git_blob']=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==x[kind+'_git']['blob']
 blob_checks.append(row)
cli_delta={k for k in set(parent)|set(cli) if parent.get(k)!=cli.get(k)};shared_delta={k for k in set(b)|set(sh) if b.get(k)!=sh.get(k)}
expected43=dict(sh)
for k in cli_delta:
 if cli[k]:expected43[k]=cli[k]
all_delta={k for k in set(b)|set(d) if b.get(k)!=d.get(k)}
attrs=obj('attributes-proof.json');protected=obj('protected-public-paths.planned.json');patch=(S/'git/exact15-patch.stdout.raw').read_bytes()
patch_names=[]
for line in patch.splitlines():
 if line.startswith(b'diff --git a/'):
  a,z=line[len(b'diff --git a/'):].split(b' b/',1)
  if a!=z:raise RuntimeError('Unexpected rename in declared exact15 patch')
  patch_names.append(a.decode('utf-8'))
audit={'blob_checks':blob_checks,'before_existing':sum(x['before_git'] is not None for x in exact),'before_absent':sum(x['before_git'] is None for x in exact),'shared_delta_count':len(shared_delta),'CLI_delta_count':len(cli_delta),'combined43_count':len(shared_delta|cli_delta),'desktop_intersection':sorted(set(names)&(shared_delta|cli_delta)),'combined58_count':len(set(names)|shared_delta|cli_delta),'logical43_exact_equal':expected43==logical,'source_desktop_delta_total':len(all_delta),'nonexact15_delta_count':len(all_delta-set(names)),'nonexact15_all_receipts':all(k.startswith('execution/') for k in all_delta-set(names)),'patch_names_exact':patch_names==names,'patch_SHA':hashlib.sha256(patch).hexdigest(),'protected_count':len(protected),'root_attributes_in_protected':protected.count('.gitattributes'),'main_Mu_protected':'.local/w0599-main-stream-integration-r268/mu-worker.mjs' in protected,'SDK_profile_path_count':sum('mu' in x.lower() or 'node_modules' in x.lower() for x in protected),'exact15_not_protected':not set(names)&set(protected),'rootattrs_git_equal':b['.gitattributes']==d['.gitattributes']==sh['.gitattributes']==cli['.gitattributes']==attrs['git_row'],'actual_Git_calls':0,'actual_target_imports':0}
save('composition-and-patch-audit.json',audit)
save('controller-lines.json',{'controller_ref':ref(S/'integrate_desktop15.py'),'launcher_ref':ref(S/'launch_desktop15.py'),'controller_numbered':list(enumerate((S/'integrate_desktop15.py').read_text(encoding='utf-8').splitlines(),1)),'launcher_numbered':list(enumerate((S/'launch_desktop15.py').read_text(encoding='utf-8').splitlines(),1))})
print(json.dumps({k:v for k,v in audit.items() if k!='blob_checks'},ensure_ascii=False))
