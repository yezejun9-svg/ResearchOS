import runner as r
import json, pathlib, datetime
def counts(p):
 rows=[json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.startswith('{')]
 passes=[x for x in rows if x.get('Action')=='pass' and x.get('Test')]
 return {'run':sum(x.get('Action')=='run' and bool(x.get('Test')) for x in rows),'pass':len(passes),'top_level':sum('/' not in x['Test'] for x in passes),'subtests':sum('/' in x['Test'] for x in passes),'fail':sum(x.get('Action')=='fail' and bool(x.get('Test')) for x in rows),'skip':sum(x.get('Action')=='skip' for x in rows),'packages_pass':sum(x.get('Action')=='pass' and not x.get('Test') for x in rows),'passed_names':[x['Test'] for x in passes]}
summary={'source176':counts(r.S/'r2-final-targeted.stdout.raw'),'independent176':counts(r.E/'independent-targeted.raw'),'independent_verifier_drain':counts(r.E/'independent-verifier-and-drain.raw')}
r.save('test-summary.json',summary)
before=r.read(r.E/'before-guards.json');after=r.read(r.E/'after-guards.json')
guard={'main_head_unchanged':before['main']['head']==after['main']['head'],'main_status_unchanged':before['main']['status']==after['main']['status'],'main_index_empty':not before['main']['index'] and not after['main']['index'],'main_dirty_hash_changes':{p:{'before':h,'after':after['main']['dirty_file_hashes'].get(p)} for p,h in before['main']['dirty_file_hashes'].items() if h!=after['main']['dirty_file_hashes'].get(p)},'candidate_guard_unchanged':before['candidate']==after['candidate'],'bundle_unchanged':before['bundle']==after['bundle']}
m=r.read(r.S/'source-manifest.revision02.json')
original=r.read(r.ROOT/'execution/v2.4/receipts/W05/W05-99/qualification_projection_a_source_codex/20261015-current-chat/source-manifest.json')
expected={x['path']:x['sha256'] for x in original['changed_files']}
expected.update({x['path']:x['sha256'] for x in m['source_paths']})
combined=[{'path':p,'expected':h,'actual':r.sha(r.W/p),'matches':h==r.sha(r.W/p)} for p,h in expected.items()]
r.save('combined15-file-hashes.json',combined)
guard['combined15_hashes_match']=all(x['matches'] for x in combined)
r.save('guard-comparison.json',guard)
build=r.T/'control-review.exe';r.save('independent-build-artifact.json',{'path':str(build),'sha256':r.sha(build),'bytes':build.stat().st_size,'role':'temporary independent build, not installed product'})
prior=(r.ROOT/'execution/v2.4/receipts/W05/W05-99/qualification_projection_a_independent_review_codex/20261015-current-chat')
retained=[]
for n in ['review.json','evidence-manifest.revision02.json','formatter-recheck.json','source-manifest-utf8.raw','base-regressions.command.json','base-regressions.raw','candidate-regressions.command.json','candidate-regressions.raw']:
 p=prior/n
 if p.is_file():retained.append({'path':str(p),'sha256':r.sha(p)})
