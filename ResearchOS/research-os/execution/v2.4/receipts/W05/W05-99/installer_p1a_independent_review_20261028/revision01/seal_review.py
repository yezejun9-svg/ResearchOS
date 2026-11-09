import datetime,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):(R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(R.parent/'REVIEW.json')=='83555b309a7d49e0a238b1490f4b735100ccf5f8c6de9a937ad4cea025ae9e8d'
assert sha(R.parent/'REVIEW.md')=='874027d649607ebaf887e504422582f755b65fb2a8a9a3bbb32e2a4f2a3515f1'
put('EVIDENCE-MANIFEST.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ('REVIEW.json','REVIEW.md','REVIEW-HASHES.json','EVIDENCE-MANIFEST.json')],'scratch':'Retained per Root; no deletion attempted; caches excluded.'})
review={
 'schema':'researchos.installer-p1a-independent-revision-review.v1','status':'NEEDS_REVISION','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/installer_p1a_independent_review','formal_increment':0,'integration_approved':False,
 'candidate':json.loads((R/'binding.json').read_bytes()),
 'prior_review_sha256':'83555b309a7d49e0a238b1490f4b735100ccf5f8c6de9a937ad4cea025ae9e8d',
 'closed_findings':[
  {'id':'P1A-R1','status':'CLOSED_FOR_STATIC_PUBLICATION_CONTRACT','evidence':['go-publication.stdout.raw','independent_test.go'],'reason':'MoveFileW no-replace closes Lstat/Rename overwrite. Actual Windows success, preexisting and controlled-before-commit cases pass. Independent test verifies both source temp and concurrent target remain intact on refusal. Canonical long root 315 chars (source 343) passes on current host. Same staged directory ensures same filesystem. No broad transaction/durability qualification.'},
  {'id':'P1A-R2','status':'ORIGINAL_PATH_ESCAPE_CLOSED; NEW_SCOPE_REUSE_REGRESSION_R4_OPEN','evidence':['python-author.stderr.raw','source.diff'],'reason':'canonical_path now rejects dotdot, exact spelling aliases and existing reparse ancestors; validated direct-child output/receipt roots cannot overlap candidate/each other and must not exist. Dotdot/overlap/junction tests pass. The new authority binding introduces R4 below.'},
  {'id':'P1A-R3','status':'CLOSED_FOR_OWNED_FAILURE_RECEIPTS','evidence':['python-author.stderr.raw','observations.json','preexisting-cli.command.json'],'reason':'Receipt ownership is set only after exclusive mkdir; failure write rechecks directory identity and uses xb. Preexisting receipt tests unchanged, independent first failure preserved across second attempt, foreign inode refused. Actual CLI early refusal leaves preexisting directory unchanged. No concurrent ancestor-swap qualification claimed.'}
 ],
 'findings':[{'id':'P1A-R4','priority':'P2','blocking':True,'title':'Builder cannot consume subsequent explicitly trusted scopes','file':'ops/release/product_installer/build.py','lines':[24,25,163,169],'evidence':['identical-scope-new-path.json','explicit-new-scope.json','observations.json','candidate-build.py'],
 'observed':'bound_roots compares both an absolute cp570 scope pathname and a compiled-in SHA. An identical-byte copy (same trusted SHA) under reviewer root is rejected; a new scope with new artifact/receipt roots is also rejected. CLI has only --scope, no trusted-scope digest/provider input. Internal authorized_roots argument bypass exists only in Python calls/tests and is not a scoped authenticated CLI entry.',
 'impact':'The reusable builder is tied to this machine and temporary review scope. New authorized build scopes require editing production builder source, and removing/moving historical receipt cp570 breaks the CLI. Scope pinning should bind invocation authority rather than permanent construction history.',
 'minimal_fix':'Accept a new explicit trusted scope binding from the authorized caller (for example --scope plus out-of-band expected --scope-sha256); compare exact raw bytes before consuming roots. Validate required scope contract/worktree/root fields and continue canonical/reparse/direct-child/non-overlap/create-new checks. Do not treat a self-computed digest or arbitrary roots alone as authorization. The exact frozen source marker/product provenance may remain pinned as required by P1a.',
 'required_tests':['Correct explicit digest permits equivalent scope at another canonical path','Two distinct explicitly trusted scopes select their own valid isolated roots without source edits','Wrong/empty digest and malformed scope reject before writes','R2 dotdot/reparse/overlap and R3 preexisting/foreign receipt tests remain passing'],
 'minimal_source_paths':['ops/release/product_installer/build.py','tests/release/product_installer_build_test.py']}],
 'verification':{'author_python_tests':5,'targeted_go_exit':0,'go_cases':['success','preexisting','appears-before-commit','independent preserve both files','315-char root publication'],'source_diff':'exact4 clean, pinned HEAD/tree/source blobs confirmed','payload_manifest':'unchanged sha256 2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c','new_finalizer_sha256':'016a45961612fb1facfebfec316fae9f3d35528087743cab9205a8e8c88d2171'},
 'limits':['Only revision delta and prior R1-R3 regressions tested; no full payload relocation repeated. Prior static artifact evidence remains scoped to its recorded hashes.','New finalizer artifact hash verified against author manifest; production finalizer was not independently rebuilt in this revision. Go publication code was independently compiled/executed as tests.','No product native, installation, registry, data migration, shared state edit, Git maintenance or formal acceptance.','No new symlink privilege attempt; prior file-symlink SKIP remains, current Python junction test passes.','Old sealed review unchanged; no scratch deletion retry. Scratch retained for further revision.','Same user independent review, not a protected holdout.'],
 'evidence_manifest_sha256':sha(R/'EVIDENCE-MANIFEST.json')
}
put('REVIEW.json',review)
md='''# Installer P1a revision01 — NEEDS_REVISION

候选 `60d2787e15e4a87b291f08c853d3738600c83734` / tree `bb0ace8936b34a45b5de03c845250b3a18c37417` 的 exact4 clean 与源码摘要已核对。原 **R1–R3 已按静态范围复验关闭**，但新增 **R4：构建工具固定绑定本轮临时 scope**，本轮仍不批准整合。正式增量 **0**。

R1 改为同目录 `MoveFileW` 不覆盖提交。实际 Windows 成功、已有目标、提交前目标出现均通过；独立探针还确认拒绝时 temp 和目标字节均保留，315 字符 canonical root 提交成功。这里只证明 marker publication，不代表安装事务、维护门或掉电恢复合格。

R2 的 dotdot、overlap、junction 边界测试通过；源码现已在写入前验证 canonical 路径、现存祖先 reparse、授权根直属子目录、互不重叠和 create-new。R3 仅在独占 mkdir 后记录目录身份，失败回执以 `xb` 写入。已有目录保持不变、首条失败不被覆盖、foreign inode 拒绝均有本轮证据。

**P1A-R4 · P2（阻止本轮接受）**：`build.py:24–25,163–169` 把 cp570 的绝对文件路径和摘要写死。相同 scope 字节换路径，或提供新授权根的后续 scope，都会报 `revision scope differs from approved exact4 authority`。CLI 只有 `--scope`；内部 `authorized_roots` 测试注入不构成新的受信 scope CLI 通道。因此该工具离开本轮目录、历史回执迁移或进入下一次授权构建时就不能工作。

最小后续只需修改 `build.py` 与对应 Python 测试：由已授权调用方显式提供 scope 和外部预期摘要，先核对原始字节，再验证 scope 合同/worktree/授权根；继续保留 R2/R3 全部边界。禁止以“对任意输入自算摘要”代替授权。原 P1a 的 frozen source marker/product provenance 固定绑定可继续保留。

新增测试应证明两份不同且显式受信的 scope 无需改源码即可选择各自授权根；错摘要、空摘要、畸形 scope 在写入前拒绝；dotdot/reparse/overlap/preexisting receipt 仍拒绝。

本轮只跑 5 个 Python 回归测试、针对性的 Go publication 测试和新增小探针，没有重复全量 relocation。payload manifest 摘要未变，新 finalizer hash 与作者回执相符；新生产 finalizer 未独立重编译，Go publication 源码已独立编译执行。没有产品原生启动、安装、registry、迁移、共享状态修改或正式验收。先前 symlink 权限 SKIP 仍保留，不据当前 junction PASS 替代。

旧封卷保持原摘要。scratch 按 Root 要求保留，没有重试先前被拒绝的清理。证据、命令和完整输出见 `EVIDENCE-MANIFEST.json`。
'''
(R/'REVIEW.md').write_text(md,encoding='utf-8')
put('REVIEW-HASHES.json',{'status':'NEEDS_REVISION','formal_increment':0,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in (R/'REVIEW.json',R/'REVIEW.md',R/'EVIDENCE-MANIFEST.json')]})
print((R/'REVIEW-HASHES.json').read_text(encoding='utf-8'))
