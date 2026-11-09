from pathlib import Path
import hashlib,json,difflib

here=Path(__file__).resolve().parent
root=here.parent
source=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-harness-progress-ui-20261105')
baseline=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-10-20261105')
scope=Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/harness-progress-ui/scope.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['apps/web/src/workbench.jsx','apps/web/src/workbench.css','apps/web/src/harness.js',
       'apps/web/src/harness-progress.js','apps/web/src/components/harness-run-progress.jsx','tests/ui/harness-progress.test.mjs']
oldhash={'apps/web/src/workbench.jsx':'060ce0ddaa52e955d797dc82c9a1f0372f9e9a417f1a50453fc3132680b0c125',
         'apps/web/src/workbench.css':'1eb31349a959f826f462febddc13c2ebb2e66b9afb0c18d38b8b1f1605180647',
         'apps/web/src/harness.js':'5061db6bf8610a87f3c0bd42dcfabc0bff0da6922e8c83e86d37e472ed1cc6f5'}
for name,expected in oldhash.items():assert sha(baseline/name)==expected,(name,'BASELINE_DRIFT')
for name in paths:assert (source/name).is_file(),(name,'MISSING_SOURCE')
assert sha(source/'apps/web/src/workbench.css')!='1eb31349a959f826f462febddc13c2ebb2e66b9afb0c18d38b8b1f1605180647'
css=(source/'apps/web/src/workbench.css').read_bytes();mark=b'/* Read-only Host Task/Run projection inside the Native Codex conversation. */'
cut=css.index(mark)
assert sha(baseline/'apps/web/src/workbench.css')==hashlib.sha256(css[:cut-1]).hexdigest(),'MOBILE_CSS_BASELINE_NOT_BYTE_PRESERVED'
patch=[]
for name in paths:
    before=(baseline/name).read_text(encoding='utf8').splitlines(True) if name in oldhash else []
    after=(source/name).read_text(encoding='utf8').splitlines(True)
    patch.extend(difflib.unified_diff(before,after,fromfile='a/'+name,tofile='b/'+name))
(here/'SOURCE.patch').write_text(''.join(patch),encoding='utf8',newline='\n')
manifest={'schema':'researchos.harness-progress-ui-author/1','status':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW',
  'source_root':str(source),'base_head_root_supplied':'11e0395f30a9c9249c2644a6596276a364d2c294',
  'scope_path':str(scope),'scope_sha256':sha(scope),
  'sources':[{'path':name,'baseline_sha256':oldhash.get(name,'ABSENT_BEFORE'),'final_sha256':sha(source/name),'bytes':(source/name).stat().st_size} for name in paths],
  'mobile_css_baseline_byte_preserved':True,'patch_sha256':sha(here/'SOURCE.patch'),
  'test_command':'C:/nvm4w/nodejs/node.exe --test tests/ui/harness-progress.test.mjs',
  'test_receipt_sha256':sha(here/'node-pure-test.txt'),'test_exit_code':0,'test_count':5,'test_pass':5,
  'app':0,'native':0,'cli':0,'model':0,'formal_increment':0,'product_acceptance_increment':0}
(here/'SOURCE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
(here/'WRITE_ATTEMPT.json').write_text(json.dumps({'schema':'researchos.harness-progress-ui-write-attempt/1',
  'initial_action':'Write exact leased workbench.jsx using local Python script',
  'initial_result':'DENIED_BY_FILESYSTEM_SANDBOX_PERMISSION_ERROR_NOT_EXECUTED',
  'target':str(source/'apps/web/src/workbench.jsx'),
  'retry':'Exact same scoped script with require_escalated was approved and completed once',
  'other_source_paths_modified_outside_lease':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
(here/'README.md').write_text('''# Harness progress UI source candidate — SOURCE ONLY

Native Codex conversation now shows Task submission, associated Run, tool events observed in the current event window, and Task result. It derives every stage from existing typed Task/Run/events; UNKNOWN and cancel-requested remain unresolved. A completed Task says independent review is still needed. Permission blocks translate existing reason codes into plain language, retain raw codes in a disclosure, and explain that installation/login do not establish execution permission. The projection and components do not call a bridge, send tasks, probe capabilities, or schedule work.

Only six leased paths changed. The existing mobile CSS prefix matches its baseline SHA byte-for-byte; scoped styles were appended. No App, Native, CLI, model, install, Go test or bundle build was run. Root owns build and actual zero-model runtime review. `SOURCE.patch` is relative to the exact baseline snapshot; `SOURCE.json` has file hashes. The focused Node fixture passed 5/5.
''',encoding='utf8',newline='\n')
names=['SOURCE.patch','SOURCE.json','WRITE_ATTEMPT.json','README.md','node-pure-test.txt','freeze.py']
frozen={'schema':'researchos.harness-progress-ui-frozen/1','status':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW',
  'source_json_sha256':sha(here/'SOURCE.json'),'patch_sha256':sha(here/'SOURCE.patch'),
  'files':[{'path':name,'sha256':sha(here/name),'bytes':(here/name).stat().st_size} for name in names],
  'actual_app_native_cli_model_run':'NOT_RUN'}
(here/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
archive={'root':str(root),'files':[{'path':f'{here.name}/{p.name}','sha256':sha(p)} for p in sorted(here.iterdir()) if p.is_file()],
  'status':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW'}
(root/'product-v1-harness-progress-ui-author-revision02-archive.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'source_sha256':sha(here/'SOURCE.json'),'patch_sha256':sha(here/'SOURCE.patch'),
  'frozen_sha256':sha(here/'FROZEN.json'),'archive_sha256':sha(root/'product-v1-harness-progress-ui-author-revision02-archive.json')},ensure_ascii=False))
