import pathlib,json,hashlib,subprocess,datetime,re,collections
OUT=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(__file__).resolve().parents[7]
WT=ROOT/'.local/worktrees/codex-w0599-host-configuration-handler'
def h(b):return hashlib.sha256(b).hexdigest()
def put(name,obj):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':h(b),'bytes':len(b)}
def git(args,name):
 argv=['git',*args];r=subprocess.run(argv,cwd=WT,capture_output=True)
 (OUT/(name+'.stdout.raw')).write_bytes(r.stdout);(OUT/(name+'.stderr.raw')).write_bytes(r.stderr)
 put(name+'.invocation.json',{'argv':argv,'cwd':str(WT),'exit_code':r.returncode,'readonly':True})
 if r.returncode:raise RuntimeError(name)
 return r.stdout
head=git(['rev-parse','HEAD'],'head').decode().strip()
changed=git(['diff','--name-only','--','apps/cli','apps/control','internal/api','internal/domain','tests/runtime/cli_contract'],'changed').decode().splitlines()
untracked=git(['ls-files','--others','--exclude-standard','apps/cli','apps/control','internal/api','internal/domain'],'new').decode().splitlines()
paths=sorted(set([p for p in changed+untracked if p.endswith('.go')]))
extra=['internal/canonical/jcs.go','internal/domain/contracts.go','internal/domain/client_protocol_schema.go','internal/domain/client_configuration.go','internal/domain/client_command_identity.go','apps/cli/cli_stream.go','apps/cli/cli_verbs.go','apps/cli/cli_doctor.go','internal/api/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.domain.schema.json','go.mod','go.sum']
snap=[]
for rel in sorted(set(paths+extra)):
 p=WT/rel;b=p.read_bytes();q=OUT/'public_inputs'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 snap.append({'source':str(p),'relative':rel,'snapshot':str(q.relative_to(OUT)),'sha256':h(b),'bytes':len(b)})
for name in ['cli_product_scope_amendment.json','fixture_boundary_scope_amendment.json']:
 p=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-product-and-closed-contract-r296'/name
 b=p.read_bytes();(OUT/name).write_bytes(b)
 snap.append({'source':str(p),'snapshot':name,'sha256':h(b),'bytes':len(b)})
git(['diff','--',*paths],'wip-source-diff')
old=git(['show','HEAD:tests/runtime/cli_contract/v2verbs.go'],'legacy-original-v2verbs')
new=(WT/'tests/runtime/cli_contract/v2verbs.go').read_bytes()
ids=lambda b:collections.Counter(re.findall(rb'\bok\(\s*"([^"]+)"',b))
a,b=ids(old),ids(new)
put('old_checks_static_inventory.json',{'old_count':sum(a.values()),'current_count':sum(b.values()),'old_ids':{k.decode():v for k,v in a.items()},'current_ids':{k.decode():v for k,v in b.items()},'removed':{k.decode():v for k,v in (a-b).items()},'added':{k.decode():v for k,v in (b-a).items()},'limitation':'Static ok-call IDs only. Predicates assessed in saved diff; this is not execution or formalcase acceptance.'})
def ev(rel,lines):
 e=next(x for x in snap if x.get('relative')==rel);return {'path':e['source'],'snapshot':e['snapshot'],'sha256':e['sha256'],'lines':lines}
