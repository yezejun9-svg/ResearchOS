import json, hashlib, pathlib, datetime, re
E=pathlib.Path(__file__).parent
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,v):(E/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
denial={'event':'owned_temp_cleanup_policy_rejected','action':'Remove-Item -LiteralPath verified own D:/作品集/ResearchOS/research-os/.local/qualification-projection-independent-review-20261015 -Recurse -Force; remove own E/__pycache__','native_exit':None,'execution_started':False,'tool_error':'CreateProcess Rejected: blocked by policy','disposition':'All targets retained. No alternate tool/path/command bypass attempted. Previously denied files not deleted.'}
with (E/'diagnostic-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(denial,ensure_ascii=False)+'\n')
save('cleanup-policy-denial.json',denial)
report=read(E/'review.json');report['cleanup']=denial;save('review.json',report)
artifact=read(E/'independent-build-artifact.json');artifact['disposition']='retained: cleanup command rejected by automatic policy; no execution or bypass';save('independent-build-artifact.json',artifact)
with (E/'review.md').open('a',encoding='utf-8') as f:f.write('\n## Cleanup policy result\n\n本任务新 Dtemp/cache/build 和 E/__pycache__ 的已验证路径 Remove-Item 清理命令在启动前被自动策略拒绝（blocked by policy）。文件保留，未更换工具或路径绕过。该拒绝不影响已记录的源码/测试结论。\n')
guard=read(E/'guard-comparison.json')
cp=ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat'
matches={}
mapping={'execution/v2.4/checkpoint.json':'checkpoint.before.raw.json','execution/v2.4/path_ownership.json':'ownership.before.raw.json','execution/v2.4/HANDOFF_RESUME_PACK.md':'handoff.before.raw.md'}
for path,change in guard['main_dirty_file_hash_changes'].items():
    matches[path]={'changes':change,'matching_root_before_raw':[]}
    for directory in sorted(cp.glob('continuation-cp50[1-9]')):
        raw=directory/mapping[path]
        if raw.is_file() and sha(raw) in change.values(): matches[path]['matching_root_before_raw'].append({'path':str(raw),'sha256':sha(raw)})
save('root-shared-drift-attribution.json',{'scope':'Only three Root-owned shared files changed; this reviewer never writes them. Initial/final hashes retained verbatim; matches below tie observations to Root CAS before captures.','files':matches})
patch=(E/'canonical-patch.raw').read_text(encoding='utf-8')
added=[line for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++')]
static=sum(len(re.findall(r'\bt\.(?:Fatalf?|Errorf?)\(',line)) for line in added)
save('static-assertion-site-recount.json',{'added_t_Fatal_Fatalf_Error_Errorf_sites':static,'method':'Regex count over added lines in exact base/candidate canonical patch; not dynamic executions','author_reported_static_sites':102})
files=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json']
save('evidence-manifest.json',{'schema':'researchos.independent-review-evidence-manifest.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NOT_ACCEPTED','candidate_commit':report['candidate_commit'],'candidate_tree':report['candidate_tree'],'files':files,'self_excluded':True})
print(json.dumps({'review_md_sha256':sha(E/'review.md'),'review_json_sha256':sha(E/'review.json'),'manifest_sha256':sha(E/'evidence-manifest.json'),'files':len(files),'static_sites':static},ensure_ascii=False))
