import collections, datetime, hashlib, json, os, platform, sys
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/owned-core-stop-anchor-r2-20261015'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ref(p):
    p=Path(p); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,obj): (E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lineage=read(E/'input-lineage.json')
classified=read(E/'classified-author-nonzero.json')
cases=sorted(E.glob('fixture-e2e-*/case-result.json'))
assert len(cases)==3
positive=read(cases[0]); negexit=read(E/'negative-native_exit_code-result.json'); negwait=read(E/'negative-native_wait_result-result.json')
assert positive['result']['state']=='STOPPED_LEASE_VERIFIED' and positive['result']['postflight']['rows']==35
assert negexit['unsafe_acceptance_reproduced'] and negwait['unsafe_acceptance_reproduced']
findings=[
 {'id':'STOP-R2-F01','priority':'P1','title':'缺失 native wait/exit 数值字段被当成零并授权 native stop','evidence_level':'fresh real two-compiled-grant CLI reproduction on two separate new synthetic fixtures','locations':[{'path':'internal/ownedcorestop/proof_windows.go','line':158},{'path':'internal/ownedcorestop/proof_windows.go','line':160},{'path':'internal/ownedcorestop/proof_windows.go','line':286}],
  'impact':'worker_native_exit/verifier_native_exit 的 native_exit_code 或 native_wait_result 缺失时 Go uint32 默认为0；NativeExitCode根本未作存在性校验，NativeWaitResult的!=0也无法拒绝缺失。两组独立真实CLI均进入STOPPED_LEASE_VERIFIED并调用一次TerminateProcess，违反原始严格native Wait/数值exit证明要求。这里只证明新synthetic fixture校验缺口，不证明原产品历史worker/verifier已关闭。',
  'evidence':[ref(E/'negative-native_exit_code-result.json'),ref(E/'negative-native_wait_result-result.json')],
  'minimal_fix':'使用presence-aware uint32表示或显式required字段解码；worker/verifier两类均要求字段存在且非null。native_wait_result必须明确等于WAIT_OBJECT_0；native_exit_code允许明确的0或非零合法uint32，不能把缺失当0。保持原proof classes及完整原生capture要求。',
  'source_paths':['internal/ownedcorestop/proof_windows.go','internal/ownedcorestop/proof_windows_test.go'],
  'required_tests':['worker与verifier分别测试missing/null/native_exit_code=0/native_exit_code=非零合法uint32','native_wait_result missing/null/非零拒绝，明确0才满足此字段','负数/越界/小数拒绝；字段存在于另一proof类不能替代本类字段','真实双grantCLI重跑本次两个畸形fixture，必须在STOP_ATTEMPT/TERMINATE_INTENT/native action前拒绝；正常非空正例仍成功']},
 {'id':'STOP-R2-F02','priority':'P1','title':'最终 native signal 边界丢失调用者取消和更早的 context deadline','evidence_level':'source control-flow proof; no dynamic cancellation injection performed in this review',
  'locations':[{'path':'internal/ownedcorestop/stop_windows.go','line':193},{'path':'internal/ownedcorestop/stop_windows.go','line':285},{'path':'internal/ownedcorestop/stop_windows.go','line':294},{'path':'internal/ownedcorestop/stop_windows.go','line':297},{'path':'ops/supervisor/owned_core_handle_windows.go','line':337}],
  'impact':'Commit创建继承caller deadline/cancel的ctx供SQL使用，但在最后一次Host查询返回后只调用g.checkAction检查grant墙钟；传入native层的是最初grant截止时间，未取ctx更早截止时间，native方法也没有ctx。调用者在TERMINATE_INTENT flush或native pre-wait期间取消，或CLI45秒deadline先到而grant仍有效时，最终检查仍可进入TerminateProcess。已消费intent不应退款，但必须零signal。',
  'evidence':[ref(E/'read-state.raw.txt'),ref(E/'read-native-proof.raw.txt'),ref(E/'read-store-cli.raw.txt'),ref(E/'final-findings-locations.raw.txt')],
  'minimal_fix':'把有效invocation deadline取grant monotonic预算与caller ctx截止的较早者，最终intent前和原生call前都检查ctx取消及墙钟/monotonic时间；将context传入retained native边界，在pre-wait后紧接调用前检查。消费后的取消写出零signal/UNKNOWN并永久保留消费；一次signal后的有限完成流程仍不得retry。',
  'source_paths':['internal/ownedcorestop/stop_windows.go','internal/ownedcorestop/stop_windows_test.go','ops/supervisor/owned_core_handle_windows.go','ops/supervisor/owned_core_handle_windows_test.go'],
  'required_tests':['caller已取消、caller deadline早于grant、取消发生在intent flush后和native pre-wait后，各自零native call','持久intent后取消跨进程重入不能重试；grant expiry after intent同样零signal且consumed','已有单次terminate失败与wait deadline tests保留，不把seam结果称为真实OS耗时证明']},
 {'id':'STOP-R2-F03','priority':'P2','title':'Core/parent映像读取尚未实现要求的祖先句柄固定','evidence_level':'source contract gap; no live ancestor race exploit claimed',
  'locations':[{'path':'ops/supervisor/owned_core_handle_windows.go','line':62},{'path':'ops/supervisor/owned_core_handle_windows.go','line':72},{'path':'ops/supervisor/owned_core_handle_windows.go','line':79},{'path':'ops/supervisor/owned_core_handle_windows.go','line':138}],
  'impact':'ownedNativePath通过EvalSymlinks按名检查，然后ownedNativeImage另行按名打开最终文件；ownedNativeProcess只保留进程和最终image句柄，没有逐级祖先句柄、逐级non-reparse/owner/ACL验证与生命周期。最终image身份hash匹配能挡普通替换，不能替代SA-D04明确要求的检查到打开之间路径稳定性证明。现有heldDocuments祖先保护不覆盖任意Core/parent image路径。',
  'evidence':[ref(E/'read-native-proof.raw.txt'),ref(E/'read-tests-manifest.raw.txt')],
  'minimal_fix':'在现有supervisor文件内逐级打开并保留image祖先native句柄，拒绝reparse/不符合授权边界的owner/ACL；从同一最终句柄计算image hash/ID并在ownedNativeProcess.close逆序关闭祖先。不要用一次EvalSymlinks作为稳定性证明，也不要新增放宽的proof类。',
  'source_paths':['ops/supervisor/owned_core_handle_windows.go','ops/supervisor/owned_core_handle_windows_test.go'],
  'required_tests':['Core及parent image路径祖先在validate/open/action边界的swap/reparse变化被阻止或拒绝','最终image写共享冲突、hardlink alias、错误parent身份均零signal','祖先保护测试必须覆盖supervisor image路径，而非只复用authority文件的heldDocuments测试']}
]
coverage=[
 {'id':'COV-01','requirement':'SA-D02 SA06/SA07 S215','observed':'journal_windows_test.go手工写records后直接调用readExistingStopOutcome；作者真实CLI只覆盖正常完成replay/concurrent','gap':'不能声称已执行完整grant-aware进程在claim/BEGIN/intent/native call各崩溃点、torn/missing journal及第三grant替换后的永久消费测试','next_cut':'新隔离fixture true-CLI crash/replay/third-successor matrix；保留每点native计数/原始失败，不新增生产testflag'},
 {'id':'COV-02','requirement':'SA-D04 SA08/SA15 S202','observed':'wrong_native/parent/root/opdir CLI负例、authority-file write/operation-directory rename辅助测试','gap':'缺少parent image祖先TOCTOU实测、foreign SID/Host/Owner完整cuts；不得把wrong index等同于全部native边界','next_cut':'与F03修复对应的最小真实句柄cut；资源不足只阻塞此cut'},
 {'id':'COV-03','requirement':'SA-D05 SA05 S211','observed':'expired preflight与native helper已过期时间seam；expired inspect成功；barrier helper有等待commit','gap':'缺少intent flush到native call之间到期/取消及caller较早deadline全路径证据，F02源码也未闭合','next_cut':'按F02矩阵验证零signal与durable消费'},
 {'id':'COV-04','requirement':'SA09 S209','observed':'真实CLI s209仅插入PREPARED effect；STARTED/UNKNOWN及其他危险状态在store helper测试','gap':'CP508要求full S209 dangerstate经true CLI Commit尚未全部具备','next_cut':'在现有new-fixture harness中分别执行STARTED/UNKNOWN危险state真实CLI拒绝；不得只以helper coverage认定完成'},
 {'id':'COV-05','requirement':'SA01 SA-D03','observed':'strict parser单元测试与default/expired真实CLI；入口源码先纯解析/compiled grant检查','gap':'现有parser单元测试并不等于所有畸形compiled grant经CLI的零side-effect计数证据','next_cut':'按新增存在性缺口聚焦bad native receipt及malformed grant必要cut，记录未执行范围'},
]
nonzero_own=[]; incomplete=[]
for p in sorted((E/'command-captures').iterdir()):
    if not (p/'after.json').exists():
        # This script's enclosing logger finishes after the report is written.
        # Its open capture is not an historical missing-after failure.
        if 'write-final-review' not in p.name: incomplete.append(str(p))
        continue
    a=read(p/'after.json')
    if a['native_exit']!=0:
        err=(p/'stderr.bin').read_text(errors='replace')
        classification='EXPECTED_DENIAL' if 'STOP_GRANT_ACTION_DENIED' in err else 'REVIEW_TOOL_ABORTED' if 'correct-relative-base' in p.name else 'REVIEW_REQUIRED'
        nonzero_own.append({'capture':str(p),'native_exit':a['native_exit'],'classification':classification,'stderr':err})
diagnostic={'schema':'researchos.stop-r2.diagnostic-audit.v1','author_counts':classified['counts'],'author_total_nonzero':63,'author_expected_denial_or_blocked':54,'author_error_records':9,'three_harness_summaries_additional_failure_count':0,'author_capture_count':275,'author_case_refs':16,'author_zero_assertion_captures':lineage['zero_assertion_captures'],'author_explicit_skip_captures':lineage['explicit_skip_captures'],'zero_assertions_are_not_passes':True,'author_original_capture_gap':classified['historical_capture_gap'],'coverage_gaps':coverage,'own_nonzero':nonzero_own,'own_incomplete_captures':incomplete,'own_gaps_and_corrections':[
 '首次仅读取项目AGENTS.md与CP514卡的发现命令没有预写E recipe或独立raw文件；只保留聊天工具输出，未补造历史raw。',
 'bootstrap Get-Command go找不到PATH中的go；随后使用项目明确Go1.27.1绝对路径。该PowerShell非终止错误在bootstrap raw保留，最终native_exit不能替代每条cmdlet状态。',
 '早期PowerShell批量只读命令保留recipe/合并raw/末尾status，未逐条分离stdout/stderr/native exit，部分未逐次快照env；不足以冒充严格逐命令native capture。所有build和fresh CLI通过run_logged.py逐命令捕获。',
 '第一次审查引用递归工具把旧设计包的相对path按repo root解析，产生18条工具解析错误；保留input-lineage-first-relative-base-error.json与完整capture。不是作者缺失文件。',
 '第二次扩大到旧设计证据递归超出本次Source核对所需范围，主动Ctrl+C终止；tool session exit1，logger实际保留after native_exit1及RuntimeError stderr。早期draft误写为缺after，最终逐文件检查已更正，draft保留。',
 '最终修正为卡指定输入hash与冻结作者包有界递归：1204refs无错误，19Gitblob、275captures、16cases及两份patch核对一致。'],
 'fresh_checks':[{'kind':'positive','ref':ref(cases[0]),'state':positive['result']['state'],'tables':87,'rows':35,'terminate_calls':1},{'kind':'missing_native_exit_code','ref':ref(E/'negative-native_exit_code-result.json'),'unexpected_acceptance':True},{'kind':'missing_native_wait_result','ref':ref(E/'negative-native_wait_result-result.json'),'unexpected_acceptance':True}],
 'own_runtime':{'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'go':'go1.27.1 windows/amd64','temporary_root':str(R/'.local/owned-core-stop-r2-independent-review-20261015'),'harness_source_change':'only go_env temp/cache constants; separate profile driver edits newly generated synthetic receipt objects, no production validator mutation'},
 'new_implementation_failure_findings':3,'actual_target_actions':0,'formal_increment':0,'all_22_open':True}
write('diagnostic-audit.json',diagnostic)
review={'schema':'researchos.owned-core-stop-source-r2-independent-review.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/owned_core_stop_source_review','model_requested_by_card':'gpt-6-astra high','runtime_model_metadata':'not independently observable; reviewer does not fabricate runtime model attestation','candidate':lineage['head'][0],'tree':lineage['head'][1],'base':'4f4023c956f84d65743f39ce77d6c8899a21ada1','scope':'complete19 Source, including8 inherited paths; not only11 repair paths','verdict':'NEEDS_CHANGES','limited_source_accepted':False,'findings':findings,'coverage_gaps':coverage,'minimal_fix_source_paths':sorted(set(p for f in findings for p in f['source_paths'])),'optional_existing_test_path_for_durable_crash_matrix':'internal/ownedcorestop/journal_windows_test.go','lineage':ref(E/'input-lineage.json'),'diagnostic':ref(E/'diagnostic-audit.json'),'classified_author_nonzero':ref(E/'classified-author-nonzero.json'),'formal_increment':0,'formal_total':'0/42','all_22_parent_tasks':'OPEN','actual_authority':False,'main_acceptance':False,'package_acceptance':False,'product_data_process_probes':False,'proof_classes':'original strict seven unchanged; no substitute/relaxation introduced','source_write_authority_used':False}
write('review.json',review)
md='''# STOP-r2 全19 Source 独立审查\n\n**NEEDS_CHANGES。f5db4a9639f1a50380eb5929ee6295887baeb756 不接受为 LIMITED_SOURCE_ACCEPTED。**\n\n候选 tree `f6d44526df9f03abf1a5544cf4e7762be3d89208`；审查 Main `4f4023c9` 到候选的完整19文件（含8个继承路径），非只审11个修订文件。1204项引用文件、19个Git blob、275 captures、16个case refs均核对一致；全19及修订补丁逐字节匹配。\n\n独立重建的正常双grant CLI 正例成功：schema24、87表、35行非空SQLite，online backup、一次原始句柄native terminate/wait、real lease及相同postflight成立。随后两组新fixture各自删除 worker/verifier synthetic receipt 的 `native_exit_code` 或 `native_wait_result`，原harness重新计算hash并真实编译双grant，两组仍返回 `STOPPED_LEASE_VERIFIED`、`terminate_calls=1`。这是必须修复的证明字段存在性漏洞。没有触碰当前Core/Desktop/Ollama、原产品DB、旧Run或私钥；synthetic证明不代表实际历史native closure。\n\n'''
for f in findings:
    md+='## '+f['id']+' '+f['priority']+' '+f['title']+'\n\n'+f['impact']+'\n\n证据级别：'+f['evidence_level']+'。\n\n最小修复：'+f['minimal_fix']+'\n\n位置：'+', '.join(x['path']+':'+str(x['line']) for x in f['locations'])+'。\n\n必要复验：\n\n'+''.join('- '+x+'\n' for x in f['required_tests'])+'\n'
md+='''## 修复范围与未证明范围\n\n三项源码缺口最小文件集：\n\n'''+''.join('- `'+p+'`\n' for p in review['minimal_fix_source_paths'])+'\n永久消费崩溃矩阵如需补辅助测试，可在原允许路径 `internal/ownedcorestop/journal_windows_test.go` 内追加；真实CLI负例应在新隔离证据harness执行，不能修改冻结f5或注入生产validator批准。\n\n'
for c in coverage: md+='- '+c['id']+' '+c['requirement']+'：'+c['gap']+'。\n'
md+='''\n## 诊断与边界\n\n作者63条非零记录为54条预期拒绝/阻断与9条错误记录：1环境工具错误、2查询工具错误、1测试源码编译错误、2测试环境错误、2harness错误、1冻结工具错误。3条harness修正摘要仅链接原始记录，不追加失败数。6个capture含 `[no tests to run]`，仅表示编译/空选择，不计执行通过；未见显式SKIP文本。所有原始错误、作者初始capture gap均保留。\n\n本审查初始发现读取未预写recipe；早期PowerShell只读合并捕获缺逐命令状态/env；自身递归引用审计先发生相对路径解析错误，第二次过宽递归被主动取消，实际logger保留native_exit1与RuntimeError stderr，最终有界审计成功。早期draft把仍在运行的本报告writer误记为缺after、把被取消审计误述为无after，已核对更正，draft保留。这些缺口未补造或用重跑覆盖。build/fresh CLI 均有执行前argv/cwd/env及完整stdout/stderr/native exit。\n\nFormal仍0/42，全部22父任务OPEN；不授予Main、package或actual接受，不修改原始proof classes。\n'''
(E/'review.md').write_text(md,encoding='utf-8')
print(json.dumps({'verdict':review['verdict'],'findings':len(findings),'minimal_paths':review['minimal_fix_source_paths'],'own_incomplete_captures':incomplete,'hashes':{n:ref(E/n)['sha256'] for n in ('review.md','review.json','classified-author-nonzero.json','diagnostic-audit.json')}},ensure_ascii=False))
