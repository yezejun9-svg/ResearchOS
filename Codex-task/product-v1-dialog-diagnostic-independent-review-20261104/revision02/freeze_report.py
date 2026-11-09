from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;P=R.parent;A=P.parent/'product-v1-real-electron-tree-diagnostic-revision-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,v):
 p=R/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'FROZEN.json')=='5fbbe985e1602a75426826588692bd122f315af489bf52192e2b0265ea7e9b8e'
assert sha(A/'MANIFEST.json')=='c324aaa26f841c9d698e1e7f87180fb5114d3077a1d9709ee2342c1d34c0e52f'
f=json.loads((A/'FROZEN.json').read_text());m=json.loads((A/'MANIFEST.json').read_text())
for row in m['files']:
 p=A/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
for name,pin in f['source_sha256'].items():assert sha(A/name)==pin
r=json.loads((R/'result.json').read_text());assert r['exit_code']==0
assert sha(R/'stdout.raw')==r['stdout_sha256'] and sha(R/'stderr.raw')==r['stderr_sha256']
tests=json.loads((R/'stdout.raw').read_text());assert tests['case_groups']==3 and tests['reverse_byte_exact']
prior=P/'report.json';assert sha(prior)=='580a77677909e18711646d311b8c01a31ced64a75621e492dd075987a5e4586f'
diag=json.loads((A/'DIAGNOSTICS.json').read_text())
put('report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':f['source_sha256'],'manifest_ref':str(A/'MANIFEST.json'),'manifest_sha256':sha(A/'MANIFEST.json'),'freeze_ref':str(A/'FROZEN.json'),'freeze_sha256':sha(A/'FROZEN.json'),'no_drift':True,'manifest_files_verified':len(m['files']),
 'scope':'C-only dedicated diagnostic revision02 environment and Electron cwd delta. No production Core cwd change.',
 'findings':[
  {'ref':'real-electron-flow.mjs:41','result':'Actual makeEnvironment now derives uppercase SystemDrive from the Windows drive-rooted explicit SystemRoot. It rejects UNC/device/root-relative/drive-relative or unresolved root without a drive. Normal account profile and explicit environment allowlist remain unchanged; ambient SystemDrive is not read.'},
  {'ref':'real-electron-flow.mjs:234','result':'Actual Electron launch cwd is the owned fresh run_root, after mkdir succeeds. Executable, argument paths and environment remain otherwise unchanged. launch-input records the chosen cwd. Core keeps its separately explicit resource REPO cwd.'},
  {'ref':'independent pure reverse proof','result':'Reverse only the two added drive lines, one returned field, launch-input cwd field and actual launch cwd restores diag01 runner byte-for-byte including CRLF. Helper hash is unchanged. Zero-model budget, no-OK diagnostic control flow, ownership/UTC/cancel/close guards are unchanged.'}
 ],
 'independent_checks':{'case_groups':3,'exit_code':0,'ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'raw_tool_chunk':'8c5c47','method':'Extract actual makeEnvironment and actual launch fragment into VM with Windows path API and fake launch only. Verify environment equality except one derived drive, invalid roots and actual cwd/options; no SDK import or app launch.','test_sha256':sha(R/'pure.mjs')},
 'reused_review':{'ref':str(prior),'sha256':sha(prior),'why':'Exact reverse proof and unchanged helper preserve previously reviewed no-OK/zero-model/owned-cancel behavior. Old 8 independent cases and author33 checks are not rerun or recounted.'},
 'qualification_limits':[
  'No SDK, GUI, Core, UIA, Native, model, DB/auth/cache DB access or poisoned bundle modification occurred.',
  'Explicit SystemRoot/profile remain trusted Root-scope platform inputs; this change does not authenticate the filesystem path or implement Core cwd isolation.',
  'Cache artifact causality remains inference. Fresh validated build plus actual Root-owned diagnostic scope must prove runtime environment and stop behavior.',
  'Existing UIA provider blocking and READY-listener limitations retain original fail-closed/outer Job requirements. No actual Cancel/app.close/full-Job result is certified here.',
  'Metadata capture is not product acceptance, login qualification, model outcome or completed user task. Actual transport POST count remains NOT_INSTRUMENTED.'
 ],
 'diagnostic_events':[{'origin_key':e['origin_key'],'classification':e['classification'],'ref':str(A/'DIAGNOSTICS.json'),'raw':e['result'],'resolution':e['resolution']} for e in diag['events']],
 'carryforward_only':{'origin_key':'sealed-bundle-native-shell-cache-missing-systemdrive','count_again':False,'old_diag03':'BUNDLE_UNLISTED_PATH before App/model; prior evidence and old bundle left untouched'},
 'runtime_prerequisites':['Fresh Root scope with this exact runner/helper and independently validated fresh build containing the approved Core environment fix.','Root original outer Job deadline and process-zero accounting; no replay of consumed scopes or old state.'],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']]
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[p['path'] for p in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({name:sha(R/name) for name in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
