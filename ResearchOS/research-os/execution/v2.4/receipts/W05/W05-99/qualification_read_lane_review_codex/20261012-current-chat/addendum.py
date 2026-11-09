import datetime,hashlib,json,pathlib,re
OUT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
OLD=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def put(n,v):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
oldlog=OLD/'.local/receipts/approved-combined-first-use-20261012/cb-desktop-suite-app-root.stdout'
newlog=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_read_lane_repair_codex/20261012-current-chat/full-bound-desktop-03.stdout')
logs={'old_cb_four_files':oldlog,'candidate_http_file':newlog}
names={k:[re.sub(r' \([^()]+ms\)$','',x[2:]) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.startswith('✔ ')] for k,p in logs.items()}
refs=[row(p) for p in logs.values()]
refs += [row(OLD/'.local/receipts/approved-combined-first-use-20261012/cb-desktop-suite-app-root.invocation.json')]
unchanged=[]
for n in ['tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/w13-react.test.js']:
    assert sha(OLD/n)==sha(SRC/n)
    unchanged.append({'path':n,'sha256':sha(SRC/n)})
refs += [row(SRC/'internal/domain/client_protocol.go'),row(SRC/'internal/domain/client_protocol_first_use.go'),row(pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/v24-continuation/spec/v2.4/22_CLIENT_INTERFACE_DETAILS.md'))]
put('test-census-01.json',{'source_commit':'cbe5404367e2ea1f00e1ea4552d59d5d0d8eedf9','old':{'total':219,'http':180,'electron':2,'coding':21,'management':11,'w13_react':5},'candidate_203':{'total':203,'http':180,'electron':2,'qualification':21,'scope':'http-wire-boundary.test.mjs only; actual command authority separately requested'},'current_review_executed':{'qualification':21,'management':11,'independent_supplemental':11,'supplemental_pass':9,'supplemental_fail':2},'missing_from_current_replay':['coding-authorization-boundary.test.mjs:21','w13-react.test.js:5'],'four_entry_total_expected_not_executed':240,'registration_names':names,'unchanged_test_files':unchanged,'input_refs':refs})
put('addendum-01.json',{'schema':'researchos.independent-review-addendum/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'REQUEST_CHANGES','finding_priority':'P2','finding_layer':'IPC scope and contract classification; no demonstrated current Core external side-effect bypass','superseded_wording':'report.md production provider.probe wording referred to specified contract behavior, not current implemented Core ability','current_core_limits':['provider.probe/provider.models handleRead default NOT_IMPLEMENTED','workspace.register current Session envelope rejected by first-use all-null scope requirement'],'ipc_only_revision':'Separate presentation whitelist/activity generation; do not expand v2.WRITE_METHODS or existing writer/CAS applicability','provider_models':'refresh=true requires allow_network=true and is active network-request contract, not presentation exemption; refresh=false is cached contract and allow_network alone does not prove network action','test_census':'test-census-01.json','report':'addendum-01.md','parent_acceptance':False,'formal_increment':0,'D_writes':0})
files=[OUT/n for n in ['addendum-01.md','addendum.py','test-census-01.json','addendum-01.json']]
put('manifest-addendum-01.json',{'schema':'researchos.independent-review-manifest-addendum/1','prior_manifest':row(OUT/'manifest.json'),'prior_report':row(OUT/'report.json'),'members':[row(p) for p in files]})
print(json.dumps({'report':sha(OUT/'report.json'),'addendum':sha(OUT/'addendum-01.json'),'manifest':sha(OUT/'manifest.json'),'manifest_addendum':sha(OUT/'manifest-addendum-01.json')},indent=2))
