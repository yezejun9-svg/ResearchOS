from pathlib import Path
import json,hashlib,re,datetime
Q=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=json.loads((Q/'stage-manifest.json').read_text(encoding='utf-8'))
C=json.loads((Q/'checks01/results.json').read_text(encoding='utf-8'))
assert C['stage_inputs_unchanged'] and all(x['exit_code']==0 for x in C['commands'])
assert all(sha(Q/'stage'/n)==v['sha256'] for n,v in M['files'].items())
def raw(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
evidence={}
for row in C['commands']:
 name=row['phase'];out=Q/'checks01'/(name+'.stdout.raw');err=Q/'checks01'/(name+'.stderr.raw')
 assert sha(out)==row['stdout_sha256'] and sha(err)==row['stderr_sha256']
 evidence[name]={'exit_code':row['exit_code'],'summary':{k:int(v) for k,v in re.findall(r'(?:#|\u2139) (tests|pass|fail|cancelled|skipped|todo) (\d+)',out.read_text(encoding='utf-8'))},
  'stdout':raw(out),'stderr':raw(err),'command':raw(Q/'checks01'/(name+'.command.json'))}
assert evidence['independent']['summary']['pass']==14
assert evidence['author-replay']['summary']['pass']==4
assert evidence['baseline-boundary']['summary']['pass']==18
report={'schema':'researchos.product-v1-source-independent-review/1','decision':'APPROVED_SOURCE_FIXTURE_ONLY',
 'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/workbench_builder','author':'codex:/root',
 'formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'source_sha256':M['source_sha256'],'freeze_sha256':M['freeze_sha256'],'manifest_sha256':M['manifest_sha256'],'scope_sha256':M['scope_sha256'],
 'evidence':evidence,'stage_manifest':raw(Q/'stage-manifest.json'),'node':M['node'],'diagnostic_events':[],
 'conclusion':['Exact allowlist preserves PATH/PATHEXT/COMSPEC plus normal USERPROFILE/APPDATA/LOCALAPPDATA and required Windows/temp fields.',
  'Windows case-insensitive duplicate keys reject even with identical values; all ten allowed keys independently covered.',
  'Unknown/sensitive CLI/provider/token/proxy/config override variables are not inherited; Host data/web/listen values override ambient values.',
  'Inherited-prototype, absent/empty/nonstring values do not invent a synthetic account or environment entry.',
  'Actual entire frozen DesktopManagement CommonJS module was executed in a VM with synthetic process.env; actual start() line430 calls the helper and its output is passed to mock spawn at437-439.',
  'The actual start() success path reaches READY from an injected process/discovery/stdio fixture, with safe fixed argv and no real process.',
  'The actual start() case-collision path returns BROKEN/ENV_CASE_COLLISION before mock child dispatch; no token/override passes.'],
 'source_locations':{'helper':'apps/desktop/main/lib/desktop-management.js:793','used_by_actual_start':'apps/desktop/main/lib/desktop-management.js:430','spawn_options':'apps/desktop/main/lib/desktop-management.js:439'},
 'limitations':['Source/pure fixture approval only; installed Harness discovery, login, real Native/CLI/model/GUI and Windows execution remain NOT_RUN.',
  'Synthetic MZ fixture bytes were data for installedResources hashing, never executed.',
  'No old DB, auth files or real user profile content was read. Fixtures/cache/output stayed inside this new C QA scope.',
  'QA wrote no D source/Main/control records; it did not modify or reset original20 tracked changes or counters. Full Main20 content was not independently rehashed as part of this two-file source review.']}
with (Q/'review.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
(Q/'REVIEW.md').write_text('''# Managed environment 独立复核

结论：APPROVED_SOURCE_FIXTURE_ONLY，pending_blockers=[]，正式/产品增量0。

独立14项通过（完整allowlist、10个大小写冲突、缺失/原型/非字符串、实际start成功和拒绝路径）；作者4项与原boundary18项重放通过，syntax通过。真实冻结start方法在VM中仅注入合成process.env，installedResources读取自有C合成字节，spawn/READY/discovery均mock，证明helper不是未使用导出。

正常Windows发现环境与账户目录保留，敏感token/CLI配置/代理/运行覆盖不继承；Host指定data/web/listen不可被ambient覆盖，大小写歧义在子进程派发前拒绝。

未运行真实CLI/Native/GUI/model、未读旧DB/认证内容、未写D或修改原20项改动。review.json含exact2 pins、原freeze/manifest、命令与raw hashes。真实发现/认证/模型/Windows资格仍未验证。
''',encoding='utf-8')
paths=[Q/n for n in ['stage-and-run.py','independent.mjs','guard.cjs','stage-manifest.json','finalize.py','review.json','REVIEW.md']]
paths+=list((Q/'checks01').iterdir())
entries=[{'path':p.relative_to(Q).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths) if p.is_file()]
with (Q/'ARCHIVE_FILES.json').open('x',encoding='utf-8') as f:json.dump({'root':str(Q),'files':entries,'file_count':len(entries),'total_bytes':sum(x['bytes'] for x in entries),
 'excludes':['stage source copies','runtime/private profile','synthetic installed fixture files']},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'decision':report['decision'],'review':str(Q/'review.json'),'review_sha256':sha(Q/'review.json'),'archive_sha256':sha(Q/'ARCHIVE_FILES.json'),
 'archive_files':len(entries),'archive_bytes':sum(x['bytes'] for x in entries),'tests':{'independent':14,'author':4,'baseline':18},'source_sha256':M['source_sha256'],'formal_increment':0},ensure_ascii=True))
