from pathlib import Path
import json,hashlib,shutil,struct
root=Path(__file__).parent
task=root.parent
run=task/'product-v1-layout-visual-中文-run-01'
outer=task/'product-v1-owned-verification-20261104/runs/product-v1-layout-visual-01'
scopepath=task/'product-v1-layout-visual-01-registration/real-flow.scope.json'
postpath=task/'product-v1-build08-post-visual01-root-readback.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result=read(run/'receipts/result.json'); visual=read(run/'receipts/workbench-responsive-visual.json')
job=read(outer/'RESULT.json'); consumed=read(outer/'CONSUMED.json'); scope=read(scopepath); post=read(postpath)
assert sha(scopepath)==result['scope_sha256']
assert job['scope_sha256']==consumed['scope_sha256']
assert job['status']=='CHILD_NONZERO_STOPPED' and job['root_exit_code']==2
assert job['job_total_processes']==57 and job['job_active_zero'] and job['stop_proved']
assert job['job_assigned'] and job['resumed'] and job['root_signaled']
assert not job['input_drift'] and not job['errors'] and not job['timed_out']
assert job['terminate_job_attempts']==job['terminate_original_root_attempts']==0
for item in job['raw']:
    assert sha(outer/item['file'])==item['sha256'] and (outer/item['file']).stat().st_size==item['bytes']
