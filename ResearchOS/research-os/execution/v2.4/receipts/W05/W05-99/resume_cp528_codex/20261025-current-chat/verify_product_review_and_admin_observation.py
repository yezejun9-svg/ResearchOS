import datetime,json
from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import read,ref,R,N
E=N.parent.parent;A=E/'c57_admin_session_observer_codex/20261025-current-chat';V=E/'desktop_main7d_independent_review_codex/20261025-current-chat/owned-host-source-review/static-001'
cp=read(R/'execution/v2.4/checkpoint.json');assert cp['revision']==558 and len(cp['failure_counters'])==2254
assert ref(A/'FINAL-SEAL.json')['sha256']=='2a97f232e94c5dc7f56836577fdae63791de481f9704bd9c169b8fd3cc15c1e6'
admin=read(A/'FINAL-SEAL.json');assert admin['probe_exit']==0 and admin['distinct_sid_process_count']==0 and admin['C57_runs']==0
refs=[]
for x in admin['files']:
 a=ref(A/x['name']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
assert len(refs)==9
assert ref(V/'STATIC-001-MANIFEST.json')['sha256']=='fd626064b37ba85c15fb1fd568ffdb7a0e6aeaf6708d4c43248e28cace6ba687'
m=read(V/'STATIC-001-MANIFEST.json');assert m['verdict']=='CHANGES_REQUIRED_STATIC_ONLY'and m['native_runs']==m['tests_run']==0
for x in m['refs']:
 a=ref(V/x['path']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
assert len(refs)==41
out=N/'Product-r1-review-and-admin-observation-verified.json'
value={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_refs':refs,'Main_preservation':verify(),'product_source_review':'CHANGES_REQUIRED_STATIC_ONLY','finding_ids':m['finding_ids'],'review_manifest_ref':ref(V/'STATIC-001-MANIFEST.json'),'builder_action':'r1 retained; source fixes for r2 underway; no acceptance','admin_observed_at':admin['created_utc'],'admin_seal_ref':ref(A/'FINAL-SEAL.json'),'admin_status':'USER_PREPARING_NOT_VERIFIED; DISTINCT_SID_NOT_OBSERVED_IN_BOUNDED_SNAPSHOT','admin_query_success':24,'admin_unknown':0,'admin_different_sid':0,'admin_same_sid_elevated':16,'admin_recheck_policy':'Do not repeatedly poll unchanged session intent; refresh when user reports readiness or another concrete session-change signal is available','C57_runs':0,'formal_increment':0}
with out.open('x',encoding='utf8')as s:json.dump(value,s,ensure_ascii=False,indent=2);s.write('\n')
print(json.dumps({'result':ref(out),'verified_refs':41,'source_findings_open':8,'distinct_admin_seen':False,'Main_preserved':True,'formal_increment':0},ensure_ascii=False))
