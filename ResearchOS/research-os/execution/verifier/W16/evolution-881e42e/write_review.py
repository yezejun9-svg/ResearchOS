import datetime,hashlib,json,pathlib
out=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/verifier/W16/evolution-881e42e')
root=pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/w16-evolution-review')
h=lambda p:'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
author='execution/receipts/W16/f1e68e3d-e065-46f9-a293-fca3ea8c6038'
assertions=[
 ('C09-01','PASS_IN_FIXTURE','Historical raw recomputation: required regression fails despite optional-function gain; candidate REJECTED; no LIVE promotion.','historical-raw-audit.json'),
 ('C09-02','PASS_IN_FIXTURE','Author raw stable hash/health and unrelated Task acceptance checked. Independent successful and degraded canaries also retain development host continuity.','probe-output.txt'),
 ('C10-01','PASS_IN_FIXTURE','Native AppContainer denied writes to all four protected fixture paths; protected hashes unchanged. Forged host policy rejected over real TCP.','forged-policy.json'),
 ('C10-02','PASS_IN_FIXTURE','Executor acceptance/self-release rejected. Real TCP denies release-principal authorship and cross-candidate acceptance replay; six raw evidence mutations fail verification.','raw-tamper-rejections.json'),
 ('C10-03','PASS_IN_FIXTURE','Separate rule proposal retains old suite/result plus separate sample refs; no acceptance or applied revision. Native tamper test independently rerun.','probe-output.txt'),
 ('C12-01','PASS_IN_FIXTURE','Degraded canary emits wrong required value despite self-score 100. Actual temporary SQLite restore inventory matches backup; exact stable binary passes native health; slot returns STABLE.','historical-raw-audit.json'),
 ('C12-02','PASS_IN_FIXTURE','Existing failed candidate becomes FROZEN; repeated canary and promotion requests return 409; durable phase reservation prevents redispatch.','probe-output.txt'),
 ('C12-03','PASS_IN_FIXTURE','Rollback journal retains threshold 0, actual required failure, raw hash; execution retains old/new build hashes, backup/restore inventory and stable-health receipt. Recovery scope explicitly isolated copy; not production qualification.','historical-raw-audit.json'),
 ('C20-01','PASS_IN_FIXTURE','Raw rubric-only candidate has identical 3/4 outcomes and required pass; independently recomputed improved=false, candidate REJECTED.','historical-raw-audit.json'),
 ('C20-02','PASS_IN_FIXTURE','Old/new rubric and scores, both builds, identical input hash, suite hash and observed outputs retained; model is explicitly NONE. Public suite is not a protected holdout.','historical-raw-audit.json'),
 ('C20-03','PASS_IN_FIXTURE','Experiment preserves NO_IMPROVEMENT and conclusion explicitly denies real-world gain/project closure.','historical-raw-audit.json')]
