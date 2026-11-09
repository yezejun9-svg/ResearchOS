from pathlib import Path
import json,hashlib,shutil,struct,math
root=Path(__file__).parent; task=root.parent
run=task/'product-v1-layout-visual-中文-run-03'; outer=task/'product-v1-owned-verification-20261104/runs/product-v1-layout-visual-03'
scopepath=task/'product-v1-layout-visual-03-registration/real-flow.scope.json'; postpath=task/'product-v1-build10-post-visual03-root-readback.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(run/'receipts/result.json');v=read(run/'receipts/workbench-responsive-visual.json');j=read(outer/'RESULT.json');consumed=read(outer/'CONSUMED.json');s=read(scopepath);post=read(postpath)
assert sha(scopepath)==r['scope_sha256']=='b1d254e3176c793029384593d462ef8834a66332a938c13fca48cc105fd8db41'
assert consumed['scope_sha256']==j['scope_sha256']=='41381192e4112001a930d9c198d061085ec7fd1b5624cb4844da646cb4290e04'
assert j['status']=='COMPLETED_OWNED_JOB_STOPPED' and j['root_exit_code']==0 and j['job_total_processes']==57
assert j['job_assigned'] and j['resumed'] and j['job_active_zero'] and j['root_signaled'] and j['stop_proved']
assert not j['input_drift'] and not j['errors'] and not j['timed_out'] and j['terminate_job_attempts']==j['terminate_original_root_attempts']==0
for q in j['raw']:assert sha(outer/q['file'])==q['sha256'] and (outer/q['file']).stat().st_size==q['bytes']
assert r.get('error') is None and r['visual_status']==v['status']=='PASS_MEASURED_VISUAL_GEOMETRY' and r['visual_findings']==v['findings']==[]
assert len(v['scenarios'])==18 and r['actual_model_calls']==r['actual_dom_submit_attempts']==0 and r['close']['app_close_resolved'] and all(g['passed'] for g in r['guard_history'])
assert len(s['source']['pins'])==48 and s['source']['head']=='11e0395f30a9c9249c2644a6596276a364d2c294'
candidate=task/'product-v1-native-layout-visual09-review-20261105/candidate09'
assert sha(candidate/'real-electron-flow.mjs')==s['harness']['runner_sha256']=='f3a540bde9a7b332ed7852834bd073fad68543a6b5e32190cf96d19bce24d047'
assert sha(candidate/'choose-owned-folder.ps1')==s['harness']['folder_helper_sha256']=='c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8'
def clip(a,b,x=True,y=True):
    if a is None:return None
    left=max(a['x'],b['x']) if x else a['x'];right=min(a['right'],b['right']) if x else a['right']
    top=max(a['y'],b['y']) if y else a['y'];bottom=min(a['bottom'],b['bottom']) if y else a['bottom']
    return {'x':left,'y':top,'right':right,'bottom':bottom,'width':right-left,'height':bottom-top} if right>left and bottom>top else None
def same(a,b):
    if a is None or b is None:return a is None and b is None
    return all(math.isclose(a[k],b[k],abs_tol=1e-6) for k in ['x','y','right','bottom','width','height'])
def center_in(raw,c):return bool(c and c['x']<=(raw['x']+raw['right'])/2<c['right'] and c['y']<=(raw['y']+raw['bottom'])/2<c['bottom'])
clip_count=0;chain_step_count=0
initial=[]
for x in v['scenarios']:
    vp=x['viewport'];w,h=vp['requested_width'],vp['requested_height'];theme=x['requested_theme']
    assert (w,h)==(vp['inner_width'],vp['inner_height']) and x['actual_theme']==theme
    assert not x['composer_overlaps_content'] and not x['horizontal_overflow']
    entries=[('heading',x['rects']['heading'],x['clipchain']['heading'],x['clipped_rects']['heading'],x['heading_center_in_view']),('composer',x['rects']['composer'],x['clipchain']['composer'],x['clipped_rects']['composer'],x['composer_center_in_view'])]
    entries += [(f'action_{i}',raw,x['clipchain']['actions'][i],x['clipped_rects']['actions'][i],x['actions_center_in_view'][i]) for i,raw in enumerate(x['rects']['actions'])]
    for name,raw,chain,final,inview in entries:
        current=clip(raw,{'x':0,'y':0,'right':w,'bottom':h});assert any(c['class_name']=='main-area' for c in chain)
        for c in chain:
            assert c['x_applied']==(c['overflow_x'] in ['auto','scroll','hidden','clip','overlay']) and c['y_applied']==(c['overflow_y'] in ['auto','scroll','hidden','clip','overlay'])
            current=clip(current,c['client_bounds'],c['x_applied'],c['y_applied']);assert same(current,c['remaining_rect']);chain_step_count+=1
        assert same(current,final) and center_in(raw,current)==inview;clip_count+=1
    if x['phase']=='INITIAL_VIEWPORT':
        assert x['document']['scroll_y']==x['transcript_scroll']['scroll_top']==x['main_area_scroll']['scroll_top']==0
        p=run/f'screenshots/04-{w}x{h}-{theme}-initial.png';b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',b[16:24])==(w,h)
        assert x['heading_center_hit']
        if w==390:
            assert x['main_area_scroll']['overflow_y']=='auto' and x['main_area_scroll']['rect']['y']==56 and x['main_area_scroll']['rect']['bottom']==780
            assert not any(x['actions_center_in_view']) and not x['composer_center_in_view']
            assert [q['height'] if q else None for q in x['clipped_rects']['actions']]==[11,11,None]
        else:assert all(x['actions_center_hit']) and x['composer_center_hit']
        initial.append({'viewport':[w,h],'theme':theme,'document_scroll_y':0,'transcript_scroll_top':0,'main_scroll_top':0,'main_area_scroll':x['main_area_scroll'],'clipped_actions':x['clipped_rects']['actions'],'initial_actions_center_in_view':x['actions_center_in_view'],'screenshot_sha256':sha(p)})
    if w==390 and x['phase']!='INITIAL_VIEWPORT':assert x['main_area_scroll']['scroll_top']>0 and x['document']['scroll_y']==0
