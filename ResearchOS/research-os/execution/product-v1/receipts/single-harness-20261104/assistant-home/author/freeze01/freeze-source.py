from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re

BASE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104')
REPO=Path('D:/作品集/ResearchOS/research-os')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
scopepath=REPO/'execution/product-v1/receipts/single-harness-20261104/assistant-home/scope.json'
scope=json.loads(scopepath.read_text(encoding='utf-8'))
directory=BASE/'final';directory.mkdir(exist_ok=False)
paths=scope['production_paths']+scope['test_paths']
pins={}
for rel in paths:
    target=directory/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/rel).read_bytes())
    pins[rel]=sha(target)
    assert pins[rel]==sha(ROOT/rel)
    assert pins[rel]!=scope['baseline_sha256'][rel]
scopecheck=json.loads((BASE/'checks-04-final/scope-check.json').read_text())
assert scopecheck['paths_exact'] and scopecheck['base_matches']
results=json.loads((BASE/'checks-04-final/results.json').read_text())
assert all(row['exit_code']==0 for row in results)
build=json.loads((BASE/'vite-03-final/result.json').read_text())
assert build['exit_code']==0 and build['all_source_unchanged']
assert json.loads((BASE/'checks-02-public-spec/result.json').read_text())['exit_code']==0
tap=(BASE/'checks-04-final/startup-and-compatibility.stdout.raw').read_text(encoding='utf-8')
assert '# tests 58\n' in tap and '# pass 58\n' in tap and '# fail 0\n' in tap
inputs=json.loads((BASE/'vite-03-final/command.json').read_text())['inputs']
for row in inputs:
    if row['path'] in pins: assert row['sha256']==pins[row['path']]
unchanged={rel:sha(ROOT/rel) for rel in ['apps/desktop/main/lib/ipc.js','apps/desktop/preload/preload.js']}
assert unchanged=={'apps/desktop/main/lib/ipc.js':'0ed4863417d428f691de8449593e3d22e5d10006c24cd0cc7a8c125a0212a581','apps/desktop/preload/preload.js':'b3225c6657424d4ef93842795834e6db068dac2c5cbe98c69788a88f6d909b42'}
manifest={'schema':'researchos.assistant-home.source-manifest/1','scope_path':str(scopepath),'scope_sha256':sha(scopepath),'base_head':scope['base_head'],'worktree':str(ROOT),'source_sha256':pins,'unchanged_boundary_sha256':unchanged,'all_final_snapshots_match_live':True,'construction_frozen':True,'source_modification_permitted':False,'formal_increment':0}
write(directory/'source-manifest.json',manifest)
diagnostics=[
 {'origin':'a3f778','classification':'PREPARATION_HARNESS_POWERSHELL_PREPARSE','exit_code':1,'count_again':False,'detail':'Read-only preparation foreach pipe syntax error; none of that invocation executed. Corrected terminal read 8e875b; recorded in immutable preparation/plan.json.'},
 {'origin':'pre-compaction-read-output-truncation','classification':'READONLY_TOOL_OUTPUT_TRUNCATED','count_again':False,'detail':'Preparation broad read output not used as evidence. Narrow subsequent reads terminal; no product execution.'},
 {'origin':'3bea0a/ab61b2:mu-first-use','classification':'SPARSE_FIXTURE_STATIC_DEPENDENCY_MISSING','exit_code':1,'product_assertions_reached':False,'raw':'checks-01/mu-first-use.stdout.raw','detail':'Existing selected test could not require omitted public OpenAPI JSON. Exact one static dependency resolved from Main in C, no D dependency/source change; checks-02-public-spec actual exit0. Root subsequently materialized tracked public dependencies; no redundant rerun.'},
 {'origin':'8c83b7','classification':'AUTHOR_INSTALLER_LINE_ENDING_CHURN_FOUND_BY_READBACK','detail':'First source writer normalized the baseline workbench mixed line endings. source-write-02 restored exact unchanged baseline bytes; no runtime behavior change.'},
 {'origin':'a56787/8ba1a1:git-diff-check','classification':'AUTHOR_SOURCE_FORMATTING_GIT_WHITESPACE_FAILURE','exit_code':2,'raw':'checks-03-final/git-diff-check.stdout.raw','detail':'Nine changed workbench CRLF lines flagged as trailing whitespace. source-write-03 changes only those terminators; normalized logic byte-equal, then checks-04-final all0 and final Vite0.'},
 {'origin':'vite-01/vite-02-final/vite-03-final:outDir','classification':'BENIGN_BUILD_CONFIGURATION_WARNING','detail':'Vite C outDir lies outside copied project root; each output directory is new and not auto-emptied. All build exit0; raw stderr retained. No deletion or dependency install.'}
]
write(directory/'diagnostics.json',{'schema':'researchos.assistant-home.diagnostics/1','events':diagnostics,'diagnostic_origin_count':len(diagnostics),'product_failures_observed':0,'all_failed_attempts_retained':True})
summary={'schema':'researchos.assistant-home.author-summary/1','status':'IMPLEMENTED_SOURCE_FROZEN_FOR_INDEPENDENT_QA','author_acceptance':False,'decision':'NOT_SELF_APPROVED','source_sha256':pins,
 'changes':['Compact assistant landing on the real default route; actual accessible projects and bounded actual opened IDs only.','Fresh dark default retains saved light/dark and handles blocked storage.','Existing true native directory registration opens workbench without a provider/model prerequisite; optional naming is secondary.','Header health strictly checks the existing flat statusHealth healthz shape and has bounded late-result/disposal handling. Project event/write barriers remain separate.','Main private AUTHORITY_READ smoke probe no longer displaces renderer presentation reads; private Symbol is not renderer-selectable.','Existing Codex/Mu workbench, IME/draft/UNKNOWN/permission behavior retained.'],
 'tests':{'final_narrow_ui':{'exit_code':0,'passed':58,'top_level':35,'subtests':23,'failed':0,'skipped':0,'raw':'checks-04-final/startup-and-compatibility.stdout.raw'},'mu_first_use':{'exit_code':0,'passed':1,'failed':0,'skipped':0,'raw':'checks-02-public-spec/stdout.raw','static_dependency_only_resolution':True},'combined_unique_cases':59,'syntax':{'main':0,'startup':0,'new_test':0},'git':{'diff_check':0,'status':0,'head':0,'exact8':True,'base_matches':True},'vite':{'exit_code':0,'raw_stdout':'vite-03-final/stdout.raw','raw_stderr':'vite-03-final/stderr.raw','all_source_unchanged':True,'modules_transformed':39,'output_files':3,'cache':'D:/作品集/ResearchOS/research-os/.local/product-v1-build-inputs-20261104/web-node_modules-02/node_modules'}},
 'limits':['Pure function/IPC/UI handler fixtures and actual production source build are not real GUI, Native or model proof.','No real Electron screenshot produced in this source scope; Root must separately assess actual visual presentation.','Host health reports service reachability only, not Harness readiness, model qualification or write authority.','Recent IDs are display preferences intersected with current accessible projects, not a second project/task authority.'],
 'real_execution':{'gui':0,'cli_entry':0,'native':0,'model':0,'user_auth_file_access':0,'user_db_access':0,'old_probe_replay':0},'pending_author_sessions':0,'pending_independent_review':True,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'summary.json',summary)
