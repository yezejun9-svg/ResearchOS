import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).parent
def read(n):return json.loads((E/n).read_text(encoding='utf-8-sig'))
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
denial={'schema':'researchos.cleanup-policy-result.v1','recipe':'cleanup.recipe.json','native_exit':None,'execution_started':False,'tool_error':'CreateProcess Rejected: blocked by policy','target':'D:/作品集/ResearchOS/research-os/.local/qualification-projection-r2-independent-review-20261015','disposition':'Retained after one policy rejection. No alternate deletion attempted. Prior A-r1 denied directory not touched or retried.'}
save('cleanup.result.json',denial)
with (E/'diagnostic-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'event':'new_r2_owned_temp_cleanup_policy_denial',**denial},ensure_ascii=False)+'\n')
diag=read('diagnostic-audit.json');diag['reviewer_new_diagnostics'].append({'event':'new_r2_owned_temp_cleanup_policy_denial',**denial});save('diagnostic-audit.json',diag)
review=read('review.json');review['cleanup']=denial;save('review.json',review)
with (E/'review.md').open('a',encoding='utf-8') as f:f.write('\n独立计数：176 = 20顶层 + 156子测试，3 package PASS；补充67 = 3顶层 + 64子测试，1 package PASS；均零fail/skip。\n\n本轮新建A-r2临时目录的一次清理命令在启动前被自动策略拒绝，构建/缓存保留；没有尝试绕过，也未触碰此前A-r1被拒绝目录。recipe与policy结果已单独记录。\n')
files=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json']
save('evidence-manifest.json',{'schema':'researchos.qualification-projection-A-r2-independent-evidence.v1','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':review['verdict'],'candidate_commit':review['candidate_commit'],'candidate_tree':review['candidate_tree'],'files':files,'self_excluded':True})
print(json.dumps({'review_md_sha256':sha(E/'review.md'),'review_json_sha256':sha(E/'review.json'),'evidence_manifest_sha256':sha(E/'evidence-manifest.json'),'file_count':len(files),'verdict':review['verdict']},ensure_ascii=False))
