import pathlib,json,hashlib,subprocess,datetime,re
E=pathlib.Path(__file__).parent;S=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/coding-profile-result-20261014');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
pins=read(E/'inputs.before.json')
for p in pins:assert sha(pathlib.Path(p['path']))==p['sha256'] and pathlib.Path(p['path']).stat().st_size==p['bytes']
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
assert git('status','--porcelain')==b'';assert git('rev-parse','HEAD').decode().strip()=='a070f16d06fee609691992ba57ee046431f8f55f';assert git('rev-parse','HEAD^{tree}').decode().strip()=='cd951533206a6a4545a6e55fec374e62289d2dd4'
(E/'git-status.final.raw').write_bytes(git('status','--short'))
fresh=read(E/'fresh-boundaries.process.json');independent=read(E/'independent-boundaries.process.json');assert fresh['native_exit']==independent['native_exit']==0
for name,count in [('fresh-boundaries',43),('independent-boundaries',2)]:
 text=(E/(name+'.stdout.raw')).read_text(encoding='utf8');assert re.search(r'pass '+str(count)+r'\b',text) and re.search(r'fail 0\b',text)
contract=read(E/'producer-contract/internal/api/contracts/domain.schema.json')['$defs'];assert contract['Id']['maxLength']==160 and contract['Id']['pattern']=='^[A-Za-z0-9][A-Za-z0-9_.:-]*$';assert contract['Revision']['minimum']==1;assert set(contract['VersionRef']['required'])=={'entity_type','id','revision','content_hash'} and contract['VersionRef']['additionalProperties']==False;assert contract['Artifact']['properties']['content_hash']=={'$ref':'#/$defs/Digest'}
attempts=read(E/'reviewer-attempts.json');attempts['attempts'].append({'attempt':3,'phase':'post-test cleanup','native_exit':1,'error':'rmdir fixture-temp failed because fixture directories remain','test_results':{'fresh_native_exit':0,'fresh_pass':43,'independent_native_exit':0,'independent_pass':2},'resolution':'Preserved original raw test results; finalizer performs only final evidence checks, no repeat testing'})
attempts['cleanup_policy_rejection']={'action':'Remove-Item -LiteralPath exact review fixture-temp -Recurse -Force after resolved path containment/reparse check','result':'automatic approval review rejected: blocked by policy','additional_reason':'not supplied','executed':False,'followup':'No alternate deletion attempted. Retained synthetic fixture files are included in FINAL-manifest.json.'}
(E/'reviewer-attempts.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cleanup={'path':str(E/'fixture-temp'),'files':sum(p.is_file() for p in (E/'fixture-temp').rglob('*')),'directories':sum(p.is_dir() for p in (E/'fixture-temp').rglob('*')),'retained_due_to_automatic_approval_rejection':True,'contains_only_current_review_synthetic_fixtures':True};(E/'retained-fixtures.json').write_text(json.dumps(cleanup,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report='''# Desktop profile_ref exact2 独立复核

结论：**SOURCE_ACCEPTED**，未发现需要修改的源码问题。接受仅覆盖本次冻结的 Desktop exact2 修复和本地验证，不代表 fresh packaged Desktop、真实页面或原产品资格链已经通过；formal increment = 0。

## 身份与范围

- Worktree: `D:/作品集/ResearchOS/research-os/.local/worktrees/coding-profile-result-20261014`。
- HEAD `a070f16d06fee609691992ba57ee046431f8f55f`，tree `cd951533206a6a4545a6e55fec374e62289d2dd4`，parent `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`。前后 clean，diff --check 通过。
- CP474 scope SHA256 `f7d5ad2626f91f70730c39d48e9062b64e917611eb1b833a7166b492dcb1269c`；作者 FINAL-report SHA256 `3dae6f571e27e684785cee7f4e2149bfa0ee11746e46dce42f03c5aa0adfc1db`；patch SHA256 `7d72a74b6b34488c1953fe109fe802bf23a4e2eaa999088e9db8e9d61aef9a12`。
- exact2：`apps/desktop/main/lib/desktop-management.js` SHA256 `74d817a1c02638b391c54ac31462a4badd0f278ff1c56b60900e3335a71a1886`；`tests/ui/desktop/coding-authorization-boundary.test.mjs` SHA256 `a04623b01cc4dd2291f084ad0676a8a128ec715e800072a6bfcfab835ce68c1e`。
- 独立冻结实际16份作者证据、scope、Node工具及本次运行涉及的 Desktop main/test 源码；所有 live source bytes 与 HEAD Git blob 比较一致。Core producer 合同通过同 HEAD 的 git show 读取并保存，确认与 parent 相同；没有改变稀疏检出配置。

## 合同与状态检查

真实 producer 链已核对：`RuntimeCodingConfirm` 返回 `prepared.ProfileRef`；`RuntimeSetupResult.ProfileRef` 为 Object；profile setup 调用 `Ref(artifact, "Artifact")`；`Ref` 精确输出 `entity_type/id/revision/content_hash` 四字段，Artifact hash取 `artifact.content_hash`。Artifact schema要求有效 Digest，虽然通用 VersionRef允许某些其他实体的 null hash，本 Artifact 引用不能为 null。domain Id 允许 1–160 个 `[A-Za-z0-9_.:-]` 字符，首字符为字母或数字。新增 `ARTIFACT_ID` 与之契合，revision 正整数且在 JS safe integer 范围内；private strictJSON已先拒绝小数或不安全整数。

生产 diff 只增加专用校验器、替换原字符串判定，并对接收后的引用使用 existing frozenCopy。所有 request、project/session、old/new model ref、REGISTERED、model/tool调用上限、scope、frozen checks、revision/config_revision判定，以及原生上下文、一次CONFIRM和原STATUS流程保持原样。校验完成后才写入 intent，复制冻结防止调用方或返回 summary 的引用改写 canonical intent。没有新增配置写入、资格调用或自动重放入口。

作者测试已覆盖真实shape的 CONFIRM→STATUS、20类非法引用、失败不结算与复制冻结。小数/unsafe revision 在 wire 层提前失败，作者已保留首次错误预期的失败，再按真实 `PRIVATE_FRAME_NUMBER` 层修正；没有将它们伪装为 validator失败。

## 独立验证

- 使用作者锁定 Node `v24.9.0`，SHA256 `5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6`，fresh运行 coding-authorization 与 desktop-management 两套：**43/43，native exit 0**，无 skipped/cancelled。
- 额外两个独立测试：10组合法边界（Id长度1/128/129/160和允许标点，revision=1或MAX_SAFE_INTEGER）通过真实 fixture CONFIRM→原STATUS，commit key一致，summary引用不可变；16项原guard逐项变异仍拒绝且不写intent。**2/2，native exit 0**。这些是隔离 fixture 流程，不是产品CONFIRM。
- 作者6次setup/test失败、测试01/02/03原始输出全部保留。reviewer两次稀疏输入枚举错误和测试结束后的清理失败也单独记录，没有重跑或覆盖已通过的原始测试。
- 原有根因诊断被复用；本轮未再次读取原数据库、未调用真实API/model、未操作GUI或任何原产品进程，也未修改Main、Source或已安装包。

## 后续与保留文件

Root可在既有授权内整合本 exact2 并 fresh rebuild/validate Desktop；包验收必须重新绑定本次 `desktop-management.js` digest。产品恢复应正常重新打开已有会话、使用已保存的新model ref继续资格链；此源码接受不授权再发 coding CONFIRM，也不保证重启后恢复旧内存intent的STATUS。

自动审批审查拒绝了对本轮证据目录 `fixture-temp` 的递归清理（返回 `blocked by policy`，没有提供更细理由）。因此106份合成夹具文件保留并纳入最终manifest，未尝试替代删除。源码/产品文件未受影响。
'''
(E/'REVIEW.md').write_text(report,encoding='utf8')
r={'schema':'researchos.desktop-coding-profile-result-independent-review/1','status':'SOURCE_ACCEPTED','findings':[],'head':'a070f16d06fee609691992ba57ee046431f8f55f','tree':'cd951533206a6a4545a6e55fec374e62289d2dd4','scope_paths':read(E/'scope.json')['paths'],'source_sha256':read(E/'author/FINAL-report.json')['changed_source_sha256'],'input_pin_count':len(pins),'source_clean':True,'fresh_tests':{'passed':43,'native_exit':0},'independent_tests':{'passed':2,'native_exit':0,'valid_ref_combinations':10,'guard_mutations':16},'product_confirm':0,'product_status':0,'database_access':0,'model_calls':0,'package_builds':0,'formal_increment':0,'source_read_finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_sha256':sha(E/'REVIEW.md'),'retained_fixture_files':cleanup['files']}
(E/'FINAL-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
members=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
(E/'FINAL-manifest.json').write_text(json.dumps({'schema':'researchos.independent-review-manifest.v1','artifacts':members},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':r['status'],'input_pin_count':len(pins),'review_sha256':sha(E/'REVIEW.md'),'report_sha256':sha(E/'FINAL-report.json'),'manifest_sha256':sha(E/'FINAL-manifest.json'),'members':len(members),'source_read_finished_at':r['source_read_finished_at']},ensure_ascii=True))
