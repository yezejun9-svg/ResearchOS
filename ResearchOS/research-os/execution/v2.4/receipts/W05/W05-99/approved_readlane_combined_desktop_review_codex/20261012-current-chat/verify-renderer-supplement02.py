import pathlib,json,hashlib,re,datetime
O=pathlib.Path(__file__).resolve().parent;F=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));mf=F/'renderer-supplement-manifest.json';assert sha(mf)=='171ad2ec63631a53512b8a8cf893e7203d8f0245b986956de3de003101b349af';m=read(mf);refs={}
def visit(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:
   p=pathlib.Path(v['path']);assert p.is_file() and sha(p)==v['sha256'];assert p.stat().st_size==v['bytes'];refs[str(p)]=v
  for x in v.values():visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
visit(m);report=read(pathlib.Path(m['supplement_report']['path']));visit(report)
census=read(pathlib.Path(m['raw_census']['path']));root=pathlib.Path(census['root']);assert census['member_count']==len(census['members'])==137
for r in census['members']:p=root/r['path'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='census.json'};assert actual=={r['path'] for r in census['members']}
cases=[]
for item in report['cases']:
 kind=item['kind'];case=read(pathlib.Path(item['case_report']['path']));visit(case);node=read(pathlib.Path(case['node_invocation']['path']));native=read(pathlib.Path(case['native_invocation']['path']));observed=read(pathlib.Path(case['native_process_observations']['path']));visit(node)
 assert node['exit']==0 and native['exit']==0 and type(native['exit']) is int and native['exited'] and native['stdoutClosed'] and native['stderrClosed']
 assert node['argv'][node['argv'].index('--test-name-pattern')+1]=='^desktop-renderer/'+kind+'-roundtrip$',node
 assert node['selected_environment']['RESEARCHOS_DESKTOP_WIRE_ROOT']==str(pathlib.Path(m['package_root'])/'apps/desktop')
 assert node['selected_environment']['RESEARCHOS_DESKTOP_CASE_RECEIPT']==str(root/kind)
 assert native['actualargv'][-1]=='--renderer-case='+kind and case['native_creation']['argv']==native['actualargv']
 assert native['pid']==case['native_creation']['pid'] and native['pid'] in [23208,64088]
 assert case['node_counts']=={'tests':1,'pass':1,'fail':0,'skipped':0,'cancelled':0}
 for channel in ['stdout','stderr']:
  p=pathlib.Path(node[channel]['path']);assert sha(p)==node[channel]['sha256']
 text=pathlib.Path(node['stdout']['path']).read_text(encoding='utf-8');assert re.search(r'(?m)^.*tests 1\s*$',text) and re.search(r'(?m)^.*pass 1\s*$',text)
 assert ('DESKTOP_RENDERER_PASS '+kind) in pathlib.Path(case['native_stdout']['path']).read_text()
 cases.append({'kind':kind,'node_exit':node['exit'],'native_pid':native['pid'],'native_numeric_exit':native['exit'],'creation':case['native_creation'],'native_stdout_ref':case['native_stdout'],'native_stderr_ref':case['native_stderr'],'node_invocation_ref':case['node_invocation'],'native_invocation_ref':case['native_invocation'],'native_process_observation':observed,'wire_root':node['selected_environment']['RESEARCHOS_DESKTOP_WIRE_ROOT']})
# This pass preserves every original four-entry raw file as captured before supplementation.
old=read(O/'bound-tests-raw-census.json');assert all(sha(pathlib.Path(x['path']))==x['sha256'] for x in old['files'])
value={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'RENDERER_RAW_GAP_CLOSED_FOR_NEW_ISOLATED_RUNS','manifest':{'path':str(mf),'sha256':sha(mf)},'refs':list(refs.values()),'raw_members_verified':137,'distinct_cases':cases,'original_four_entry_raw_files_unchanged':old['count'],'original_react_raw_recovered':False,'unique_desktop_tests_remain':253,'full_suite_repeated':False,'ordinary_GUI_or_Core_or_verifier_evidence':False}
(O/'renderer-supplement-independent.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'cases':[(x['kind'],x['native_pid'],x['native_numeric_exit']) for x in cases],'raw137verified':True,'original_raw_unchanged':old['count']}))
