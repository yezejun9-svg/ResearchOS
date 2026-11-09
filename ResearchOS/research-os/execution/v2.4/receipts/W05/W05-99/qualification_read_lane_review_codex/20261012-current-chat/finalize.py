import datetime,hashlib,json,pathlib,subprocess
OUT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
BUNDLE=SRC/'.local/readlane-sourcebundle-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def row(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def put(n,v):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
before=read(OUT/'binding-before.json')
drift=[x['path'] for x in before['refs'] if sha(pathlib.Path(x['path']))!=x['sha256']]
assert not drift,drift
refs=[]
final=read(BUNDLE/'final-candidate-03.json')
assert sha(BUNDLE/'final-candidate-03.json')=='92f0efa3837c7924b50f8453c4270adb4e22e694d7e25062435c77382599832f'
refs.append(row(BUNDLE/'final-candidate-03.json'))
for x in final['files']:
    p=BUNDLE/x['name'];assert sha(p)==x['sha256'];refs.append(row(p))
observations=[]
for directory in ['author-targeted-raw','supplemental-raw']:
    for p in (OUT/directory).rglob('observations.json'):
        value=read(p)
        for c in value['children']:
            assert c['exitCode']==0 and c['closeCode']==0 and all(c[k] for k in ['spawned','exited','closed','stdinClosed','stdoutClosed','stderrClosed']) and not c['killRequested'],c
        observations.append({'path':str(p.relative_to(OUT)),'http':len(value['http']),'children':len(value['children']),'sha256':sha(p)})
put('verification-final.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_refs_unchanged':len(before['refs']),'drift':drift,'late_author_append_only_refs':refs,'observations':observations,'http_count':sum(v['http'] for v in observations),'actual_validator_children':sum(v['children'] for v in observations),'all_validator_children_exit0_and_closed':True,'metadata':'c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0 + vcs.modified=true preserved','source_bytes_bound_to':'cbe5404367e2ea1f00e1ea4552d59d5d0d8eedf9'})
put('report.json',{'schema':'researchos.qualification-read-lane-independent-review/1','verdict':'REQUEST_CHANGES','source_commit':before['source_commit'],'source_tree':before['source_tree'],'findings':[{'id':'R1','priority':'P2','path':'apps/desktop/main/lib/ipc.js','lines':[102,155,160],'title':'Side-effecting methods inherit presentation-read exemption','mechanism':'!write && !authorityRead classifies provider.probe and workspace.register as presentation reads; neither reserves write sequence nor write barrier, so Main authority scope completes while such an operation is queued/in-flight','evidence':['supplemental.stdout.raw','supplemental-cases.json','supplemental-raw/47fa441f-0559-450c-9cfe-a1510bdd521a/observations.json','supplemental-raw/8d84f122-82a5-4236-b876-cd032fdc6955/observations.json'],'actual_model_calls':0}], 'independent_runs':{'author_targeted':{'tests':21,'pass':21,'fail':0,'exit':0},'management':{'tests':11,'pass':11,'fail':0,'exit':0},'supplemental':{'tests':11,'pass':9,'fail':2,'exit':1},'total':{'tests':43,'pass':41,'fail':2,'skipped':0,'cancelled':0}},'author_full_run':'203/203 log reviewed, not rerun here','build_assessment':'Full 6444 input hashes match and exact3 bytes equal frozen HEAD blobs. Existing dirty precommit build is usable as byte-bound fixture evidence only, metadata remains C381 dirty; Source is rejected for R1; subsequent repaired Root package must be freshly rebuilt and honestly component-bound.','reverse_order_assessment':'Single production createTransport serializes queued successful HTTP completion. Author dual-instance inversion is supplemental IPC robustness. Independent tests cover display-first while authority waits for credential using one real transport, and single-lane latest-ticket rejection.','source_binding_refs':'binding-before.json','late_author_refs':'verification-final.json','report_md_sha256':sha(OUT/'report.md'),'D_writes':0,'product_launches':0,'real_sqlite_reads':0,'actual_model_calls':0,'actual_external_tool_calls':0,'source_or_canon_changes':0,'formal_increment':0,'parent_acceptance':False})
members=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['manifest.json','seal.json']]
put('manifest.json',{'schema':'researchos.independent-review-evidence-manifest/1','members':members,'count':len(members),'location':'C_ONLY_D_DISK_FULL_NO_MIRROR_CLAIM'})
put('seal.json',{'report_sha256':sha(OUT/'report.json'),'report_md_sha256':sha(OUT/'report.md'),'manifest_sha256':sha(OUT/'manifest.json')})
print((OUT/'seal.json').read_text());print(json.dumps({'files':len(members),'http':sum(v['http'] for v in observations),'children':sum(v['children'] for v in observations)}))
