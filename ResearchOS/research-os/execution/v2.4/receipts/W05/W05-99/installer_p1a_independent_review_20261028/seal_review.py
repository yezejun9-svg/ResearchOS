import datetime, hashlib, json, pathlib
R=pathlib.Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(name,value):
 (R/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cleanup_command = r"""$reviewRoot=(Resolve-Path -LiteralPath 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\installer_p1a_independent_review_20261028').Path; $scratchPath=(Resolve-Path -LiteralPath (Join-Path $reviewRoot 'scratch')).Path; if ($scratchPath -ne (Join-Path $reviewRoot 'scratch') -or -not $scratchPath.StartsWith($reviewRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe scratch path' }; Copy-Item -LiteralPath (Join-Path $scratchPath 'preexisting-receipts\failed.json') -Destination (Join-Path $reviewRoot 'preexisting-failed.json'); Remove-Item -LiteralPath $scratchPath -Recurse -Force; [pscustomobject]@{verified_cleanup_target=$scratchPath;exists_after=(Test-Path -LiteralPath $scratchPath)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $reviewRoot 'scratch-cleanup.json') -Encoding utf8"""
put('scratch-cleanup.json',{'status':'BLOCKED_BY_EXECUTION_POLICY','target':str(R/'scratch'),'exact_submitted_command':cleanup_command,'absolute_target_guard_in_submitted_command':True,'guard_or_delete_executed':False,'delete_command_executed':False,'retained':True,'retention_after_rejection':'Root explicitly requested retaining scratch for revision comparison; no further deletion attempted.','automatic_review_quote':'blocked by policy','reason':'exec_command rejected process creation for recursive Remove-Item command; no more specific reason supplied. No workaround attempted.'})
findings=[
 {'id':'P1A-R1','priority':'P1','title':'marker commit is not atomic create-new','file':'ops/release/product_installer/finalize/main.go','lines':[352,358],'evidence':['go-tests.stdout.raw','independent_test.go'],'observed':'Windows os.Rename(temp, existing) returned nil and replaced existing content. Production finalizer checks Lstat then invokes the same replacing primitive, leaving a check/use gap. This is a demonstrated primitive plus source-path proof; an orchestrated race of the complete finalizer was not claimed.','impact':'A marker created after Lstat can be overwritten, violating the explicit create-new/atomic-last requirement. Author concurrency caveat cannot satisfy this requirement.','minimal_fix':'Replace the marker commit with a Windows no-replace rename/move operation that fails if destination exists, preserve marker-last publication, and add an independent existing-destination/no-clobber test plus an injected or controlled race test. Keep temp and target on the same staged filesystem.','required_paths':['ops/release/product_installer/finalize/main.go','ops/release/product_installer/finalize/main_test.go']},
 {'id':'P1A-R2','priority':'P1','title':'builder output containment accepts dotdot escape','file':'ops/release/product_installer/build.py','lines':[143,149],'evidence':['builder-containment-observation.json','relocation_probe.py'],'observed':'Path.absolute retained .local/../../escape-review; is_relative_to(worktree/.local) returned true, while resolve() placed it outside that .local. No escaped build/write was executed. Source also does not validate existing output-parent ancestors for reparse redirection; the latter is source review, not independently exercised builder-junction evidence.','impact':'The declared output-isolated-under-worktree-.local condition is bypassable by supplied path spelling; a build can create outputs outside its allowed root.','minimal_fix':'Reject noncanonical input paths and validate canonical resolved output/receipt containment against authorized roots before mkdir or any failure write. Validate every existing ancestor for Windows symlink/reparse redirection and reject source/output/receipts overlap. Add dotdot and junction-parent boundary cases within disposable test roots.','required_paths':['ops/release/product_installer/build.py','tests/release/product_installer_build_test.py']},
 {'id':'P1A-R3','priority':'P2','title':'failure handler writes into unowned preexisting receipts','file':'ops/release/product_installer/build.py','lines':[216,220],'evidence':['preexisting-receipts-result.json','preexisting-receipts.stderr.raw','write_boundary_probe.py'],'observed':'An isolated directory containing sentinel.txt was supplied as --receipts. build refused with output and receipts must be create-new, exit 1, but the top-level except added failed.json to that already-existing directory.','impact':'Create-new refusal itself mutates a directory this invocation never acquired, violating preservation and receipt ownership.','minimal_fix':'Track receipt ownership only after successful create-new acquisition; write failure evidence only to that owned canonical directory. On early admission failure use stderr or an explicitly separate owned diagnostic destination. Add a preexisting-receipts snapshot test asserting no changes.','required_paths':['ops/release/product_installer/build.py','tests/release/product_installer_build_test.py']}
]
evidence=[]
for p in sorted(R.iterdir(),key=lambda p:p.name):
 if p.is_file() and p.name not in {'REVIEW.json','REVIEW.md','REVIEW-HASHES.json','EVIDENCE-MANIFEST.json'}:
  evidence.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-static-review-evidence/1','files':evidence,'scratch_excluded':'Disposable caches and two payload copies retained due delete policy rejection; exact marker/verifier and all logs retained outside scratch.'})
review={
 'schema':'researchos.installer-p1a-independent-source-static-review.v1','status':'NEEDS_REVISION','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'codex:/root/installer_p1a_independent_review','model_selection':'Inherited parent model; no override; independent reviewer agent, same OS user, not a protected holdout',
 'formal_increment':0,'parent_acceptance':False,'formal_acceptance':False,'integration_approved':False,
 'candidate':json.loads((R/'source-binding.json').read_bytes()),'findings':findings,
 'verified':[
  'Exact HEAD 6cf0457072bdd1d730dae961474d4d885a2cdd1b / tree 7af2395a271731f1159c367fc0ab24d69bb26751; clean candidate and exact five added paths against authorized base; committed blobs and file hashes agree.',
  'Scope and author manifest exact expected SHA256; pinned Python/Go/Node hashes checked before execution.',
  'Original frozen source marker and all 133 inventory files checked by freeze; only position-specific verifier metadata removed to yield 132 payload files. All payload files, five binary roles, source/protocol/schema/build/tool metadata and runtime/contracts/licenses inventory preserved.',
  'All four extra source cache db files are unchanged, listed and omitted. Source marker/extras were not modified or removed.',
  'Deterministic freeze reproduces exact trusted payload manifest bytes SHA256 2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c.',
  'Independent pinned module-mode rebuild produces exact finalizer SHA256 5bb69149ddb8ccc3a81bc5c940498534af53322ad99c3eb1978862500284179d. Initial GO111MODULE=off mismatch retained and explained; matching build configuration rerun is byte-identical.',
  'Compiled author finalizer rejects whitespace-mutated manifest before any staged-root write. Development/unbound manifest rejection exercised by Go tests.',
  'Author Go tests and 16 independently added path/metadata guards pass; Windows hardlink/junction rejection exercised; uppercase drive and exact component spelling/extra/missing/tamper rejection exercised.',
  'Both author finalized roots independently fully rehashed. Two additional fresh Unicode/space roots finalized with the exact shipped binary; each has 133 inventory files plus marker, correct final verifier executable/hash, same payload digest and distinct installation identities.',
  'Real committed JavaScript product-layout loadProductLayout executed read-only on all four roots with isolated LOCALAPPDATA; full inventory/roles and identities accepted and no data folder created.',
  'Go consumer productIdentity/productInventoryIdentity/productMarker and loadProductLayout contract inspected from exact committed source; field ordering, serialization types, five role order, protocol/schema, file ordering and 256 MiB per-file constraints match the actual artifact. Go consumer binary/full loader was not run.',
  'Existing marker refusal preserves sentinel in sequential test; success leaves no temp marker. Verifier metadata written before marker and full tree verified before marker preparation. Atomic no-replace remains FAILED as P1A-R1.'
 ],
 'limitations_and_skips':[
  'File symlink creation skipped by Windows missing privilege (one explicit Go subtest SKIP); junction and hardlink branches do run.',
  'No product CLI/Electron/Core native startup, registry, installer/NSIS, installation, data migration, user data writes, upgrade/rollback/uninstall, C57 replacement, live provider or formal acceptance.',
  'No protected holdout isolation: independent agent uses same Windows user and shared read-only candidate.',
  'Full native Go product loader not executed; Go compatibility conclusion is source-contract inspection plus independent digest reconstruction, while JS loader is executed.',
  'No concurrent mutation, crash/power-loss durability, installation journal or maintenance gate qualification. This does not waive explicit atomic-create-new requirement.',
  'No all-repository fsck/gc/repack run. Only selected commit/tree/blob objects read with git -c gc.auto=0 -c maintenance.auto=false. Prior author bad-tree auto-gc event remains unresolved.',
  'Scratch cleanup blocked by execution policy; caches and copied fixture payloads remain only under this reviewer receipt root. No policy bypass attempted.'
 ],
 'required_revision_scope':sorted({p for f in findings for p in f['required_paths']}),
 'evidence_manifest':{'path':'EVIDENCE-MANIFEST.json','sha256':sha(R/'EVIDENCE-MANIFEST.json')},
 'static_artifact_result':'PASS for exact hash/inventory/relocation/JS compatibility under tested sequential scenarios; source safety contract fails three findings; do not integrate as accepted P1a.'
}
put('REVIEW.json',review)
md='''# Installer P1a independent review — NEEDS_REVISION

候选 `6cf0457072bdd1d730dae961474d4d885a2cdd1b` 的静态 payload、全量 inventory、跨位置身份和只读 JS loader 复验通过，但源码存在 3 项写入边界缺口，本轮不批准整合。正式增量 **0**。

| Finding | 位置 | 结论与最小修复 |
|---|---|---|
| P1A-R1 · P1 | `finalize/main.go:352–358` | `Lstat` 后的 `os.Rename` 在 Windows 会覆盖已有目标。独立原语测试已复现。这不满足 marker create-new/atomic last。改为同卷、不覆盖目标的原子提交，并测试目标已存在及受控竞争。作者并发免责声明不能替代硬要求。 |
| P1A-R2 · P1 | `build.py:143–149` | `Path.absolute()` 保留 `.local/../../`，词法 `is_relative_to` 为 true，实际 resolved 路径已在 `.local` 外。拒绝非canonical路径，并在任何写入前核对输出/回执的授权根、祖先 reparse 和互相重叠。仅做路径判定复现，未执行越界构建。 |
| P1A-R3 · P2 | `build.py:216–220` | 指向已有回执目录时，build 拒绝 create-new，但异常处理仍向该目录添加 `failed.json`。实际隔离复现已确认。仅在本次成功获得目录所有权后写失败回执；早期拒绝不得写入既有目录。 |

建议修改仅涉及原授权路径中的 `build.py`、`finalize/main.go` 及对应两个测试文件；无需扩展源文件范围。保留本轮失败与原候选证据，修复后用新提交和新回执补验。

已确认 exact5 范围、clean HEAD/tree、所有源码 blob 摘要以及 Python/Go/Node 锁定摘要。原 marker 的 133 个 inventory 文件经核验；仅剔除位置相关 verifier metadata 后产出 132 个 payload 文件，五个 binary role、运行时、合同、licenses 和源构建元数据完整保留。四个源目录额外 cache db 仍保留，摘要与原记录一致，未进入 payload。

manifest 可确定性重建，摘要 `2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c`。按作者 module-mode 参数独立编译得到相同 finalizer 摘要 `5bb69149ddb8ccc3a81bc5c940498534af53322ad99c3eb1978862500284179d`。首次 GO111MODULE=off 编译的差异完整保留，已定位为构建配置差异。

两份作者 finalized root 全量摘要复验通过。另用精确 finalizer 在两个新建中文/空格根完成真实 payload 的静态 finalization；均为 133 inventory + marker、正确的最终 verifier 路径/hash，payload identity 相同，installation identity 不同。真实 JS `loadProductLayout` 对四根只读加载通过。Go consumer 的字段、排序、摘要算法和大小约束按精确提交源码核对；未运行 Go 产品完整 loader 或产品入口。

Go 作者测试和新增边界测试通过；新增 8 个 stage 拒绝、8 个 manifest 拒绝，以及 Windows rename 语义观察。hardlink 与 junction 实际覆盖；file symlink 因当前 Windows 权限不足明确 SKIP。顺序运行时已有 marker 保持不变、成功时 marker 最后可见且无 temp；这些成功不覆盖 P1A-R1 的并发缺口。

没有安装、registry、PATH、用户数据、迁移、原生产品启动、C57 或正式验收操作。未运行 Git gc/repack/全库 fsck；作者此前 bad-tree 事件未修复。源码审查与静态复验不能替代实际安装事务、维护门、崩溃恢复、原生生命周期或正式 22/42 验收。

所有命令、stdout/stderr、独立探针、输入绑定、marker/verifier 快照和摘要见 `EVIDENCE-MANIFEST.json`；机器可读结论见 `REVIEW.json`。

清理限制：包含绝对路径边界检查的专属 scratch 清理命令被执行层自动审批以 `blocked by policy` 拒绝启动，未提供更细理由；命令内检查及删除均未执行。确切命令和目标见 `scratch-cleanup.json`。未绕过；Root 随后明确要求保留临时缓存和两份 fixture payload，用于 revision 差异复验。
'''
(R/'REVIEW.md').write_text(md,encoding='utf-8')
put('REVIEW-HASHES.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in (R/'REVIEW.json',R/'REVIEW.md',R/'EVIDENCE-MANIFEST.json')],'formal_increment':0,'status':'NEEDS_REVISION'})
print((R/'REVIEW-HASHES.json').read_text(encoding='utf-8'))