frozen={'schema':'researchos.assistant-home.freeze/1','at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'source_manifest_sha256':sha(directory/'source-manifest.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'all8_source_pins_match_live':True,'pending_author_sessions':0,'author_self_acceptance':False,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'FROZEN.json',frozen)
# Retain original attempts, diagnostics, exact8 final snapshots and build receipts;
# no node_modules, generated dist, or repeated whole-web source copies in archive.
selected=[]
for p in BASE.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(BASE)
    if rel.as_posix() in ['EVIDENCE_MANIFEST.json','archive-file-list.json']:continue
    if rel.parts[0].startswith('vite-') and len(rel.parts)>1 and rel.parts[1] in ['source','dist']:continue
    selected.append(p)
selected.sort(key=lambda p:p.relative_to(BASE).as_posix())
evidence={'schema':'researchos.assistant-home.evidence/1','source_sha256':pins,'files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in selected],'excluded':['vite-*/source duplicate build-input copies','vite-*/dist generated artifacts','node_modules/cache (none owned under this evidence root)']}
write(BASE/'EVIDENCE_MANIFEST.json',evidence)
archive={'schema':'researchos.assistant-home.archive-selection/1','root':str(BASE),'files':[p.relative_to(BASE).as_posix() for p in selected]+['EVIDENCE_MANIFEST.json','archive-file-list.json'],'exclude_tree':['vite-*/source','vite-*/dist'],'evidence_manifest_sha256':sha(BASE/'EVIDENCE_MANIFEST.json')}
write(BASE/'archive-file-list.json',archive)
for row in evidence['files']:assert sha(BASE/row['path'])==row['sha256']
for rel,digest in pins.items():assert sha(ROOT/rel)==digest
print(json.dumps({'status':'FROZEN','source_manifest_sha256':sha(directory/'source-manifest.json'),'freeze_sha256':sha(directory/'FROZEN.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'evidence_sha256':sha(BASE/'EVIDENCE_MANIFEST.json'),'archive_list_sha256':sha(BASE/'archive-file-list.json'),'evidence_files':len(selected),'all8_live_pins_match':True,'source_sha256':pins},ensure_ascii=True),flush=True)