r.save('prior-evidence-retained.json',retained)
diag={'reviewer_new_diagnostics':[{'event':'initial_scope_bootstrap_read_capture_gap','operation':'Get-FileHash and Get-Content CP510 scope before own runner was created','native_exit':0,'raw_capture':'tool output only; not backfilled as original raw','source_mutation':False},{'event':'runner_display_encoding_error','native_exit':1,'child_command':'source-manifest','child_native_exit':0,'child_raw_preserved':'source-manifest.raw','error':'UnicodeDecodeError: utf-8 cannot decode byte 0xd7 at position456; child Python stdout used Windows locale','fix':'Set PYTHONIOENCODING=utf-8 and stdout UTF-8 in receipt runner; separately captured source-manifest-utf8; original raw retained','original_wrapper_traceback':'tool output only; not backfilled'}],'source_native_nonzero':[{'tag':x['tag'],'native_exit':x['native_exit']} for x in m['recorded_commands'] if x['native_exit']!=0],'source_recorded_command_count':len(m['recorded_commands']),'source_capture_gaps':r.read(r.S/'capture-gap-ledger.json'),'old_cleanup_denial':'Prior task directory not retried or touched'}
r.save('diagnostic-audit.json',diag)
consumers={
 'creation':'Prepare branches native-offline/model=none before model_config lookup; existing marker still rejects. Mu actual Task type and bound eligibility remain mandatory before final manifest hash/INSERT. Native qualification test executes and passes.',
 'stage':'Same runtimepolicy.Effective; 30 marker/authority cases and valid cloned projection, no staged worker.json on failure. Legacy/normal full8/4 exact configuration preserved.',
 'adapter':'UseNumber clone; unchanged clone validated before every one-field mutation. All30 cases reach validation/StartBridge with recomputed outer manifest hash; no native directory created on rejection; bundle/argv guards preserved.',
 'broker_preprepare':'Production brokerEffect calls validateModelEffectBeforePrepare before prepareEffectTx. Genuine first-dispatch fixture has unmodified seed reaching loopback after effect preparation; all30 mutations produce intended projection/admission guard errors with zero provider calls/new effects and unchanged ledger. Separate helper matrix corroborates.',
 'broker_pretransport':'brokerModel independently derives effective config before HTTP construction. Stage/pretransport 30-case loop rejects before provider. Native frozen-worker positive uses complete local SSE; bounded normal8/4 host wire and actual legacy brokerEffect preserve original config.',
 'verifier':'verifyMuTurn profile binding and Effective unchanged from prior A; added 30-case snapshot matrix with valid positive clone independently executed in separate test beyond176. Legacy/normal8/4 synthetic snapshots pass with matching request/ledger bindings. This is bounded predicate proof, not normal full-session acceptance.',
 'unknown_cost':'completedLocalUnknownCost calls validateCompletedLocalModelRequest after unchanged original profile/native/effect checks. Real entry tests unmodified seed and all30 mutations; ledger/effect history unchanged. Synthetic append-only effect/native observation fixture is explicitly not historical/native/live proof.'}
