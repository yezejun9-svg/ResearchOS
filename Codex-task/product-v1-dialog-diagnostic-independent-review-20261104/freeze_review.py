from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
A=R.parent/'product-v1-real-electron-tree-diagnostic-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
 p=R/name
 assert not p.exists(),str(p)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pins={'real-electron-flow.mjs':'a7e38ceecd654e63b6689556c18ec57346b8ae4390068bcd3e80d28a4ede692d','choose-owned-folder.ps1':'d3e37e333fa85fe57b6951292a458f73b08a2f801a2e9b997089599ec044ade4'}
for name,pin in pins.items(): assert sha(A/name)==pin
assert sha(A/'FROZEN.json')=='a339d476fda107967a2c983c25d371975653d0bae5d64c858fd711dc76a207bb'
assert sha(A/'MANIFEST.json')=='b67351f3bd6b96f6a15879838512aa3283aeeebd36c36dca42b424fe3cc6af35'
manifest=json.loads((A/'MANIFEST.json').read_text(encoding='utf-8-sig'))
for row in manifest['files']:
 p=A/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
result=json.loads((R/'result.json').read_text())
assert result['exit_code']==0 and sha(R/'stdout.raw')==result['stdout_sha256'] and sha(R/'stderr.raw')==result['stderr_sha256']
run=json.loads((R/'stdout.raw').read_text())
assert run['passed']==8
diag=json.loads((A/'DIAGNOSTICS.json').read_text(encoding='utf-8-sig'))
events=[{'origin_key':e['origin_key'],'classification':e['classification'],'author_evidence_ref':str(A/'DIAGNOSTICS.json'),'raw':e['result'],'resolution':e['resolution']} for e in diag['new_events']]
put('report.json',{
 'schema':'researchos.independent-source-review.v1',
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,
 'pending_blockers':[], 'source_sha256':pins,
 'freeze_sha256':sha(A/'FROZEN.json'),'freeze_ref':str(A/'FROZEN.json'),
 'manifest_sha256':sha(A/'MANIFEST.json'),'manifest_ref':str(A/'MANIFEST.json'),
 'manifest_files_verified':len(manifest['files']),'no_drift':True,
 'scope':'C-only dedicated owned-dialog Tree metadata diagnostic; admission for a separately approved zero-model Root scope only.',
 'findings':[
  {'ref':'real-electron-flow.mjs:67','result':'Actual boolean diagnostic_only true and numeric task/retry budgets zero are required before launch; diagnostic-only continuation physically ends before workbench, caps, prompt or submission.'},
  {'ref':'choose-owned-folder.ps1:334','result':'FromHandle targets the revalidated owned dialog. All descendant Tree candidates are counted without filtering or deduplication; at most 16 metadata projections. Zero candidates permits at most 32 Win32 child metadata rows without text/items.'},
  {'ref':'choose-owned-folder.ps1:379','result':'Effective entry does not call retained selection/expansion helpers, locate IDOK, set okAttempted or click OK. Fixed diagnostic throw reaches revalidated owned HWND IDCANCEL only.'},
  {'ref':'real-electron-flow.mjs:73','result':'Complete UTF-8 JSON is bounded to 64KiB and parsed before per-scalar sanitization. Wrong owner/HWND, OK/navigation flags, unknown cancel, inconsistent counts and excess fallback rows are refused.'},
  {'ref':'real-electron-flow.mjs:300','result':'Diagnostic capture status explicitly says NOT_PRODUCT_ACCEPTED and model outcome NOT_RUN_DIAGNOSTIC_ONLY. App.close must resolve; external Root Job accounting remains required.'}
 ],
 'independent_checks':{'kind':'C_ONLY_NODE_PURE_EXTRACTED_ACTUAL_SCOPE_AND_REPLY_FUNCTIONS','case_groups':8,'exit_code':0,'ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'raw_tool_chunk':'b161b5','test_sha256':sha(R/'pure.mjs'),'node_sha256':'5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'},
 'static_review':{'own_diff_read_chunk':'6dfaf7','own_locator_chunk':'0c4b02','second_reader':'prompt_flow_review: independent static read of pinned runner/helper, no concrete P1/P2; no runtime execution'},
 'qualification_limits':[
  'No SDK/helper entry/Add-Type/UIA/GUI/native/model, DB or auth file access was executed by this review. Original author 19 Node/14 helper checks are referenced, not recounted as independent.',
  'Actual COM/provider property calls can block. Per-call hard interruption is not established; fresh approved Root deadline and owned outer Job cleanup are required.',
  'No actual Cancel, app-close, process-zero, selector suitability, login or task success is qualified by pure checks. Failure or ownership uncertainty stays blocked/unknown.',
  'Tree metadata may include bounded provider Name/AutomationId within the owned dialog; this is not a global desktop scan or TreeItem/file-content inventory.',
  'Original real flow02 UIA_TREE_NOT_UNIQUE_NO_CLICK is preserved as a pre-model picker blocker; model/login failure is not inferred. Actual transport POST count is NOT_INSTRUMENTED.'
 ],
 'original_run_context_ref':str(R/'PREPARATION.json'),
 'diagnostic_events':events,'counter_reset':False,
 'pending_operations':[],'uncertain_outcomes':[],
 'runtime_admission':'Root may create one new exact-source, zero-task, zero-model, owned-Job diagnostic scope. This source review is not authorization to reuse old run state.'
})
files=[]
for p in sorted(R.iterdir()):
 if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']:
  files.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[v['path'] for v in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({name:sha(R/name) for name in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