assert result['error']['code']=='VISUAL_GEOMETRY_FAILED' and result['visual_findings']==visual['findings']
assert result['actual_model_calls']==result['actual_dom_submit_attempts']==0 and result['close']['app_close_resolved']
assert all(g['passed'] for g in result['guard_history'])
assert len(scope['source']['pins'])==47
assert scope['harness']['runner_sha256']=='c8da238c3815a7223a7b2487393bdcadf41c43ffc06056a888048f9f7cfd590e'
assert scope['harness']['folder_helper_sha256']=='c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8'
assert sha(postpath)=='d7ba6e4338f22f6ac9232cdc5f0eef221e96960c10490e4f217bf8dc0f8b0942'
assert post['listed_files']==len(post['rows'])==134 and not post['mismatches'] and not post['unlisted_paths'] and all(r['matches'] for r in post['rows'])
initial=[r for r in visual['scenarios'] if r['phase']=='INITIAL_VIEWPORT']
assert len(initial)==4
initial_summary=[]
for r in initial:
    v=r['viewport']; w=v['requested_width']; h=v['requested_height']; theme=r['requested_theme']
    assert (w,h)==(v['inner_width'],v['inner_height']) and r['actual_theme']==theme
    assert r['document']['scroll_y']==r['transcript_scroll']['scroll_top']==0
    assert not r['horizontal_overflow']
    p=run/f'screenshots/04-{w}x{h}-{theme}-initial.png'
    b=p.read_bytes(); assert b[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',b[16:24])==(w,h)
    if w==1440:
        assert not r['composer_overlaps_content'] and r['heading_center_hit'] and r['composer_center_hit'] and all(r['actions_center_hit'])
    else:
        assert 'heading' in r['composer_overlaps_content'] and r['heading_center_in_view'] and not r['heading_center_hit']
        ch=r['clipped_rects']['heading']; cc=r['clipped_rects']['composer']
        assert max(ch['x'],cc['x'])<min(ch['right'],cc['right']) and max(ch['y'],cc['y'])<min(ch['bottom'],cc['bottom'])
    initial_summary.append({'viewport':[w,h],'theme':theme,'document_scroll_y':0,'transcript_scroll_top':0,'heading_rect':r['rects']['heading'],'composer_rect':r['rects']['composer'],'composer_overlaps':r['composer_overlaps_content'],'heading_center_hit':r['heading_center_hit'],'actions_center_hit':r['actions_center_hit'],'horizontal_overflow':False,'screenshot_sha256':sha(p)})
assert all(not r['horizontal_overflow'] for r in visual['scenarios'])
assert len(visual['findings'])==22 and all(s.startswith('390x844/') for s in visual['findings'])
mobile_actions=[r for r in visual['scenarios'] if r['viewport']['requested_width']==390 and r['action_index'] is not None]
assert len(mobile_actions)==6 and all(r['action_focused'] and not r['actions_center_hit'][r['action_index']] for r in mobile_actions)
wrapper=read(run/'receipts/native-folder-automation.json'); helper=json.loads(wrapper['stdout'])
raw=(run/'receipts/native-helper-stdout-prefix.bin').read_bytes()
assert json.loads(raw.decode('utf-8-sig'))==helper and sha(run/'receipts/native-helper-stdout-prefix.bin')==result['helper_stdout_progress']['final_sha256']
journal=[json.loads(s) for s in (run/'receipts/native-helper-history.ndjson').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
assert journal==helper['history'] and len(journal)==75
assert helper['invalid_kept_chooser_open'] and helper['invalid_ok_attempted'] and helper['valid_ok_attempted'] and helper['clicked_ok'] and not helper['outcome_uncertain']
posts=[r['evidence']['purpose'] for r in journal if r['event']=='BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN']
assert posts==['INVALID_OK','WARNING_DISMISS','VALID_OK']
main=read(run/'receipts/main-current-project-observation.json'); after=read(run/'receipts/main-context-after-open.json')
item=main['listed']['result']['items'][0]
assert main['context']['project_id']==after['context']['project_id']==result['project_id']==item['project_id']
assert item['status']=='ACTIVE' and item['display_path']==result['public_display_path'] and item['authorized_workspace_ref']==result['authorized_workspace_ref']
write(root/'independent-evidence-checks.json',{'checks_passed':True,'initial_cases':initial_summary,'scenario_rows':len(visual['scenarios']),'mobile_action_focus_true_but_center_miss_count':6,'findings':visual['findings'],'native_history_rows':75,'native_post_sequence':posts,'source_pin_count':47,'job_process_count':57,'postbundle_files':134,'replay':False})
for folder in ['receipts','screenshots']:
    (root/'evidence'/folder).mkdir(parents=True,exist_ok=True)
    for p in (run/folder).iterdir():
        if p.is_file(): shutil.copyfile(p,root/'evidence'/folder/p.name)
(root/'evidence/outer').mkdir(exist_ok=True)
for name in ['RESULT.json','CONSUMED.json','stdout.raw','stderr.raw']:shutil.copyfile(outer/name,root/'evidence/outer'/name)
shutil.copyfile(scopepath,root/'evidence/real-flow.scope.json'); shutil.copyfile(postpath,root/'evidence/postbundle.json')
report={
 'schema':'researchos.independent-real-layout-visual-review/1','decision':'ACTUAL_MOBILE_LAYOUT_DEFECT_CONFIRMED_NOT_PRODUCT_ACCEPTED','formal_increment':0,'product_increment':0,'journey_acceptance':{'J13':False,'J01':False},
 'actual_scope_id':job['scope_id'],'actual_scope_consumed':True,'replay_permitted':False,'inner_scope_sha256':result['scope_sha256'],'outer_scope_sha256':job['scope_sha256'],
 'source_head':scope['source']['head'],'source_pin_count':47,'source_sha256':{p['path']:p['sha256'] for p in scope['source']['pins']},'controller_source_sha256':scope['harness'],'bundle_manifest_sha256':scope['bundle']['manifest_sha256'],'core_sha256':scope['bundle']['control_sha256'],
 'functional_observations':['Native invalid-path warning, single dismiss, same chooser retention, valid Shell confirmation and actual Main ACTIVE workspace binding observed. Project remains identical after open-workbench.','Main project '+result['project_id']+'; workspace '+result['authorized_workspace_ref']+'; exact owned Chinese fixture display path; access READ_WRITE. This does not expose private canonical path or original choose-workspace reply.'],
 'visual_observations':{'desktop':'1440x1000 dark/light initial screenshots and measured rows show heading/composer/action center hits and no composer-content overlap; no findings for desktop scenarios.','mobile':'390x844 dark/light initial screenshots visibly show composer occupying the welcome-title region. Heading center is in the visible clip yet misses, and clipped rectangles overlap. This is a real product layout defect, not the prior partial-visibility false positive.','mobile_actions':'All six per-action scroll/focus probes focus their intended action but center-hit remains false. Mobile screenshots also show the fixed bottom navigation covering action area; receipts do not identify the element returned by elementFromPoint, so the precise occluder for every action is not asserted.','initial_integrity':'All four exact-dimension PNGs and rows have document scroll_y=0 and transcript scroll_top=0; initial failures are retained before scroll probes.','overflow':'No horizontal document overflow in any measured row.','loading':'Task/Host loading markers absent; this does not prove model/capability execution readiness.','findings':22,'manual_screenshots_reviewed':['04-390x844-dark-initial.png','04-390x844-light-initial.png','04-1440x1000-dark-initial.png','04-1440x1000-light-initial.png','05-390x844-dark-actions-scroll.png']},
 'terminal':{'status':job['status'],'root_exit_code':2,'job_total_processes':57,'job_active_zero':True,'stop_proved':True,'errors':[],'input_drift':False,'forced_termination_attempts':0,'app_close_resolved':True},
 'postbundle':{'sha256':sha(postpath),'verified_files':134,'mismatches':0,'extras':0,'basis':'Independent C receipt hash/row consistency audit of Root post-run bundle readback; no D readback rerun.'},
 'budgets':{'task_submissions':0,'model_calls':0,'automatic_retries':0,'actual_transport_post_count':'NOT_INSTRUMENTED'},
 'pending_blockers':['Mobile composer/title overlap and shortcut accessibility require product CSS fix and new source/build-pinned scope validation; this consumed run must remain failed.','No full UI/J13/product acceptance or model capability inference from desktop success and Native binding.'],
 'diagnostic_events':[
  {'origin_key':'layout-visual01:mobile-sticky-composer-overlap','classification':'ACTUAL_PRODUCT_RESPONSIVE_LAYOUT_DEFECT','detail':'Both 390x844 themes show initial composer overlap with visible heading, heading center miss, and subsequent shortcut center misses despite focus; screenshots corroborate real obstruction. Four initial offsets are zero. Desktop geometry does not share this defect. Preserve 22 findings as one stable defect event.'},
  {'origin_key':'layout-visual01-review:control-alias-read-miss','classification':'REVIEW_READONLY_PATH_RESOLUTION_DIAGNOSTIC','detail':'Initial read treated parent shorthand CONTROL as a literal workspace folder and found no RESULT file. rg located actual product-v1-owned-verification-20261104/runs/product-v1-layout-visual-01; original terminal receipt was then audited. No execution/replay/write to actual inputs occurred.'}
 ],
 'review_actions':{'gui_runs':0,'app_runs':0,'cli_runs':0,'model_calls':0,'d_writes':0,'old_tests_rerun':0,'only_c_receipt_read_hash_and_archive':True}
}
write(root/'actual-review-report.json',report)
files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files})
write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'report':str(root/'actual-review-report.json'),'report_sha256':sha(root/'actual-review-report.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1,'decision':report['decision']}))
