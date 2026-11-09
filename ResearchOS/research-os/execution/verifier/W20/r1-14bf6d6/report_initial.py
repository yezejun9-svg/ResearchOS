from pathlib import Path
import json,hashlib,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
audit=read(OUT/'source-audit.json');dirty=read(OUT/'dirty-build/result.json');process=read(OUT/'fixture-probe/result.json');summary=read(OUT/'author-evidence/summary.json')
assert process['observed']['cross_data_process_killed']
assert dirty['build_exit_code']==0 and dirty['uncommitted_docs_packaged'] and dirty['untracked_json_packaged']
for label in ['a','b']:assert read(OUT/('fixture-probe/identity-cleanup-'+label+'.stdout.log'))['alive'] is False
for row in audit['source_files']:assert sha(OUT/'source'/row['path'])==row['sha256']
for row in audit['author_evidence_files']:assert sha(OUT/'author-evidence'/Path(row['path']).name)==row['sha256']
assert sha(OUT/'dirty-build/dirty-input-candidate.zip')==dirty['archive_sha256']
manifest=read(OUT/'release-manifest.json');checks=[]
def check(name,ok,actual):checks.append({'id':name,'status':'PASS' if ok else 'FAIL','actual':actual})
check('original-archive-hash',audit['zip_sha256']==summary['archive_sha256'],audit['zip_sha256'])
check('original-manifest-385-files',audit['manifest_files']==385,audit['manifest_files'])
check('packaged-source-matches-frozen-git',audit['source_git_matches']==344,audit['source_git_matches'])
check('fixture-scope-explicit',manifest['acceptance']['normal_live_runtime']=='CLOSED' and manifest['acceptance']['W20']=='NOT_ACCEPTED',manifest['acceptance'])
check('upgrades-unimplemented-explicit',manifest['database']['schema13_to_final_plan']=='NOT_IMPLEMENTED',manifest['database'])
check('two-owned-fixtures-start',all(process['observed']['before_'+x]['status']==200 for x in ['a','b']),process['pids'])
check('stop-refuses-cross-data-pid',not process['observed']['cross_data_process_killed'],process['observed'])
check('owned-fixtures-finally-stopped',all(read(OUT/('fixture-probe/identity-cleanup-'+x+'.stdout.log'))['alive'] is False for x in ['a','b']),process['pids'])
check('dirty-and-untracked-source-refused',dirty['build_exit_code']!=0,dirty)
check('builder-command-cwd-pinned',all(row['cwd'].endswith('source-checkout') for row in read(OUT/'dirty-build/commands.json') if row['label']=='build'),'independent sparse detached checkout at '+audit['source_revision'])
write(OUT/'assertions.json',checks)
findings=[{
 'id':'R1-IDENTITY-001','priority':'P1','source':'ops/release/stop.ps1','lines':[7,14],
 'title':'Stop can terminate a different fixture sharing the same release executable',
 'trigger':'Two independent fresh data directories A and B launch the same release bin/control.exe. A stale or incorrect PID record in A names the B process.',
 'actual':'stop.ps1 -DataDir A succeeds, kills B and leaves A healthy; only the shared executable path is checked.',
 'impact':'A stale/reused PID record can terminate another running fixture or instance from the same release directory. Data directory selection is not bound to the process being stopped.',
 'required_fix':'Record and verify process creation identity plus a launch-instance/data-directory binding before destructive stop. Reject mismatches without stopping either process, preserve data, and retain an explicit recoverable stale-record path.',
 'evidence':'fixture-probe/result.json','fixture_pids':process['pids'],'fixture_ports':process['ports']
},{
 'id':'R1-SOURCE-001','priority':'P1','source':'ops/release/build.py','lines':[171,210],
 'title':'A package labelled with a frozen Git commit includes dirty and untracked inputs',
 'trigger':'Detached HEAD remains 14bf6d6 while a tracked installation README contains an uncommitted synthetic marker and release/independent-untracked.json is untracked.',
 'actual':'The actual offline build exits zero and packages both markers; manifest.source_commit still names the clean frozen revision. source_tree_sha256 describes the selected bytes but is never bound to that Git tree.',
 'impact':'The release artifact cannot be reproduced from its declared source_commit alone. Changes during dependency/build steps can also mix packaged source with compiled input because no stable source snapshot or pre/post check exists.',
 'required_fix':'Build from the exact pinned Git tree or reject changed/untracked build inputs and verify source bytes before and after the build. Ensure the source manifest and binaries originate from that same immutable input.',
 'evidence':'dirty-build/result.json','archive_sha256':dirty['archive_sha256']
}]
review={
 'artifact_kind':'INDEPENDENT_R1_FIXTURE_RELEASE_REVIEW','verifier':'codex:/root/evolution_verifier','source_revision':audit['source_revision'],'author_evidence_revision':audit['evidence_revision'],
 'verdict':'NEEDS_FIX_R1_SOURCE_AND_PROCESS_IDENTITY','scope':'R1 development fixture packaging only; no W20/A15/final release/LIVE acceptance',
 'findings':findings,'validation':{'original_archive_files_verified':385,'original_source_git_blob_matches_LF_normalized':344,'author_18_case_result_hash_verified':True,'author_18_cases_independently_replayed':False,'owned_fixture_processes':2,'both_owned_processes_stopped_after_probe':True,'actual_dirty_input_build_exit':0,'assertions_pass':sum(x['status']=='PASS' for x in checks),'assertions_fail':sum(x['status']=='FAIL' for x in checks)},
 'limits':[
  'Original author two-build equality, wrong-tool rejection and 18-case output are hash-verified source evidence. The full 18-case harness is not redundantly rerun; independent actual ZIP/Git comparison, start/stop and dirty-build negatives target the unresolved boundaries.',
  'Only reviewer-owned fresh credential-free fixture processes, data directories, an isolated sparse Git checkout, and owned output ZIPs were used. No existing product/protected service, production database, holdout payload or provider was accessed.',
  'The builder uses pinned Go/Node/npm, offline dependency resolution, trimpath binaries, sorted ZIP entries and fixed ZIP timestamps. The independent negative harness also invoked the hash-pinned Python interpreter.',
  'The manifest honestly reports 27 license-text gaps, release.reproduce UNBOUND, unqualified runtime/provider identity, final upgrade not implemented, A15 clean Windows not run and W20 not accepted.',
  'Bundled construction source is not a standalone full execution environment: tool locks are external and the project-cycle fixture contract is absent. Existing source_checkout_required restrictions remain; this is not a complete final source/rebuild distribution claim.',
  'Existing policy-denied temporary cleanup paths were untouched. All observed stop actions concerned only the two newly launched known fixture PIDs.',
 ],'W20_accepted':False,'A15_accepted':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False,
}
write(OUT/'review.json',review)
(OUT/'review.md').write_text('# R1 fixture release review\n\nVerdict: **NEEDS_FIX_R1_SOURCE_AND_PROCESS_IDENTITY** for `14bf6d6`.\n\nTwo P1 findings are confirmed by owned local fixtures. A dirty tracked README and an untracked JSON were packaged successfully while the manifest still claimed the frozen Git revision. A wrong PID record in data directory A caused the stop script to kill independently running fixture B from the same release; A stayed healthy. Both test processes were stopped afterwards.\n\nThe original ZIP hash and all 385 manifest entries passed; 344 source entries matched the frozen Git blobs after line-ending normalization. The author 18-case result and two-build equality evidence were hash-verified. These positives do not resolve the two reproduced boundaries.\n\nNo W20, clean-Windows A15, final upgrade, LIVE or BOUNDED_AUTO acceptance is granted. Full details and raw references are in review.json, fixture-probe/ and dirty-build/.\n',encoding='utf-8')
print(json.dumps({'verdict':review['verdict'],'review_sha256':sha(OUT/'review.json'),'pass':review['validation']['assertions_pass'],'fail':review['validation']['assertions_fail']}))