findings=[
 {'id':'H38-CLI-PRE-01','priority':'P1','status':'STATIC_SOURCE_DEFECT_NEEDS_FIX','title':'原响应数字先经IEEE754规范化，原schema整数校验不再可靠',
 'evidence':[ev('apps/cli/cli_contract.go','710-725,615-644'),ev('internal/canonical/jcs.go','8-23'),ev('apps/cli/cli_stream.go','241-244'),ev('internal/domain/client_protocol_schema.go','188-214'),ev('internal/api/contracts/client.protocol.schema.json','ConfigurePayload/ModelConfiguration/HostStatusResult/CommandResponse revision')],
 'cause':'canonical.JSON(raw) 调用 RFC8785 Canonicalize，随后 json.Unmarshal(any) 使用float64。JSON schema看到的是已舍入结果，UseNumber在SchemaDoc内重编码后才做不能恢复原数字。',
 'specific_counterexample_to_execute_later':'其余完全合法COMPLETED，status.result.config_revision raw=0.00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001（或configure result.config_revision=1.0000000000000001 / scoped revision=8.0000000000000001）应为非整数拒绝，而JCS float64会舍入/下溢。优先用1.0000000000000001的短确定反例，不需执行超长输入。',
 'minimal_fix':'只已授权cli_contract.go私有边界：strict原raw解析（递归decoded-key重复、UTF8/surrogate、单个完整JSON），用json.Number保留原数字，原值完整schema验证，再做精确整数/范围/有界+1比较。可调用既有Num以big.Rat检查；不得复用会先舍入的canonical结果或改generic v2Call/cliInteger/L01/L02。',
 'required_controls':['host.status和configure各自fraction-near-integer拒绝且原local bytes不变','正确合法整数含允许数学整数形式、safe boundary精确通过','浮点溢出、int64溢出、相邻不同整数不可碰撞','原重复escaped-key/nested/UTF8/schema/method/identity负例全保留'],
 'execution':'NOT_RUN; based on actual conversion source and IEEE754 semantics, not claimed observed product run'},
 {'id':'H38-CLI-PRE-02','priority':'P1','status':'STATIC_SOURCE_BOUNDARY_MISMATCH','title':'Session CAS上界被误当配置head上界，合法next revision被拒绝',
 'evidence':[ev('apps/cli/cli_contract.go','546,569,615-644,661-672'),ev('apps/cli/cli_v2.go','181-195'),ev('internal/domain/client_protocol_configuration.go','414-420,549'),ev('internal/domain/client_configuration.go','23,143')],
 'cause':'当前Host scope允许expected_revision=9007199254740991（仅>max拒绝），SQL UPDATE产生next Session revision=9007199254740992；该next值在int64中完全可表达。CLI以scope.revision>=max在网络前拒绝，且共享cliInteger拒绝>=2^53。配置head current+1不得超过foundation max与Session CAS并非同一限制。',
 'minimal_fix':'在已授权私有configure路径分开处理配置head上限和Session revision/epoch范围；原请求数字必须保持exact，合法Host输入max和返回max+1可校验和落盘，真正int64+1 overflow明确拒绝。不要为CLI自绿化收窄Host/冻结schema或改foundation上限。',
 'required_controls':['配置head current=max-1可发送next=max，current=max拒绝其+1','scoped expected=max与合法next=max+1精确落盘；下一次超过Host当前允许输入上限应明确拒绝','epoch=max保持原值，无response epoch伪证明','请求/响应相邻整数、分数和overflow区分'],
 'execution':'NOT_RUN; concrete cross-function boundary comparison, no fabricated high-revision DB'}
]
put('findings.json',findings)
notes=[
 'cli_v2 diff只host.configure分支，generic其他method/transport未改。default四null与scoped四nonnull显式区分，NoEpoch在status前拒绝。',
 '8s timeout / 1MiB+1 boundedread / no redirect / non2xx先分类；401/4033、5xx1，错误body不回显。静态成立，需最终实际raw证明。',
 'COMPLETED+完整schema/identity/result字段echo+verified_at null才writeConfig；ACK/IN_PROGRESS不写。当前测试ACK/IN_PROGRESS仅改status保留ConfigureResult，未证明是冻结合法ACK fixture，应补合法ACK包以验证该实际门。',
 'default修改cfg.Model为未来Session opaque ref但保留现有SID/project/revision/epoch；现有Session真实绑定由Host数据库掌握。实际Windows测试检查旧Session model_ref不变。不能把local Model称现有Session当前模型。',
 'cfg.Model消费仅新session.create传model_config_ref；不拼provider/model ref。scoped通过才更新对应SID/revision并保留已发送epoch；响应没有epoch，不伪称返回证明。',
 '旧fixture在model阶段才设configurePhase/revision；host.status先成功，再configure-busy返回合法SESSION_BUSY，原拒绝谓词补method和reason。非配置global WRITER_BUSY3没有在本diff改为1。',
 '旧49 IDs应看实际static inventory计数；本预审不复述作者绿色或把原拒绝替换成status失败。fixture的model_id由label改bare后缀、local Model改实际opaque输出属于既定规范纠正。',
 '目前仅WIP；whole38最终审查仍需foundation/current32/backup/header/runtime/API/CLI/TLS语义及编译向量冻结。无额外授权，更无SOURCE_READY。'
]
put('static_assessment.json',notes)
selectors={
 'CLI':['TestCLIModelConfigurationNativeMatrix','TestCLIModelConfigurationActualWindowsHost'],
 'transaction_identity_header':['TestClientTypedRejectionRollsBackBusinessWrites','TestHandlerOriginalHeaderExactBytesAndCorruption','TestHandlerStrictScopesAndRaw','TestHandlerGlobalIdentityCASAndFirstRaw','TestHandlerGlobalOriginalConflictFields','TestHandlerSQLFaultsRollbackOuterTransaction','TestHandlerScopedCASFaultRollsBackAllBusiness','TestHandlerConcurrentDefaultCAS','TestHandlerConcurrentScopedCAS'],
 'binding_settlement_legacy':['TestHandlerPendingProducerTransaction','TestHandlerScopedConfigurationRetainsOriginalTaskSettlement','TestHandlerOfflineTypedSessionAndScopedRebind','TestHandlerUnanchoredLegacyReadAndExplicitRebind','TestHandlerCreateNeverSuppliesImplicitModel','TestHandlerScopedFencesAndNoHistoricalRebind','TestHandlerHistoricalReferenceAndRepeatedRebind','TestHandlerStatusBoundedCompleteHistory','TestHandlerStatusCredentialDedupAndLegacyReplay','TestHandlerEndpointLexicalMapping'],
 'runtime_actual':['TestHandlerRuntimeStoredProfileExactMapping','TestHandlerRuntimeTaskNeedsExactSession','TestHandlerPendingOriginalTranscript','TestHandlerTLSActualSDKConfiguredSession','TestHandlerOriginalTaskProofAfterQueuedInput','TestHandlerPreSDKCancelledQueueCanRebind'],
 'public_backup':['TestBackupHostConfigurationPublicRoundTrip','TestHandlerRejectedSessionPublicBackupReplay','TestHandlerRejectedOriginalProofBackupTampering','TestHandlerNewIdentityRequiresOriginalHeader','TestBackupHostConfigurationCompleteHistoryRefusals','TestBackupHostConfigurationSchemaRefusals'],
 'public_API':['TestConfigurationActualWindowsHostOfflineHTTP','TestW14SessionHTTPCreateSendEventsAndReplay','TestW14SessionHTTPAuthorityAndFrozenRequest','TestW14SessionWriterLeaseHandoff']}
