from pathlib import Path
import json,hashlib,shutil,struct
root=Path(__file__).parent; task=root.parent
run=task/'product-v1-layout-visual-中文-run-02'; outer=task/'product-v1-owned-verification-20261104/runs/product-v1-layout-visual-02'
scopepath=task/'product-v1-layout-visual-02-registration/real-flow.scope.json'; postpath=task/'product-v1-build09-post-visual02-root-readback.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(run/'receipts/result.json'); v=read(run/'receipts/workbench-responsive-visual.json'); j=read(outer/'RESULT.json'); consumed=read(outer/'CONSUMED.json'); s=read(scopepath); post=read(postpath)
assert sha(scopepath)==r['scope_sha256'] and consumed['scope_sha256']==j['scope_sha256']
assert j['status']=='CHILD_NONZERO_STOPPED' and j['root_exit_code']==2 and j['job_total_processes']==57
assert j['job_assigned'] and j['resumed'] and j['job_active_zero'] and j['root_signaled'] and j['stop_proved']
assert not j['input_drift'] and not j['errors'] and not j['timed_out'] and j['terminate_job_attempts']==j['terminate_original_root_attempts']==0
for q in j['raw']:assert sha(outer/q['file'])==q['sha256'] and (outer/q['file']).stat().st_size==q['bytes']
assert r['error']['code']=='VISUAL_GEOMETRY_FAILED' and r['visual_findings']==v['findings']
expected=[f'390x844/{theme}/INITIAL_VIEWPORT/initial:VISIBLE_ACTION_COVERED_INITIAL' for theme in ['dark','light']]
assert v['findings']==expected and len(v['scenarios'])==18
assert r['actual_model_calls']==r['actual_dom_submit_attempts']==0 and r['close']['app_close_resolved'] and all(g['passed'] for g in r['guard_history'])
assert len(s['source']['pins'])==48 and s['source']['head']=='5956907bd640d2d4f4abcb583aeb2520883e97c8'
assert s['harness']['runner_sha256']=='c8da238c3815a7223a7b2487393bdcadf41c43ffc06056a888048f9f7cfd590e'
assert s['harness']['folder_helper_sha256']=='c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8'
initial=[x for x in v['scenarios'] if x['phase']=='INITIAL_VIEWPORT']; assert len(initial)==4
summary=[]
for x in initial:
    vp=x['viewport']; w,h=vp['requested_width'],vp['requested_height']; theme=x['requested_theme']
    assert (w,h)==(vp['inner_width'],vp['inner_height']) and x['actual_theme']==theme
    assert x['document']['scroll_y']==x['transcript_scroll']['scroll_top']==0
    p=run/f'screenshots/04-{w}x{h}-{theme}-initial.png'; b=p.read_bytes()
    assert b[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',b[16:24])==(w,h)
    assert not x['composer_overlaps_content'] and x['heading_center_hit'] and not x['horizontal_overflow']
    if w==390:
        assert all(x['actions_center_in_view']) and not any(x['actions_center_hit'])
        assert x['rects']['composer']['y']==924 and not x['composer_center_in_view']
    else:assert all(x['actions_center_hit']) and x['composer_center_hit']
    summary.append({'viewport':[w,h],'theme':theme,'document_scroll_y':0,'transcript_scroll_top':0,'heading_rect':x['rects']['heading'],'composer_rect':x['rects']['composer'],'action_rects':x['rects']['actions'],'heading_hit':x['heading_center_hit'],'action_hits':x['actions_center_hit'],'screenshot_sha256':sha(p)})
assert all(not x['composer_overlaps_content'] and not x['horizontal_overflow'] for x in v['scenarios'])
actions=[x for x in v['scenarios'] if x['action_index'] is not None]
assert len(actions)==12 and all(x['action_focused'] and x['actions_center_hit'][x['action_index']] for x in actions)
assert all(x['composer_center_in_view'] and x['composer_center_hit'] for x in v['scenarios'] if x['phase']=='COMPOSER_SCROLLED')
wrapper=read(run/'receipts/native-folder-automation.json'); helper=json.loads(wrapper['stdout'])
raw=run/'receipts/native-helper-stdout-prefix.bin'; assert json.loads(raw.read_text(encoding='utf-8-sig'))==helper and sha(raw)==r['helper_stdout_progress']['final_sha256']
history=[json.loads(line) for line in (run/'receipts/native-helper-history.ndjson').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
assert history==helper['history'] and len(history)==75
assert helper['invalid_kept_chooser_open'] and helper['invalid_ok_attempted'] and helper['valid_ok_attempted'] and helper['clicked_ok'] and not helper['outcome_uncertain']
assert [x['evidence']['purpose'] for x in history if x['event']=='BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN']==['INVALID_OK','WARNING_DISMISS','VALID_OK']
main=read(run/'receipts/main-current-project-observation.json'); after=read(run/'receipts/main-context-after-open.json'); item=main['listed']['result']['items'][0]
assert item['status']=='ACTIVE' and item['project_id']==main['context']['project_id']==after['context']['project_id']==r['project_id']
assert item['authorized_workspace_ref']==r['authorized_workspace_ref'] and item['display_path']==r['public_display_path'] and item['access']=='READ_WRITE'
assert sha(postpath)=='c442dbc176d3aab33033add6c36585f338e4ff077cfaa54828ca10cf299d54da'
assert post['listed_files']==134 and not post['mismatches'] and not post['unlisted_paths'] and post['manifest_sha256']==s['bundle']['manifest_sha256']
write(root/'independent-evidence-checks.json',{'passed':True,'initial_cases':summary,'scenario_rows':18,'findings':expected,'focused_and_hit_action_probes':12,'source_pin_count':48,'native_history_rows':75,'job_process_count':57,'postbundle_files':134,'replay':False})
for folder in ['receipts','screenshots']:
    (root/'evidence'/folder).mkdir(parents=True,exist_ok=True)
    for p in (run/folder).iterdir():
        if p.is_file():shutil.copyfile(p,root/'evidence'/folder/p.name)
(root/'evidence/outer').mkdir(exist_ok=True)
for name in ['RESULT.json','CONSUMED.json','stdout.raw','stderr.raw']:shutil.copyfile(outer/name,root/'evidence/outer'/name)
shutil.copyfile(scopepath,root/'evidence/real-flow.scope.json');shutil.copyfile(postpath,root/'evidence/postbundle.json')
report={
 'schema':'researchos.independent-real-layout-visual-review/1','decision':'ACTUAL_RESIDUAL_MOBILE_NAVIGATION_OCCLUSION_CONFIRMED_NOT_PRODUCT_ACCEPTED','formal_increment':0,'product_increment':0,'journey_acceptance':{'J13':False,'J01':False},
 'actual_scope_id':j['scope_id'],'actual_scope_consumed':True,'replay_permitted':False,'inner_scope_sha256':r['scope_sha256'],'outer_scope_sha256':j['scope_sha256'],'source_head':s['source']['head'],'source_pin_count':48,'source_sha256':{q['path']:q['sha256'] for q in s['source']['pins']},'controller_source_sha256':s['harness'],'bundle_manifest_sha256':s['bundle']['manifest_sha256'],'core_sha256':s['bundle']['control_sha256'],
 'observations':[
  'Measured findings fall from22 in visual01 to2 in visual02 with byte-identical runner/helper/finding rules; all prior consumed evidence remains unchanged.',
  'All18 scenario rows have no composer/content overlap and no horizontal overflow. Heading center-hit passes in both mobile initial themes. Mobile composer now starts at document y924, below viewport844, and is accessible after scrolling; its initial offscreen center is correctly not an occlusion failure.',
  'The2 remaining findings are mobile dark/light INITIAL_VIEWPORT VISIBLE_ACTION_COVERED_INITIAL. Buttons occupy y769..813 and820..864, with centers791 and842 inside the measured visible clip, but all3 initial action center hits are false. Initial screenshots visibly show fixed bottom navigation obscuring those controls. This is real initial-layout obstruction rather than a partial-visibility offscreen-center false positive.',
  'All12 action scroll/focus probes across4 viewport/theme cases focus and hit the intended action, including6 mobile probes. Thus initial mobile obstruction remains, while post-scroll accessibility is improved; later success does not erase initial failure.',
  'All4 initial PNG dimensions match requested1440x1000 or390x844, actual themes match, and document/transcript scroll offsets equal0. Desktop dark/light measurements and screenshots have no listed findings.',
  'Native75-event history matches raw/helper JSON. Single INVALID_OK, WARNING_DISMISS, VALID_OK posts, same-chooser retention, valid Shell close and Main ACTIVE workspace binding succeed. Project '+r['project_id']+' and workspace '+r['authorized_workspace_ref']+' remain consistent after workbench open; access READ_WRITE. Original choose-workspace reply/private canonical path are not exposed.',
  'Current capture does not record main-area scrollTop/rect or native DOM occluder identity. Screenshot corroborates navigation obstruction, but exact elementFromPoint element identity is not available. A future bounded main scroll region requires new source-bound controller capture/reset for that actual scrolling container; keep finding semantics.'
 ],
 'visual_findings':expected,'manual_screenshots_reviewed':['04-390x844-dark-initial.png','04-390x844-light-initial.png','05-390x844-dark-actions-scroll.png','05-390x844-light-actions-scroll.png','04-1440x1000-dark-initial.png','04-1440x1000-light-initial.png'],
 'terminal':{'status':j['status'],'root_exit_code':2,'job_total_processes':57,'job_active_zero':True,'stop_proved':True,'errors':[],'input_drift':False,'forced_termination_attempts':0,'app_close_resolved':True},
 'postbundle':{'sha256':sha(postpath),'root_reported_verified_files':134,'mismatches':0,'extras':0,'basis':'Independent C receipt exact hash/manifest binding audit of Root post-run summary. This summary has no per-file rows;134-file content verification is attributed to Root. No D traversal or per-file rehash by this reviewer.'},
 'budgets':{'task_submissions':0,'model_calls':0,'automatic_retries':0,'actual_transport_post_count':'NOT_INSTRUMENTED'},
 'pending_blockers':['Fixed bottom navigation still obstructs visible mobile initial shortcut controls; retain actual02 failed status until a separately reviewed product/layout change is validated under a new scope.','No full UI/J13/product acceptance and no model/capability inference.'],
 'diagnostic_events':[{'origin_key':'layout-visual02:mobile-fixed-navigation-covers-initial-actions','classification':'ACTUAL_PRODUCT_RESPONSIVE_LAYOUT_DEFECT_REMAINS','detail':'Two dark/light390x844 initial visible-action-covered findings remain; screenshots show fixed bottom nav over buttons at y769+. Composer y924 no longer overlaps heading, and all mobile scroll/focus action probes now hit. Preserve unchanged finding policy and consumed scope.'},{'origin_key':'layout-visual02-review:postbundle-summary-schema','classification':'REVIEW_RECEIPT_SCHEMA_DIAGNOSTIC','detail':'First C audit writer assumed prior postbundle rows schema and stopped on KeyError rows before report/archive creation. Actual Root receipt contains only manifest hash, listed_files134 and empty mismatch/unlisted arrays. Corrected audit to its actual summary schema, kept exact hash pin and explicitly attributed per-file verification to Root; no actual run replay or input mutation.'}],
 'review_actions':{'gui_runs':0,'app_runs':0,'cli_runs':0,'model_calls':0,'d_writes':0,'old_tests_rerun':0,'only_c_receipt_read_hash_and_archive':True}
}
write(root/'actual-review-report.json',report)
files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','archive-sha256.json'])
write(root/'archive-sha256.json',{f:sha(root/f) for f in files});write(root/'archive-file-list.json',{'root':str(root),'files':files+['archive-sha256.json']})
print(json.dumps({'report':str(root/'actual-review-report.json'),'report_sha256':sha(root/'actual-review-report.json'),'archive_sha256':sha(root/'archive-file-list.json'),'files':len(files)+1,'decision':report['decision']}))