review={
 'schema':'RESEARCHOS_INDEPENDENT_VERIFIER_REVIEW_V1','reviewer':'codex:/root/evolution_verifier','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'model_policy':{'requested_model':'gpt-6-astra','requested_reasoning':'high','reason':'independent security and acceptance review per project AGENTS and delegation'},
 'project_id':'aede0678-7308-43dc-b9f2-cfe3d90cfdfb','source_revision':'881e42e7252a614c0f372b1e3a45a236cc64cf94','review_head':'c2aed3e1a26ab7daedf09bdfd45f4eae9583d487','source_worktree':str(root),
 'source_revision_chain':['03ff319','1d79f77','881e42e'],'author_receipt':author+'/report.json','author_report_sha256':h(root/author/'report.json'),
 'verdict':'PARTIAL','fixture_numbered_assertions':'PASS_IN_FIXTURE','G02_basis':'The frozen W16-G02 gate is explicitly FIXTURE and asks tamper, self-certification, degradation and version assertions for C09/C10/C12/C20/A16; those bounded checks are evidenced. It does not independently require LIVE control plane or formal protected holdout. This gate pass does not accept C20 as a complete case, A16 or W16.','all_four_cases_fully_accepted':False,
 'case_verdicts':{'C09':'PASS_IN_FIXTURE','C10':'PASS_IN_FIXTURE','C12':'PASS_IN_FIXTURE','C20':'PARTIAL_EVIDENCE','A16':'PARTIAL_FIXTURE_ONLY'},
 'gate_verdicts':{'W16-G01':'NOT_ACCEPTED','W16-G02':'PASS_IN_FIXTURE_SCOPE','W16-G03':'BLOCKED_W14_LIVE','W16':'NOT_ACCEPTED'},
 'numbered_assertions':[dict(zip(['id','verdict','assessment','independent_evidence'],row)) for row in assertions],
 'formal_A16':[{'id':'A16-01','verdict':'PARTIAL','gap':'Real zero-capability AppContainer candidate proved; development process is not an independent installed OS supervisor.'},{'id':'A16-02','verdict':'PARTIAL','gap':'Temporary SQLite backup restored to fresh copy and old binary health verified; active production service/database not switched or crash-reconciled.'},{'id':'A16-03','verdict':'PARTIAL','gap':'Frozen fixture gains/no-gains measured; no actual operating cycle or 6-24h successful LIVE observation.'},{'id':'A16-04','verdict':'PARTIAL','gap':'Fixture unrelated task continuity, freezing and no weight-update claim proved; production-wide task continuity not qualified.'}],
 'findings':[{'id':'W16-V-E01','kind':'EVIDENCE_GAP','severity':'P2','blocking_scope':['C20_FULL_CASE'],'claim':'C20 evidence_required includes frozen holdout results; current evidence is a public frozen deterministic suite and explicitly formal_holdout=NOT_RUN.','evidence':[author+'/0569b32dc4054c01304cb36794c24824-C20-conclusion.json','spec/v2.0/contracts/acceptance.json:C20.evidence_required'],'resolution':'Retain all three numbered C20 fixture assertions as passing, but do not represent the full case evidence requirement as satisfied until frozen holdout results are supplied or the authorized fixture interpretation is formally recorded.','security_exploit':False}],
 'reproduced_security_defects':[],
 'validation':{'go_top_level_pass':3,'go_subtest_pass':5,'go_fail':0,'named_fixture_assertions_observed_pass':9,'author_raw_execution_records_recomputed':9,'raw_hashes_pass':19,'source_hashes_pass':136,'hash_failures':0,'real_loopback_http_negative_probes_pass':5,'raw_tamper_variants_rejected':6,'strict_cli_rejection_probes_pass':4,'locked_go_hash':'PASS','review_worktree_clean':True},
 'tested_boundaries':['native positive gain vs baseline','native permission tamper','native canary required regression and actual isolated restore','raw execution integrity','public HTTP role and fixed policy enforcement','current deadline','cross-candidate exact acceptance binding','frozen candidate retry rejection','LIVE promotion fail closed','historical startup-failure/timeout raw receipt recomputation'],
 'limits':['No production scheduling, upgrades, services, provider calls, data directories, UAC, installation or schema 13/14 mutation.','Migration 0015 used only by fresh isolated test SQLite.','Trusted local RegisterEvolutionFixture/RegisterEvolutionBuild are administrative provisioning boundaries; candidate has no HTTP registration route.','Same-user role separation is not protected holdout isolation.','Host crash/restart reconciliation and stable independent OS service remain untested/unqualified.','Unchanged author C09/C20 scenarios were source-reviewed and raw-recomputed, not all independently rerun.','No whole Go suite or unchanged UI rerun.'],
 'production_acceptance':'NONE','source_modified':False,
 'key_evidence':{name:h(out/name) for name in ['probes_test.go','probe-output.txt','historical-audit-output.txt','historical-raw-audit.json','hash-audit.json','runner-rejections.json','command-receipt.json']}
}
(out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'REVIEW.md').write_text('''# W16 独立审查（源码 881e42e）

结论：整体范围 PARTIAL；W16-G02=PASS_IN_FIXTURE_SCOPE，其冻结门防篡改、自证拒绝、退化与版本断言均有证据，不要求在此 gate 完成 LIVE 控制面。11 条编号 fixture 断言均有源码与原始证据支持；C09/C10/C12 可按 fixture 范围接受。C20 的三条编号断言通过，但合同还要求“冻结 holdout 结果”，现有只有公开冻结算术套件，且原始回执明记 formal_holdout=NOT_RUN，因此完整 C20 保留 PARTIAL_EVIDENCE。不得接受整个 W16。

独立执行 3 个顶层 Go 测试、5 个子测试，全部通过；其中包含真实 native 正常收益/有界试用，C10 权限攻击和 C12 退化回滚。5 条真实 loopback HTTP 负向请求、6 项原始记录篡改、4 项 runner 非法选择均正确拒绝。19 份 raw 与 136 份源码哈希一致；另从原始输出重算 6 份回归、3 份 canary，校验执行/验收 receipt hash、同输入、独立进程、启动错误/超时及恢复 inventory。

未复现 P1/P2 安全漏洞。C20 为合同证据缺口，不是漏洞。正式 A16 仍只到 PARTIAL_FIXTURE_ONLY；隔离 SQLite 恢复和旧 binary 健康检查不能证明生产服务切换、独立 OS supervisor 或宿主崩溃恢复。W14 LIVE、W15、W18 的上游状态不由本审查解除；W16-G01/G03 与生产接线均不接受。

完整断言映射、范围及可复现命令见 review.json、command-receipt.json 和 probes_test.go。冻结 worktree 保持干净，只新增本 verifier 目录。所有运行时临时目录由 Go fixture 清理；overlay 和 probe 保留用于复现。
''',encoding='utf-8')
files={str(p.relative_to(out)):h(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-index.json'}
index={'schema':'RESEARCHOS_VERIFIER_EVIDENCE_INDEX_V1','reviewer':'codex:/root/evolution_verifier','source_revision':review['source_revision'],'review_head':review['review_head'],'review_sha256':h(out/'review.json'),'file_count':len(files),'files':files}
(out/'evidence-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'review':h(out/'review.json'),'evidence_index':h(out/'evidence-index.json'),'files':len(files),'verdict':review['verdict']},indent=2))