assert len(initial)==4 and clip_count==90
actions=[x for x in v['scenarios'] if x['action_index'] is not None]
assert len(actions)==12 and all(x['action_focused'] and x['actions_center_in_view'][x['action_index']] and x['actions_center_hit'][x['action_index']] for x in actions)
assert all(x['composer_center_in_view'] and x['composer_center_hit'] for x in v['scenarios'] if x['phase']=='COMPOSER_SCROLLED')
wrapper=read(run/'receipts/native-folder-automation.json');helper=json.loads(wrapper['stdout']);raw=run/'receipts/native-helper-stdout-prefix.bin'
assert json.loads(raw.read_text(encoding='utf-8-sig'))==helper and sha(raw)==r['helper_stdout_progress']['final_sha256']
history=[json.loads(line) for line in (run/'receipts/native-helper-history.ndjson').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
assert history==helper['history'] and len(history)==75
assert helper['invalid_kept_chooser_open'] and helper['invalid_ok_attempted'] and helper['valid_ok_attempted'] and helper['clicked_ok'] and not helper['outcome_uncertain']
assert [x['evidence']['purpose'] for x in history if x['event']=='BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN']==['INVALID_OK','WARNING_DISMISS','VALID_OK']
main=read(run/'receipts/main-current-project-observation.json');after=read(run/'receipts/main-context-after-open.json');item=main['listed']['result']['items'][0]
assert item['status']=='ACTIVE' and item['project_id']==main['context']['project_id']==after['context']['project_id']==r['project_id']
assert item['authorized_workspace_ref']==r['authorized_workspace_ref'] and item['display_path']==r['public_display_path'] and item['access']=='READ_WRITE'
assert sha(postpath)=='0c58a53e3944bd0414ab58bbad2768797e8d586645d3861050988bbcceec4f59'
assert post['listed_files']==len(post['rows'])==134 and not post['mismatches'] and not post['unlisted_paths'] and post['manifest_sha256']==s['bundle']['manifest_sha256']
assert all(q['expected_sha256']==q['actual_sha256'] for q in post['rows'])
write(root/'independent-evidence-checks.json',{'passed':True,'initial_cases':initial,'scenario_rows':18,'findings':[],'effective_clips_recomputed':clip_count,'ancestor_steps_recomputed':chain_step_count,'focused_visible_hit_action_probes':12,'source_pin_count':48,'native_history_rows':75,'job_process_count':57,'postbundle_rows':134,'replay':False})
for folder in ['receipts','screenshots']:
    (root/'evidence'/folder).mkdir(parents=True,exist_ok=True)
    for p in (run/folder).iterdir():
        if p.is_file():shutil.copyfile(p,root/'evidence'/folder/p.name)
(root/'evidence/outer').mkdir(exist_ok=True)
for name in ['RESULT.json','CONSUMED.json','stdout.raw','stderr.raw']:shutil.copyfile(outer/name,root/'evidence/outer'/name)
shutil.copyfile(scopepath,root/'evidence/real-flow.scope.json');shutil.copyfile(postpath,root/'evidence/postbundle.json')
shutil.copyfile(candidate/'real-electron-flow.mjs',root/'evidence/reviewed-runner.mjs')
report={
 'schema':'researchos.independent-real-layout-visual-review/1','decision':'REAL_NATIVE_BINDING_AND_RESPONSIVE_GEOMETRY_FUNCTIONALLY_OBSERVED_NOT_FULL_PRODUCT_ACCEPTED','formal_increment':0,'product_increment':0,'journey_acceptance':{'J13':False,'J01':False},'source_head':s['source']['head'],
 'actual_scope_id':j['scope_id'],'actual_scope_consumed':True,'replay_permitted':False,'inner_scope_sha256':r['scope_sha256'],'outer_scope_sha256':j['scope_sha256'],'source_pin_count':48,'source_sha256':{q['path']:q['sha256'] for q in s['source']['pins']},'controller_source_sha256':s['harness'],'bundle_manifest_sha256':s['bundle']['manifest_sha256'],'core_sha256':s['bundle']['control_sha256'],
 'observed_result':{'status':r['status'],'visual_status':v['status'],'findings':[],'scenario_rows':18,'initial_viewport_theme_cases':4,'focused_visible_hit_action_probes':12},
 'observations':[
  'Four exact1440x1000/390x844 dark/light initial PNGs and actual viewport/theme rows agree; document, transcript and main scrollTop all0 before any scrolling.',
  'Mobile main-area actual overflowY:auto has rect y56..780, client right375 excluding its scrollbar. App-grid also clips to y56..780. The fixed navigation is below that scroll region. Actual per-axis computed clipchain accounts for this boundary;90 element clips and every ancestor remaining-rect step were independently recomputed from the recorded raw geometry with matching results.',
  'Mobile initial action rectangles start y769 and820; first two have only11px visible before main bottom780 and third is fully clipped. Their centers are outside the actual main clip. They are not all initially visible or usable; scrolling is required. Initial heading remains visible/hit and composer below the fold is not misreported as covered.',
  'After scrolling the mobile main-area by about601.33px, document scroll stays0; screenshots in both themes show all three actions and composer inside the main region above bottom navigation. Every12 action probe across4 cases has center-in-clip, actual original-center hit and focus true. Both mobile composer-scrolled rows have visible center and hit true.',
  'No measured composer/content overlap or horizontal document overflow in any18 rows. Desktop dark/light initial and after-scroll evidence likewise satisfies measured gates. PASS is limited to these viewport/theme cases and measured interactions.',
  'Pinned runnerf3a540... is the independently reviewed real DOM/ancestor-computed-style reader with unchanged original-center hit and action gates; source has no DOM/CSS substitution, nav64-based finding suppression, task submission or model calls. Runtime source guards all pass and Root reports no input drift. Geometry corrections reflect the real new scroll container, not manufactured UI.',
  'Native75-event raw/helper/journal evidence agrees; single invalidOK/warning-dismiss/validOK sequence, chooser retention and final Shell close precede Main ACTIVE exact Chinese fixture workspace binding. Project '+r['project_id']+' and workspace '+r['authorized_workspace_ref']+' persist after workbench open, access READ_WRITE. This is current-state bridge observation, not private canonical-path exposure or original chooser reply.',
  'Prior visual01 and visual02 failures stay preserved and consumed. This run adds functional repair evidence without rewriting old failures or granting product journeys.'
 ],
 'manual_screenshots_reviewed':['04-1440x1000-dark-initial.png','04-1440x1000-light-initial.png','04-390x844-dark-initial.png','04-390x844-light-initial.png','04c-390x844-dark-composer-scroll.png','04c-390x844-light-composer-scroll.png','05-390x844-dark-actions-scroll.png','05-390x844-light-actions-scroll.png'],
 'terminal':{'status':j['status'],'root_exit_code':0,'job_total_processes':57,'job_active_zero':True,'stop_proved':True,'errors':[],'input_drift':False,'forced_termination_attempts':0,'app_close_resolved':True,'outer_result_file_sha256':sha(outer/'RESULT.json')},
 'postbundle':{'sha256':sha(postpath),'root_verified_files':134,'expected_actual_hash_rows_matching':134,'mismatches':0,'extras':0,'basis':'Independently verified exact C receipt hash and all134 expected/actual hash pairs against matching manifest binding. Physical bundle rehash was performed by Root; not rerun here.'},
 'budgets':{'task_submissions':0,'model_calls':0,'automatic_retries':0,'actual_transport_post_count':'NOT_INSTRUMENTED'},
 'diagnostic_events':[],'pending_blockers':[],
 'limitations':['Functional geometry/Native binding observation only; formal/product/J01/J13 increments remain0.','Banner states were neither manufactured nor exercised/verified in this run. No task/model/capability-enforcement acceptance is inferred from login/status text or loading-marker absence.','Center-hit/rectangle observations and selected screenshots are not exhaustive interaction/accessibility or full-product acceptance.','Scope is consumed; no replay performed or authorized by this report.'],
 'review_actions':{'gui_runs':0,'app_runs':0,'cli_runs':0,'model_calls':0,'d_writes':0,'old_tests_rerun':0,'only_c_receipt_read_hash_geometry_recompute_and_archive':True}
}
write(root/'actual-review-report.json',report)
files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files});write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'report':str(root/'actual-review-report.json'),'report_sha256':sha(root/'actual-review-report.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1,'decision':report['decision'],'clip_steps':chain_step_count}))
