import runner as r
import json
m=r.read(r.S/'source-manifest.revision02.json')
scope=r.ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp510/qualification-projection-A-r2-independent-review-scope.json'
inputs=[{'path':str(scope),'expected':'88b7a386b4a4512d8d60033a4e17c3e9531b2b9edb93cf6f2c06815a358242e8','actual':r.sha(scope)},{'path':str(r.S/'source-manifest.revision02.json'),'expected':'9acfbe0094a73d4a994f44bf0bcb9714470871fd200142960172a67309a8caa6','actual':r.sha(r.S/'source-manifest.revision02.json')}]
card=r.read(scope)
for key in ['prior_independent_review_ref','construction_scope_ref','original_scope_ref']:
 x=card[key];p=r.ROOT/x['path'];inputs.append({'path':str(p),'expected':x['sha256'],'actual':r.sha(p)})
for x in m['source_paths']:
 p=r.W/x['path'];inputs.append({'path':str(p),'expected':x['sha256'],'actual':r.sha(p)})
for name,x in m['patches'].items():
 p=r.S/name;inputs.append({'path':str(p),'expected':x['sha256'],'actual':r.sha(p)})
for x in m['recorded_commands']:
 for suffix,field in [('.command.json','command_sha256'),('.stdout.raw','stdout_sha256'),('.stderr.raw','stderr_sha256')]:
  p=r.S/(x['tag']+suffix);inputs.append({'path':str(p),'expected':x[field],'actual':r.sha(p)})
for x in inputs:x['matches']=x['expected']==x['actual']
r.save('input-hashes.json',inputs)
assert all(x['matches'] for x in inputs)
r.run('full-A-diff',['git','--no-optional-locks','diff','--binary',m['main_base_commit'],m['commit']],show=False)
r2=r.run('r2-full-diff',['git','--no-optional-locks','diff','--binary',m['base_commit'],m['commit']],show=False)
restricted=r.run('A-restricted10-diff',['git','--no-optional-locks','diff','--binary',m['main_base_commit'],m['commit'],'--',*[x['path'] for x in m['source_paths']]],show=False)
paths=r.run('full-A-paths',['git','--no-optional-locks','diff','--name-only',m['main_base_commit'],m['commit']],show=False).decode().splitlines()
r.save('patch-scope-audit.json',{'r2_patch_exact':r2==(r.S/'r2-diff-from-525.binary.patch').read_bytes(),'author_named_full_patch_is_only10paths':restricted==(r.S/'r2-full-diff-from-4f.binary.patch').read_bytes(),'whole_A_paths':paths,'whole_A_path_count':len(paths),'r2_path_count':len(m['source_paths'])})
command=r.read(r.S/'r2-final-targeted.command.json')
r.run('independent-targeted',command['argv'],show=False)
r.run('independent-build',[r.GO,'build','-o',str(r.T/'control-review.exe'),'./apps/control'],show=False)
r.guards('after')
