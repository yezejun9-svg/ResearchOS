import datetime,hashlib,json,pathlib,re
E=pathlib.Path(__file__).parent;I=E/'inputs'
def read(name):return json.loads((I/name).read_bytes())
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()
def put(p,v):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
scope=read('Owned-Desktop-native-scope.json');proof=read('native-proof.json');result=read('native-result.json')
put(E/'002-verify.recipe.json',{'mode':'READ_ONLY_CAPTURED_PROOF_AND_EXACT_SCOPE_BOUND_FILES','bound_files':[r['path'] for r in scope['bound_files']],'forbidden':'No native rerun, process query, state/database/credential read, source write or original-resource hash refresh'})
refs=json.loads((E/'001-captured-refs.json').read_bytes());by_source={str(pathlib.Path(r['source'])):r for r in refs}
for row in refs:
    assert sha(row['local'])==sha(row['source'])==row['sha256'] and pathlib.Path(row['source']).stat().st_size==row['bytes']
def ref_check(ref):
    p=pathlib.Path(ref['path']);r=by_source[str(p)]
    assert r['sha256']==ref['sha256'] and r['bytes']==ref['bytes']
for ref in scope['bound_files']:
    p=pathlib.Path(ref['path']);assert p.is_file() and p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'],str(p)
assert scope['mode']=='OWNED_FRESH_DESKTOP_NATIVE_SMOKE_ONLY' and scope['native_launch_authorized'] is True and scope['formal_increment']==0 and scope['checkpoint_revision']==553
assert scope['candidate_commit']=='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419' and scope['candidate_tree']=='1d44a02c9483fc529b08ffe81895ec443920bdd1'
bound={str(pathlib.Path(r['path'])):r for r in scope['bound_files']}
B=pathlib.Path(scope['bundle_root']);state=pathlib.Path(scope['state_root']);P=pathlib.Path(scope['receipts_root'])
assert not state.is_relative_to(B) and not B.is_relative_to(state) and state.parent==B.parent
assert bound[str(B/'development-manifest.json')]['sha256']=='e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620'
seal=json.loads(pathlib.Path(scope['source_review_ref']['path']).read_bytes())
assert sha(scope['source_review_ref']['path'])==scope['source_review_ref']['sha256']=='2981911af85ea4163389592041a9474f0ed5ed8e027ba5ac131e3912560b939c'
assert seal['verdict']=='SOURCE_BUILD_REVIEW_PASS_NOT_NATIVE_ACCEPTED' and seal['candidate_commit']==scope['candidate_commit']
outer=read('085-owned-desktop-native.recipe.result.json');assert outer['native_exit']==0
for ref in [outer['recipe'],outer['stdout'],outer['stderr'],proof['scope_ref'],proof['native_result'],result['stdout_ref'],result['stderr_ref']]:ref_check(ref)
assert result['native_exit']==0 and result['timed_out'] is False and result['raw_capture_status']=='SEALED_AFTER_LAUNCHER_EXIT'
assert result['state_created'] is True and result['formal_increment']==0
pre=read('native-invocation.pre.json');spawn=read('spawn.json')
ref_check(pre['scope_ref'])
expected=[str(B/'apps/desktop/resources/control/runtime/node.exe'),str(B/'launch-development.mjs'),'--bundle',str(B),'--state',str(state),'--launch','--smoke']
assert pre['argv']==spawn['argv']==expected and pathlib.Path(pre['cwd'])==B
assert result['owned_launcher_pid']==spawn['owned_launcher_pid']==29668
assert set(k.upper() for k in pre['environment_keys']) <= {'SYSTEMROOT','WINDIR','COMSPEC','OS','PATH','PATHEXT'}
start=datetime.datetime.fromisoformat(result['started_at']);end=datetime.datetime.fromisoformat(result['ended_at'])
assert datetime.datetime.fromisoformat(scope['created_at'])<datetime.datetime.fromisoformat(pre['at'])<=start<end<datetime.datetime.fromisoformat(proof['at'])
duration=(end-start).total_seconds();assert duration<pre['timeout_seconds']==120
raw=(I/'stdout.raw').read_bytes();assert hashlib.sha256(raw).hexdigest()==proof['raw_report_sha256']
lines=[line for line in raw.decode('utf-8',errors='strict').splitlines() if line]
assert len(lines)==3 and '\ufffd' not in '\n'.join(lines)
reports=[json.loads(line.removeprefix('ROS_DESKTOP_REPORT ')) for line in lines[:2]]
final=json.loads(lines[2]);ready,stopped=reports
assert ready==proof['ready_report'] and stopped==proof['shutdown_report']
assert ready['event']=='ready_to_show' and stopped['event']=='shutdown_confirmed'
assert ready['management_state']=='READY' and ready['host_health']=='UP'
assert ready['native_probe']['ok'] is True and ready['native_probe']['protocol_status']=='COMPLETED'
r=ready['renderer'];assert r['bridge'] is True and r['react_root'] is True and r['mounted_title']=='项目入口' and r['navigation']==10
identity=ready['owned_core_identity']
assert identity==stopped['owned_core_identity']==final['owned_core_identity']
assert identity=={'pid':12144,'created_ns':'1792921594448754600','image_sha256':'3e45078c3108418f90092b02291ff79c3dca100afcec5bc4a95f085394bf185c','host_id':'host-b86c7d65bcf4'}
assert identity['image_sha256']==bound[str(B/'apps/desktop/resources/control/researchos-control.exe')]['sha256']
assert stopped['process_exit_confirmed'] is True and final['status']=='NATIVE_SMOKE_CONFIRMED' and final['renderer_title']==r['mounted_title']
assert ready['pid']==84648 and ready['management_diagnostic_truncated'] is False
pidpre=read('exact-owned-pids-postcheck.pre.json');pidresult=read('exact-owned-pids-postcheck.result.json')
assert pidpre['pids']==[84648,12144] and pidresult['native_exit']==0
for ref in [pidresult['stdout'],pidresult['stderr']]:ref_check(ref)
rows=json.loads((I/'exact-owned-pids-postcheck.stdout.raw').read_text(encoding='utf-8-sig'))
assert rows==proof['exact_owned_pids_absent'] and len(rows)==2
assert {r['pid'] for r in rows}=={84648,12144} and all(r['present'] is False and r['creation'] is None for r in rows)
assert 'foreach($ownedId in @(84648,12144))' in pidpre['argv'][-1] and '-Filter ("ProcessId="+$ownedId)' in pidpre['argv'][-1]
outerfinal=json.loads((I/'085-owned-desktop-native.recipe.stdout.raw').read_bytes())
assert outerfinal['native_exit']==0 and outerfinal['owned_core']==identity and outerfinal['owned_desktop_pid']==84648 and outerfinal['exact_pids_absent'] is True
ref_check(outerfinal['proof'])
before=read('originals.before.json');after=read('originals.after.json');assert before==after
assert before['dirty_path_count']==20
assert not (P/'originals.after.error.json').exists()
assert all(proof[k] is False for k in ['original_data_or_process_actions','C57_recovery_or_fullrestart_acceptance','installer_acceptance']) and proof['formal_increment']==0
preservation={k:len(v) if isinstance(v,(dict,list)) else v for k,v in before.items()}
summary={'verdict':'OWNED_NATIVE_SMOKE_EVIDENCE_REVIEW_PASS_LIMITED','scope_sha256':sha(I/'Owned-Desktop-native-scope.json'),'proof_sha256':sha(I/'native-proof.json'),'candidate_commit':scope['candidate_commit'],'bundle_manifest_sha256':bound[str(B/'development-manifest.json')]['sha256'],'scope_bound_files_verified':len(bound),'captured_refs_verified':len(refs),'native_exit':0,'outer_native_exit':0,'pid_postcheck_native_exit':0,'timed_out':False,'raw_capture_status':result['raw_capture_status'],'native_duration_seconds':duration,'owned_launcher_pid':29668,'owned_desktop_pid':84648,'owned_core_identity':identity,'renderer_title':r['mounted_title'],'navigation_count':r['navigation'],'native_protocol_status':ready['native_probe']['protocol_status'],'captured_exact_owned_pids_absent':rows,'preservation_before_after_equal':True,'preservation_summary':preservation,'reviewer_native_reruns':0,'reviewer_process_queries':0,'original_resource_direct_reads':0,'formal_increment':0,'C57_recovery_or_acceptance':False,'installer_acceptance':False,'blocking_findings':0,'diagnostics':[]}
put(E/'NATIVE-PROOF-INDEPENDENT-CHECK.json',summary)
print(json.dumps(summary,ensure_ascii=False))
