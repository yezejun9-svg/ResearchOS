import argparse,hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,doc):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
p=argparse.ArgumentParser();p.add_argument('--review-sha',required=True);args=p.parse_args()
review=out/'reviews/development-build-review.json';assert sha(review)==args.review_sha
desktop=json.loads((out/'development-build/controller-02/final.json').read_bytes())
cli=json.loads((out/'cli-development-build/result.json').read_bytes())
assert desktop['status']=='DEVELOPMENT_BUILT_AND_DRYRUN_VALIDATED_NO_NATIVE_START'
assert cli['mode']=='DEVELOPMENT_BUILD_COMMAND_SURFACE_CHECKED_NOT_LIVE_QUALIFIED'
head=desktop['head'];assert cli['source_head']==head
bundle=Path(desktop['bundle']);manifest=bundle/'development-manifest.json'
assert sha(manifest)==desktop['manifest_sha256']
assert sha(Path(cli['binary']['path']))==cli['binary']['sha256']
git=['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks']
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=root).decode().strip()==head
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==585 and len(cp['failure_counters'])==2376
assert not (out/'checkpoint.cp585.before-final-artifacts.json').exists()
(out/'checkpoint.cp585.before-final-artifacts.json').write_bytes(raw)
initial=cp['failure_counters'][:];now=datetime.now(timezone.utc).isoformat()
report=json.loads(review.read_bytes())
diagnostics=report.get('diagnostics',[])
for i,event in enumerate(diagnostics):
    cp['failure_counters'].append({'at':now,'origin_key':f'20261104|development-artifacts-independent-review|{i}','attempts':1,'status':'PRESERVED_READONLY_REVIEW_DIAGNOSTIC','detail':event,'source_ref':{'path':str(review.relative_to(root)),'sha256':args.review_sha},'counter_reset':False})
assert cp['failure_counters'][:2376]==initial
protected=json.loads((out/'integration.json').read_bytes())['protected_preserved']
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
refs={}
for relative in ['integration.json','reviews/prompt-review.json','reviews/prompt-integration-readback.json','reviews/development-build-review.json','reviews/r2-preservation-readback.json','reviews/delivery-contract-design-review.json','builder-stdout-fix/integration.json','builder-stdout-fix/reviews/source-review.json','development-build/controller-01/controller-failed.json','development-build/controller-02/final.json','cli-development-build/result.json']:
    path=out/relative;refs[relative]={'path':str(path.relative_to(root)),'sha256':sha(path),'bytes':path.stat().st_size}
summary={'status':'DEVELOPMENT_ARTIFACTS_BUILT_AND_INDEPENDENTLY_REVIEWED_NOT_LIVE_ACCEPTED','at':now,'main_head':head,'main_tree':cli['source_tree'],'desktop':{'bundle':str(bundle),'manifest_sha256':sha(manifest),'indexed_files':desktop['files'],'indexed_bytes':desktop['bytes'],'native_started':False,'dryrun_state_created':False},'cli':cli['binary'],'artifact_review':refs['reviews/development-build-review.json'],'source_and_review_refs':refs,'old_r2_preserved':True,'failed_r3_and_attempt1_evidence_preserved':True,'build_failure_origin':'compatibility-development-bundle-20261104','successful_build_attempt_index':2,'registry_revision':41,'step_state_unchanged':True,'formal_accepted':0,'formal_required':42,'formal_increment':0,'all_22_parents_accepted':False,'failure_records':len(cp['failure_counters']),'counter_reset':False,'actual_product_business_tasks_this_scope':0,'provider_inference_calls_this_scope':0,'remaining_blockers':['Current Mu v2.4 formal LIVE driver is absent; all five dispatched selectors are BLOCKED/NOT_RUN.','Ordinary coding LIVE acceptance remains blocked by untrusted test-output evidence and nonconvergent shared Task/Goal contracts; ordinary503 unchanged.','Existing W14 writer takeover fixture fails equally on base/candidate; writer guard was not loosened.','A genuine trusted workspace selection, current Mu qualification and purpose-bound authorization are required before a new real task.','Local Ollama assets exist, but declared11435 refused connection and no Ollama process was observed. Consumed/unknown old scopes and counts are not reusable.'],'next':'Resume frozen task selection at W05-99, read this summary plus delivery-contract-design-review. Refine the bounded trusted delivery contract and separate Task/Goal aggregation before any LIVE exception; investigate W14 base failure without lowering writer safety. Resource/native branches require current resources and exact scopes. Preserve failure history and continue other eligible source branches.'}
put(out/'ARTIFACTS_AND_BLOCKERS.json',summary)
resume=dict(summary);resume['checkpoint_revision']=586;resume['summary_ref']=str((out/'ARTIFACTS_AND_BLOCKERS.json').relative_to(root))
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=585;cp['revision']=586;cp['updated_at']=now;cp['updated_by']='codex:/root';cp['head']=head;cp['current_Main_HEAD']=head;cp['current_Main_tree']=cli['source_tree']
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
cp['next_command']=summary['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':summary['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'summary_ref':str((out/'ARTIFACTS_AND_BLOCKERS.json').relative_to(root)),'active_construction_owners':[],'formal_increment':0}
cp['development_artifacts_20261104']={'desktop':summary['desktop'],'cli':summary['cli'],'review_ref':summary['artifact_review'],'build_attempt_index':2,'first_failure_preserved':True,'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp585.before-final-artifacts.md').write_bytes(before)
prefix=('# Current resume CP586\n\nRead '+str((out/'RESUME.json').relative_to(root))+' or ARTIFACTS_AND_BLOCKERS.json. Current Main '+head+'. Reviewed source delivered as Desktop development r4 plus standalone CLI development exe. Build/dry-run/commands evidence only; no Core/GUI/model business task or formal acceptance. r2 preserved; failedr3 and same-origin attempt1 retained; attempt2 succeeded without resetting counts. W14 base failure and business contract design gaps remain. Formal0/42, not all22parents.\n\n').encode()
temp=handoff.with_name(handoff.name+'.cp586.new');temp.write_bytes(prefix+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':586,'main_head':head,'desktop_indexed_files':desktop['files'],'cli_sha256':cli['binary']['sha256'],'failure_records':len(cp['failure_counters']),'formal_increment':0}))
