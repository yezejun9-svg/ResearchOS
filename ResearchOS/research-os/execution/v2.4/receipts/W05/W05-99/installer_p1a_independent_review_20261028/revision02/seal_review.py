import datetime,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):(R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=[(R.parent/'REVIEW.json','83555b309a7d49e0a238b1490f4b735100ccf5f8c6de9a937ad4cea025ae9e8d'),(R.parent/'revision01/REVIEW.json','1bd24e8b273f5c91627f0321ac31a5846cdc1953794c3f899dd675164c7e07dc')]
for path,want in prior:assert sha(path)==want
put('EVIDENCE-MANIFEST.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('REVIEW.json','REVIEW.md','REVIEW-HASHES.json','EVIDENCE-MANIFEST.json')],'scratch':'Retained per Root; no deletion retry. Contains only scoped admission fixtures; no product payload copied.'})
review={
 'schema':'researchos.installer-p1a-independent-final-source-static-review.v1','status':'ACCEPTED_SOURCE_STATIC_P1A_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/installer_p1a_independent_review','formal_increment':0,'formal_acceptance':False,'parent_acceptance':False,'source_static_accepted':True,'native_installation_accepted':False,
 'candidate':json.loads((R/'binding.json').read_bytes()),
 'findings':[],
 'closed_findings':[
  {'id':'P1A-R1','closure':'Carried from revision01 no-replace MoveFileW Windows execution tests; main.go/main_test.go hashes unchanged, no Go suite rerun.'},
  {'id':'P1A-R2','closure':'Canonical/reparse/direct-child/non-overlap/create-new protections retained byte-for-byte outside scope admission diff. Current 7-test suite again exercises dotdot/overlap/junction; independent new-scope negatives reject noncanonical/overlap/absent roots before writes.'},
  {'id':'P1A-R3','closure':'Ownership-based xb failure writing retained; current tests confirm preexisting receipts byte-for-byte unchanged. Independent CLI early failures produce no output/receipts; prior first-failure preservation and foreign inode checks retained.'},
  {'id':'P1A-R4','closure':'Removed temporary absolute scope path and fixed digest. CLI requires explicit --scope-sha256, checks digest syntax and exact scope bytes before JSON, then recognized schema/owner/worktree and canonical non-overlapping existing roots. Actual cp571 scope supplied with independently verified expected digest accepted; two new fixture scopes and same bytes at a different canonical path accepted without source edits. Internal test-injection roots are not represented as a CLI authorization mechanism.'}
 ],
 'accepted_scope':[
  'Exact combined five-file source change from original base 5c4c94022bd92da68ef544f2779527bfe065c428 through final HEAD 69f91b72e919c01a2297da31109e59bf7a54ccbf, with reviewed exact4 then exact2 repairs; no source paths outside original five.',
  'Static, offline, fresh-stage payload construction/finalization for the exact frozen product marker and trusted caller supplied authorization scope.',
  'Trusted payload digest, original 132 payload inventory preservation, five roles, location-specific verifier regeneration and Go/JS identity compatibility bounded by original independent artifacts/fixtures plus reviewed immutable references.',
  'Atomic no-replace marker publication and receipt acquisition protections under tested static scenarios. No broad installer transaction claim.'
 ],
 'current_checks':{'python_regression_tests':7,'independent_bad_admission_cases':11,'same_bytes_new_scope_path':'PASS','two_distinct_scope_root_pairs':'PASS','actual_cp571_external_pin':'PASS','valid_scope_cli':'Reached frozen-source validation on deliberately empty fixture source; no product build/native launch','missing_pin_cli_exit':2,'exact2_clean_and_source_blob_hashes':'PASS','unchanged_finalizer_and_schema_sources':'PASS','unchanged_payload_manifest_sha256':'2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c','unchanged_revision01_finalizer_sha256':'016a45961612fb1facfebfec316fae9f3d35528087743cab9205a8e8c88d2171'},
 'trust_boundary':'This is a trusted local construction tool. The expected scope digest must come from the already authorized caller/control plane. Passing an arbitrary scope together with a digest computed from that same arbitrary input does not establish authorization. Recognized schema/owner/worktree constrain interpretation; they are not an authentication signature.',
 'evidence_reuse':[{'path':str(p),'sha256':h,'preserved':True} for p,h in prior],
 'limitations':[
  'Final acceptance is SOURCE/STATIC only. Full22parents42formal and W05 parent completion remain unchanged; formal increment 0.',
  'No product native/CLI/Electron/Core, installer/NSIS, registry/PATH/shortcuts, user-data migration, upgrade/rebind/rollback/uninstall or C57 runtime-verifier replacement execution.',
  'No full Go suite, compiler build, payload copy, full new-payload rehash or relocation repeated in revision02. Current production artifact manifest/finalizer hashes verified; new complete builder run is author evidence. Original independent all-file/relocation evidence and revision01 no-replace tests are explicitly reused by immutable references.',
  'Go product loader compatibility was source-contract inspection; actual JS loader previously ran on four roots. No new product consumer execution in this increment.',
  'Original file-symlink test remains SKIP_PRIVILEGE. Junction/hardlink observations are their own evidence and do not erase this skip.',
  'No broad concurrent filesystem mutation, maintenance admission, journal, crash/power-loss transaction or final directory durability qualification.',
  'No Git gc/repack/whole-repo fsck; earlier unrelated bad-tree maintenance event remains outside this task.',
  'Independent agent shares same OS account; not a protected holdout. Old evidence/failures retained. Scratch retained per Root, no cleanup retry.'
 ],
 'integration_note':'Source/static review gate is satisfied for the pinned final commit. Root remains owner of any integration/checkpoint update; this reviewer changed only new review receipts.',
 'evidence_manifest_sha256':sha(R/'EVIDENCE-MANIFEST.json')
}
put('REVIEW.json',review)
md='''# Installer P1a revision02 — ACCEPTED_SOURCE_STATIC_P1A_ONLY

本轮接受固定提交 `69f91b72e919c01a2297da31109e59bf7a54ccbf`（tree `f7cbb41dfc4cf5a5ef730161bc58afc1ec44c599`）的 **P1a 源码与静态构建范围**。R1–R4 均已关闭，未发现新的阻断项。正式增量 **0**，不表示 W05、父任务、22/42 正式验收或实际安装完成。

R4 修复已独立验证：临时 cp570 路径/hash 常量已移除。CLI 要求显式 `--scope` 与外部 `--scope-sha256`，先比对摘要，再解释 schema/owner/worktree 与授权根。当前 Root 给定 cp571 摘要可准入；同字节 scope 换位置、两份不同 scope/授权根无需改源码均可准入。真实 CLI 使用有效 fixture scope 已进入后续 frozen-source 检查，缺少摘要则由 argparse 拒绝。fixture 故意为空，没有构建或运行产品。

本轮 7 个 Python 回归测试通过；新增独立检查覆盖空/错误摘要、错误 schema/owner/worktree、缺失或非字符串根、dotdot、重叠及不存在的根，均未写 output/receipts。畸形 JSON 配错摘要时先得到摘要错误，确认 hash-before-parse。R2 路径/junction 和 R3 已有回执保护无回退。R1 的 Go no-replace 代码和测试摘要与 revision01 相同，沿用前轮 Windows 实际提交/竞争保护证据，不重复跑 Go。

已核对 exact2 clean、提交 blob 和本地源码摘要；finalizer 源码、Go 测试及 payload schema 均未变。revision02 的 manifest 摘要仍为 `2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c`，finalizer 摘要仍为 `016a45961612fb1facfebfec316fae9f3d35528087743cab9205a8e8c88d2171`。作者使用新 scope 的完整构建回执已读取并固定引用；本轮独立检查没有重复全量 payload rehash、复制或 relocation。

接受范围仅包含已授权的原五个文件、精确 frozen product marker、受信调用方提供授权 scope 的静态 fresh-stage 构建/finalization。原独立全量 inventory、五角色、跨位置 identity、verifier final path/hash 与只读 JS loader 证据，以及 revision01 的 no-clobber 测试，按固定摘要复用。新目录产物的完整构建属于作者证据，不能表述为本轮独立全量复验。

预期 scope 摘要必须来自已授权调用方或控制面；对任意输入自行计算摘要再传入，不构成授权。本工具是本地施工工具，schema/owner 校验也不是认证签名。

仍未覆盖实际安装、原生产品启动、registry/PATH、用户数据迁移、升级/回滚/卸载、C57、维护门、事务 journal 或掉电恢复。先前 file-symlink 权限 SKIP 保留，不能由 junction/hardlink PASS 替代。Go consumer 兼容性仍是源码合同检查，JS loader 是先前真实只读执行。本轮没有修改共享状态、修复 Git 历史对象或重试清理。

旧封卷和失败记录保持原摘要；scratch 按 Root 要求保留。详细命令、输出和输入引用见 `EVIDENCE-MANIFEST.json`。源码/静态独立审查关卡已满足，任何整合与共享 checkpoint 更新由 Root 单独负责。
'''
(R/'REVIEW.md').write_text(md,encoding='utf-8')
put('REVIEW-HASHES.json',{'status':review['status'],'formal_increment':0,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in (R/'REVIEW.json',R/'REVIEW.md',R/'EVIDENCE-MANIFEST.json')]})
print((R/'REVIEW-HASHES.json').read_text(encoding='utf-8'))