alltests={}
for x in snap:
 if x.get('relative','').endswith('_test.go'):
  for name in re.findall(r'^func (Test\w+)\(t \*testing\.T\)',(OUT/x['snapshot']).read_text(encoding='utf-8'),re.M):alltests[name]=x['relative']
put('final_review_preparation.json',{'status':'PLAN_ONLY_NOT_AUTHORIZED_TO_RUN','selectors':selectors,'current_test_locators':{n:alltests.get(n) for group in selectors.values() for n in group},'requires_final_source_freeze':True,'additional_requirements':['全38精确Git scope和未改生产/SQL/SDK边界；foundation既有独审链必须真实复用而非作者自签','真实全CLI/API+common跨平台编译，原assert/control逐项保留，不能Skip缺runtime输入','当前Go实际编译图allplatform/test/embeds+原SDK树/锁/Node/Go/Git/SQL/schema镜像/testbinary/实际bundle beforeafter闭合','独立实际ValidateBinding同Tx probe先1外层0、journal/identity1，replay调用仍1；不能公共provenance先拒绝空证明','public rejected unknown/crossproject SID完整原request/base64/headerhash/fullschema roundtrip+corruption；原legacyemptyheader严格规则','真实Host offline可配置，不等于qualified execution；TLS正常CA验证/actual SDK语义链与0paid注明','CANCEL_FENCE/noRun合法settled与Run/effect/queue UNKNOWN不得被新configure绕过；原ACK-final F08仍OPEN','旧合同原49谓词真实重放保留所有失败，不把fullCLI替代旧formal contract','本预审2新数值反例须实际先红后修，原raw不可改；最终非作者重放须另获Root授权']})
after=[]
for e in snap:
 p=pathlib.Path(e['source']);cur=h(p.read_bytes());after.append({'source':str(p),'before':e['sha256'],'after':cur,'equal':cur==e['sha256']})
put('input_audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'worktree':str(WT),'head':head,'author_finalfreeze':False,'changed_source_paths_count':len(paths),'changed_source_paths':paths,'snapshots':snap,'after':after,'drift_count':sum(not e['equal'] for e in after),'note':'WIP current snapshots only; unchanged authorized paths may not appear in diff inventory.'})
put('failure_origins.json',{'tooling':[{'origin':'tool-7f01c3','outer_exit':1,'exact_bad_argument':'internal/domain/client_protocol*.go','native_message':'os error123 Windows literal wildcard path invalid','invocation':'readonly rg last command; preceding source reads succeeded','original_raw_locator':'functions.exec tool result chunk7f01c3 in this reviewer turn','raw_limit':'not saved as native file at invocation time; do not invent standalone original raw','product_failure':False}],'non_failure_diagnostics':[{'chunk':'f28c9b','outer_exit':1,'cause':'last expected search had no matches; not source/product failure'}],'test_or_product_failures':[]})
put('review.json',{'decision':'PRELIMINARY_NEEDS_FIX_NOT_SOURCE_READY','reviewer':'/root/w05_merge_review','scope':'Handler38 WIP CLI5 plus final whole38 review preparation','findings':findings,'assessment':notes,'input_audit':ref(OUT/'input_audit.json'),'old_assertions':ref(OUT/'old_checks_static_inventory.json'),'future_review':ref(OUT/'final_review_preparation.json'),'executed':{'tests':0,'SQL':0,'HTTP':0,'Node':0,'model':0,'paid':0},'source_or_canonical_mutations':0,'source_acceptance_increment':0})
files=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
put('manifest.json',{'listed_count':len(files),'files':files,'excludes':['manifest.json','handoff.json']})
put('handoff.json',{'decision':'PRELIMINARY_NEEDS_FIX_NOT_SOURCE_READY','review':ref(OUT/'review.json'),'manifest':ref(OUT/'manifest.json'),'namespace':str(OUT),'author_WIP':True,'models_tests_SQL_HTTP_Node':0})
print(json.dumps({'review':ref(OUT/'review.json'),'manifest':ref(OUT/'manifest.json'),'handoff':ref(OUT/'handoff.json'),'snapshots':len(snap),'drift_count':sum(not e['equal'] for e in after),'old_ids':sum(a.values()),'current_ids':sum(b.values())},ensure_ascii=True))