report={'schema':'researchos.qualification-projection-A-r2-independent-review-result.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/qualification_projection_review','model':'gpt-6-astra','reasoning_effort':'high','verdict':'LIMITED_SOURCE_ACCEPTED','candidate_commit':m['commit'],'candidate_tree':m['tree'],'main_base_commit':m['main_base_commit'],'revision_base_commit':m['base_commit'],'actionable_findings':[],'prior_findings':{'F01':'CLOSED: native-offline dispatch compatibility corrected, independent existing native test now PASS','F02':'CLOSED: UseNumber clone plus unchanged positive control before every adapter mutation','F03':'CLOSED_FOR_LIMITED_SOURCE: shared30 marker/authority mutations at consumers; true brokerEffect and cost entry controls; bounded legacy/normal8/4 host wire/verifier checks. Full normal session remains unproved and not counted.'},'consumers':consumers,'test_counts':{k:{n:v for n,v in x.items() if n!='passed_names'} for k,x in summary.items()},'build_native_exit':r.read(r.E/'independent-build.result.json')['native_exit'],'guards':guard,'patch_scope':'Own full Git4f-to-f48 diff covers15 paths; author r2-full-diff-from-4f patch is restricted to10r2 paths and is NOT the entire candidate. Its scope is explicitly corrected, no frozen author file changed.','historical_evidence':'Original22 formatter restoration and overwritten early patch/raw limitations remain retained. Source r2 has58 captured command records, nine native failures, nine read-only capture gaps and one recipe-parser preexecution gap. No missing raw backfill.','limitations':['Source and isolated fixture only; no Main merge/installed package/actual provider/actual DB/GUI/Core stop/oldRun operation','Native worker fixture binds frozen SDK artifact and loopback provider; cost/native-observation and ordinary verifier snapshots are synthetic bounded evidence','Legacy brokerEffect reaches actual loopback; normal mode invokes bounded brokerModel directly, not full normal admission/session/tool-chain acceptance','Prior normal full-session base and candidate failure remains historical unproved, not PASS','No B deterministic closure, no C old-Run repair, no parent acceptance or formal case increment'],'actual_provider_calls':0,'actual_product_data_calls':0,'formal_case_increment':0,'all22_parents':'remain open'}
r.save('review.json',report)
text='''# A-r2 独立 Source 审查：LIMITED_SOURCE_ACCEPTED

候选 `f48fca0e4013bda19913a34d91da0cd23157a08b`，tree `16e72ccf939c13142091495458ad04348a3ba660`；r2 基于 `525a9c923a8761a9491070123de3c94aa5618d71`，整个 A 基于 Main `4f4023c956f84d65743f39ce77d6c8899a21ada1`。

此前 F01–F03 已在本次 Source 范围内关闭，未发现新的可操作阻断问题。结论仅允许后续按冻结候选整合/继续相关 Source 工作，不是 Main、安装包、实际运行或正式验收。

## 修复与实测

- F01：native-offline/model=none 在 model_config 读取前分流，仍拒绝已存在 marker；原先 candidate525 失败的 `TestRuntimeCoordinatorNativeQualification` 在 f48 独立执行通过。纯 policy 也验证普通 native-offline 不变、Mu 缺失配置不回退。
- F02：adapter 使用 UseNumber，每个 mutation 先验证未修改 clone 有效，再单独改变字段。30 个 marker/authority case 通过 validation 与 StartBridge，重算外层 manifest hash，拒绝时不创建 native launch 目录。
- F03：共享 21 marker + 9 authority 变化覆盖 stage、adapter、Host preprepare/pretransport、verifier 与 cost；brokerEffect/cost 的真实函数入口均有未改首行 seed 正对照。反例不能触达 provider、新 effect 或改变原账本。Host provider identity 始终使用 original8/4，投影只用于 effective1/0。

作者176节点选择已独立重跑，另单独运行未被该选择覆盖的 `TestRuntimeMuVerificationRejectsFabrication`（含30矩阵与normal/legacy8/4快照）和旧 drain/UNKNOWN 回归。具体节点数见 test-summary.json，不能把 subtest 数写成动态断言数。独立 build 原生退出0。

## 夹具真实性与边界

TEMP BEFORE INSERT RAISE(IGNORE) 只在新建的隔离数据库中捕获 Begin 将产生的 dispatch，随后删除 TEMP trigger/table，首次 INSERT 一次带正确 manifest_hash 的 dispatch；没有改写历史 immutable dispatch。cost 测试在首次 dispatch INSERT 前构造合成 append-only PREPARED/STARTED/CONFIRMED effect 与 UNKNOWN ledger，正反例使用相同 seed 流程；这证明成本谓词，不证明历史或实际 native 闭合。

旧 marker 缺失配置经真实 legacy brokerEffect 发往 loopback，普通模式的8/4 wire 经直接 brokerModel 发往 loopback；verifier 的普通/legacy8/4是合成快照。完整普通 Mu session 旧基线失败仍未证明通过，未重复无关失败，也未将上述有界证明冒充完整会话。实际冻结 worker 的投影与 hostile tool_calls 回归仍在独立176选择中执行；只证明一次 MODEL、无 coding tool 暴露/TOOL effects，不签发 B 终态闭合。

## 冻结与诊断

已逐项核对58条作者 command/raw 记录、10个r2文件、scope与manifest输入hash；整个 A 的15路径另用完整 Git diff 审查。作者名为 `r2-full-diff-from-4f.binary.patch` 的文件仅含10个r2路径，不能当全部15路径；本审查使用 full-A-diff.raw，不改冻结作者件。

作者9次原生失败、9项只读命令capture gap与1项recipe parser gap保持；原A22条formatter恢复、早期raw缺失和原patch被覆盖的限制保留，不补称历史日志已捕获。审查自身首次scope读取发生在runner创建前，原始输出只在tool记录；另有一次runner显示阶段UTF-8解码失败，子命令已成功捕获raw，后续以独立UTF-8记录纠正；两者在 diagnostic-audit.json 明示。

候选源码/tree/index保持；Main20项既有dirty和空index保持，允许Root3共享文件CAS变化并逐hash记录；冻结SDK bundle不变。没有写实际产品数据、配置、安装包或执行模型/Ollama/Core stop。formal增量0，全部22父任务保持开放。此前policy拒绝清理的旧目录没有重试。
'''
(r.E/'review.md').write_text(text,encoding='utf-8')
print(json.dumps({'verdict':report['verdict'],'counts':report['test_counts'],'guard':guard},ensure_ascii=False))
