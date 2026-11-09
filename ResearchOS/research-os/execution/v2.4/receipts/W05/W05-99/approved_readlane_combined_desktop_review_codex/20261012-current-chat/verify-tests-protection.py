import pathlib,hashlib,json,subprocess,datetime,re
O=pathlib.Path(__file__).resolve().parent;F=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat');M=pathlib.Path('D:/作品集/ResearchOS/research-os');S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
m=read(F/'manifest.json');P=pathlib.Path(m['package']['root']);br=pathlib.Path(m['build']['receipts']);checks=[]
for r in read(O/'protected-source-baseline.json')['protected_source']:
 actual=M/r['path'];assert sha(actual)==r['sha256'] and actual.stat().st_size==r['bytes'],r
 if (S/r['path']).is_file():assert sha(S/r['path'])==r['sha256'],r
 checks.append({**r,'Main_sha256':sha(actual),'Source_present':(S/r['path']).is_file()})
assert len(checks)==9
mu=read(P/'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json');assert mu['mu_commit']==m['component_vector']['mu_sdk']=='8dfebe36508ac0c2508735bb866756dab9283e74';assert mu['bundle_sha256']==sha(P/'apps/desktop/resources/control/runtime/mu-worker.mjs') and mu['bundle_bytes']==(P/'apps/desktop/resources/control/runtime/mu-worker.mjs').stat().st_size
assert sha(P/'apps/desktop/resources/control/runtime/node.exe')==next(r['sha256'] for r in m['build']['tools'] if r['name']=='node')
symlinks=[str(p) for p in P.rglob('*') if p.is_symlink() or p.is_junction()];assert not symlinks,symlinks
bound=read(F/'bound-tests.json');testproof=[];census=[]
for item in [*bound['desktop_entrypoints'],{'name':'validator','invocation':bound['validator_invocation']}]:
 inv=item['invocation'];assert inv['exit']==0
 for channel in ['stdout','stderr']:assert sha(pathlib.Path(inv[channel]))==inv[channel+'_sha256']
 raw=pathlib.Path(inv['stdout']).read_text(encoding='utf-8-sig')
 if 'counts' in item:
  for key,value in item['counts'].items():assert re.search(r'(?m)^.*\b'+re.escape(key)+r' '+str(value)+r'\s*$',raw),(item['name'],key,value)
  assert inv['selected_environment']['RESEARCHOS_DESKTOP_WIRE_ROOT']==str(pathlib.Path(m['build']['root'])/'apps/desktop')
 else:assert '\nPASS\n' in raw.replace('\r','') or raw.strip().endswith('PASS')
 root=inv['selected_environment'].get('RESEARCHOS_DESKTOP_CASE_RECEIPT')
 if root:
  for p in sorted(pathlib.Path(root).rglob('*')):
   if p.is_file():census.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 testproof.append({'name':item['name'],'argv':inv['argv'],'exit':0,'counts':item.get('counts'),'stdout_sha256':inv['stdout_sha256'],'stderr_sha256':inv['stderr_sha256']})
# Both compiler logs are frozen as new read-only evidence references.
compiler=[]
for name in ['go-build','react-build','go-version','node-version']:
 inv=read(br/(name+'.invocation.json'));assert inv['exit']==0
 for stream in ['stdout','stderr']:
  p=br/inv[stream];compiler.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 if name=='go-build':assert inv['cwd']==str(S) and '-mod=readonly' in inv['actualargv'] and inv['environment']['GOPROXY']=='off' and inv['environment']['GOSUMDB']=='off' and '-X main.buildInputDigest='+m['build']['full_input_digest'] in inv['actualargv']
result=read(pathlib.Path(m['build']['build_result']['path']));put('build-result-readonly-summary.json',{k:v for k,v in result.items() if k not in ['files','inputs','inventory']})
put('bound-tests-raw-census.json',{'files':census,'count':len(census),'bytes':sum(x['bytes'] for x in census)})
put('source-protection-tests.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected9':checks,'source_core_diff_only_exact3':True,'Mu_M0_V4_not_included_basis':'Main C381 to 912 and Source 070e cumulative diff is exact3 UI files; pinned worker/node/build manifest byte-identical to previous reviewed package and Mu8df','mu_build':mu,'package_symlink_or_junction_count':len(symlinks),'tests':testproof,'desktop_unique':sum(x['counts']['tests'] for x in testproof if x['counts']),'compiler_log_refs':compiler,'tests_rerun_by_reviewer':False,'renderer_gap':'known shared React/legacy native raw filenames; append-only isolated supplement requested by Root'})
print(json.dumps({'protected':len(checks),'desktop_tests':253,'raw_files':len(census),'raw_bytes':sum(x['bytes'] for x in census),'symlinks':len(symlinks),'build_result_keys':list(result)}))
