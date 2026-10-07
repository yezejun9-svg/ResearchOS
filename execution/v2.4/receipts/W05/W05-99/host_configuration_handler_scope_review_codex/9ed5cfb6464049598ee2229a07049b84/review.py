import pathlib,json,hashlib,datetime,sys
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');OUT=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def write(n,x):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
before=json.loads((OUT/'input.before.json').read_bytes());entries=before['entries']
extra=[]
for path in ['internal/domain/client_protocol_goal.go','internal/domain/runtime_goal_bindings_windows.go','internal/domain/client_workspace_write_windows.go']:
 p=ROOT/path;b=p.read_bytes();s=write('snapshots/main/'+path,b)
 extra.append({'group':'main','path':path,'original':str(p),'sha256':sha(b),'bytes':len(b),'snapshot_ref':s})
write('input.supplement.before.json',{'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':extra,'resolution':'Actual names discovered with rg --files/rg; initial nonexistent client_protocol_goals.go retained in initial missing_inputs. Source file was not fabricated or restored.'})
entries+=extra;idx={(x['group'],x['path']):x for x in entries}
def ev(path,lines=None,group='main',pointer=None):
 e=idx[group,path];r=dict(e['snapshot_ref'])
 if lines:
  n=len((ROOT/r['path']).read_text(encoding='utf8').splitlines());a,z=lines
  assert 1<=a<=n;r['locator']={'lines':[a,min(z,n)]}
 else:r['locator']={'json_pointer':pointer or ''}
 return r
P='execution/v2.4/receipts/W05/W05-99/host_configuration_handler_scope_readonly_codex/7e34df584e1b45a1b68f06ce62fcdb95/scope_proposal.json'
proposal=json.loads((ROOT/idx['main',P]['snapshot_ref']['path']).read_bytes())
def pr(pointer):return ev(P,pointer=pointer)
docs='22_CLIENT_INTERFACE_DETAILS.md';schema='internal/api/contracts/client.protocol.schema.json'
protocol=json.loads((ROOT/idx['main',schema]['snapshot_ref']['path']).read_bytes())
extract={k:protocol['$defs'][k] for k in ['ConfigurePayload','ConfigureResult','ModelConfiguration','CreateSessionPayload','HostStatusResult','CredentialSummary','SessionSnapshot','CommandEnvelope','CommandResponse']}
write('frozen.contract.definitions.json',extract)
comparisons=[]
for source,frozen,expected in [('internal/api/contracts/client.protocol.schema.json','contracts/client.protocol.schema.json','8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b'),('internal/api/contracts/domain.schema.json','contracts/domain.schema.json','b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54')]:
 a=idx['main',source];b=idx['frozen',frozen]
 comparisons.append({'source_ref':a['snapshot_ref'],'frozen_ref':b['snapshot_ref'],'expected_sha256':expected,'exact_equal':a['sha256']==b['sha256']==expected})
assert all(x['exact_equal'] for x in comparisons)
write('schema.byte-comparison.json',comparisons)
findings=[]
def add(id,state,title,facts,decision,refs):findings.append({'id':id,'status':state,'title':title,'actual_facts':facts,'required_scope_or_interface_decision':decision,'evidence_refs':refs,'tests_executed_here':0})
add('G01','READY_WITH_PRECISE_BOUNDARIES','默认与 Session configure 的解码和事务分支可在既有路径完成',
 ['当前 DecodeEnvelope 的 MODEL_CHANGE_WITHOUT_EPOCH 阻止全null默认configure；writeMethods未包含host.configure且无handler。','冻结文档要求不适用字段显式null；session为空时仅默认配置，session非空必须project/revision/epoch齐备。'],
 ['明确接受A全null(scope四字段)和B全非null(session/project/positive revision/epoch)两形状；拒绝missing key、空串、混合scope。默认分支在generic Session gate之前，但仍验证当前OWNER、trusted localHost与完整typed payload。','可在client_protocol.go保存严格原始Envelope字节/规范化完整请求；不能先json.Unmarshal去掉重复key或未知字节后再声称验证了原始输入。','成功session配置同时head+1/session revision+1，writer_epoch和event_watermark保持；default不改变任何Session/Run。无CONFIG_CHANGED枚举，不造新事件。'],
 [ev('internal/domain/client_protocol.go',[44,164]),ev('internal/domain/client_protocol.go',[814,904]),ev(docs,[92,122],'frozen'),pr('/transaction_order')])
add('G02','READY_WITH_FOUNDATION_AMENDMENT','两个 foundation helper 的窄修改合法，但必须保留原默认 helper 契约',
 ['stageClientConfiguration 和 readClientConfiguration 拒绝session scope、identity join固定project空；read会逐历史行被backup调用。','ConfigureResult仅ModelConfiguration，没有SessionSnapshot；Session响应顶层SessionID/revision必须由原scope而非当前head证明。'],
 ['新增私有scoped staging入口可复用同一SQL；原stageClientConfiguration default-only入口继续拒绝session。修改readClientConfiguration按确切scope恢复原Envelope、实际project identity及原typed结果。','session历史响应需session_id等于scope.session_id、revision==expected_revision+1、原client/writer epoch绑定；default响应scope/revision采用明确null约定，config_revision只来自result，不把host revision混为Session revision。','历史读验证每个原配置与原响应，不要求当前Session model等于旧ref，不因归档、之后改配置或当前凭据撤销而破坏备份。全三表历史/原journal不变。'],
 [ev('internal/domain/client_configuration.go',[93,269]),ev('internal/domain/backup_host_configuration.go',[132,253]),ev(schema,pointer='/$defs/ConfigureResult')])
add('G03','READY_WITH_PERSISTED_CREATION_CHECK','session.create 的 derived SessionID 例外必须仅限原创建成功',
 ['真实createClientSession返回新sid作为顶层和result.session_id；request.session_id为null。','项目级goal.start故意顶层null、真实新sid在result.snapshot；session scoped goal.start保留原sid。','当前decodeClientIdentityResponse一律等于request.SessionID，因此新创建响应需方法特例。'],
 ['仅 session.create + COMPLETED + request.SessionID null 接受derived非空sid，要求result.sid==response.sid、result.project==request.project、原session行以及唯一原创建journal归属principal一致。其余状态/方法继续原一致性。','解码器本身没有tx：在lookupClientCommandIdentity已有caller Tx内加持久创建核验，或私有分层函数；不能把任意非空result.sid当持久证明。新响应在原journal INSERT之后作同样postcondition核验。','goal.start项目级保持顶层null；创建身份核验用原result.snapshot，不补写假session.create journal，不因后续Session revision变化破坏原replay。'],
 [ev('internal/domain/client_command_identity.go',[99,194]),ev('internal/domain/client_protocol_sessions.go',[62,115]),ev('internal/domain/client_protocol_sessions.go',[156,204]),ev('internal/domain/client_protocol_goal.go',[350,382])])
add('G04','READY_WITH_REPLAY_ORDER_CONDITIONS','新 raw principal 与旧 prefixed principal 原样回放可保留备份守卫',
 ['host.status目前输出principal:+principal；backup只对已有global identity的host.status要求result.authenticated_principal_ref等于raw principal。','lookup扫描principal+command整个v2 namespace，reserve helper会给旧回放补identity，H1必须在调用reserve前分支返回旧回执。'],
 ['真实身份认证先行；global lookup先于任何业务变更/Session CAS。旧存在且唯一、request完整hash匹配的原响应原样返回，不能调用reserve自动回填；不同project/method/client/payload/null区别的相同command冲突。','新命令reserve与原journal同caller Tx；建议reserve在business savepoint之外，REJECTED回滚业务后仍保存该合法rejected response+identity；schema/commit错误回滚全部。不得留orphan identity。','ACK session.control在global lookup命中后仍进入原有受保护finalization路径；不能简单return绕开它，也不修F081811。','新host.status raw principal是合同string合法形式；旧prefixed不重写、不自动链接。按此选择无需修改backup_host_configuration.go，真实新status/session多方法全量backup是必需控制。'],
 [ev('internal/domain/client_protocol.go',[703,808]),ev('internal/domain/client_protocol.go',[931,962]),ev('internal/domain/client_command_identity.go',[129,217]),ev('internal/domain/backup_host_configuration.go',[190,253]),ev(docs,[113,122],'frozen')])
add('G05','REVISION_REQUIRED','离线可见性与执行准入要分开，不能靠缺 row 判 legacy',
 ['createBoundClientSession目前调用checkClientBinding，后者要求SessionRuntime非nil；无coordinator的启动handler无法创建离线Session。','CreateSessionPayload.model_config_ref与SessionSnapshot.model_config_ref都必须非空string；null不是请求使用default的语义。','sessionModel只接project/ref，没有SessionID或principal；同时供AdmitTurn、sessionTaskRoute和任务输入冻结/写权限使用。'],
 ['新configuration authority应独立于SessionRuntime；离线create仍需真实Workspace binding、当前Host/OWNER和typed config可见性，不能绕过目录撤销检查。NORMAL/goal实际执行保持currentRuntimeAdmission和原effect gates。','新session.create必须显式已存ref；禁止null/空串/缺失时latest/default fallback。用户选default由host.status返回的head配置明确ref完成。','提交可重算provenance规则：新创建global identity+原creation response的ref、后续成功session-scoped configure的原请求/响应链证明typed绑定。legacy只依据真实旧creation/运行profile身份；缺typed row、mc-字符串前缀或任意现行head都不是legacy授权。','旧Session改绑后不得把创建时legacy永久当豁免；当前session.model_config_ref必须和原创建或最后合法scoped配置链相符。损坏/歧义拒绝。历史read/backup不等于当前可执行。','sessionModel shared签名可保持，在已有路径中按trusted port owner/principal+ref验证；如果设计需每Session参数，必须列出所有外部调用者再扩scope，不能漏client_workspace_write_windows.go。'],
 [ev('internal/domain/client_protocol_sessions.go',[129,204]),ev('internal/domain/runtime_sessions_windows.go',[11,94]),ev('internal/domain/client_workspace_write_windows.go',[9,67]),ev(schema,pointer='/$defs/CreateSessionPayload'),ev(schema,pointer='/$defs/SessionSnapshot'),pr('/runtime_binding/legacy')])
add('G06','INTERFACE_DECISION_REQUIRED','保存策略、credential null 和 endpoint 映射必须先明确',
 ['foundation仅HTTPS、无userinfo/query/fragment并有限label；schema URI更宽，现有严格测试覆盖拒绝http等。','payload credential_ref允许null；新保存不能要求一个已qualified runtime route存在，否则首次配置永远不能进入资格流程。','现有LIVE MODEL broker要求非空CredentialRef==CredentialRevision，profile endpoint是完整dispatch URL，存储base_url不是相同概念。'],
 ['保存沿用已审HTTPS严格策略；不放宽旧测试。对null须选定可解释策略：保存为未验证/缺凭据的配置，或在明确provider要求凭据时返回CREDENTIAL_MISSING；不能声称现有LIVE已支持无凭据provider。metadata AVAILABLE不代表解密或网络可用。','非null凭据只查同localHost bound principal、record.Ref/Provider/Kind/Revoked；不能调用CredentialUsable、vault.open或ModelCredential。返回仅allowlisted metadata，不导出Wrapped/MaterialDigest。','endpoint建议固定一个已评审openai-completions策略：base_url的明确规范形式+固定/chat/completions suffix；保存原值且将转换用于严格比较。明列末尾斜杠、已有suffix、大小写、百分号/双斜杠/路径dot段处理，默认拒绝歧义，不尝试多个URL。这个规则是需Root批准的实现策略，不是冻结合同已有的具体suffix。','实际intake至少唯一绑定configRef、provider/model、完整endpoint、CredentialRef=CredentialRevision、routeID、project/runtime/purpose/capability、profile/model_config hash和admission版本。保存不改profile/ref，不自动qualify；新同内容配置依然新ref需新资格。'],
 [ev('internal/domain/client_configuration.go',[48,74]),ev('internal/host/vault.go',[36,174]),ev('internal/host/model_credential.go',[12,29]),ev('internal/domain/runtime_broker_windows.go',[43,108]),ev('internal/domain/runtime_model.go',[51,90]),pr('/runtime_binding/endpoint_open_decision')])
add('G07','DESIGN_ALLOWED_WITH_EXACT_SELECTION','head + newest99 符合100形状上限，但不是完整历史列表',
 ['HostStatusResult model_configurations/credentials maxItems100；文档没有要求该数组枚举全部历史，也没有配置分页/nextcursor字段。','SessionSnapshot仅携带ref而非完整配置正文；旧ref可用于原Session/内部typed查找，但不能宣称存在未实现的完整历史配置API。'],
 ['精确current owner_host_ref+principal：先head一次，再排除head按config_revision DESC、ref稳定次序最多99；head为空则revision0+[]，不借其他owner/head。必须全行通过typed history读验证，重复ref拒绝或去重后仍正确limit。','credentials按被列config的非nullref去重，每项Ref/Provider/Status/last_checked_at来自metadata实际检查；最多100，绝不扫描其它Host私有目录。','测试0/1/99/100/101/200+配置：head必在、顺序可复现、原三表行数不裁、旧Sessionref仍能typed解析/回放/backup，选旧合法ref不会被分页丢失判NOT_FOUND。','此数组仅有界视图，不能把未列项视为被删除或未配置；不新增冻结schema字段。'],
 [ev(schema,pointer='/$defs/HostStatusResult'),ev(schema,pointer='/$defs/CredentialSummary'),ev(docs,[68,92],'frozen'),pr('/known_gaps_and_required_decisions/6')])
add('G08','SCOPE_REVISION_REQUIRED','14范围没有覆盖真实新默认创建分支及一条过时测试断言',
 ['runtime_goal_bindings_windows.go:ResolveGoalBinding 为项目级goal.start创建新Session，直接遍历唯一旧route选model，不读host default。若新default未qualified，继续旧route会违背新会话default和不降级语义。','client_configuration_test.go:608–613 明确断言默认public configure Decode失败，H1成功解码与其必然冲突。此为静态必然冲突，未运行新产品失败。'],
 ['建议追加第15路径internal/domain/runtime_goal_bindings_windows.go，仅ResolveGoalBinding模型选择：存在真实head时固定其ref，按已有admission gates验证，未qualified拒绝而不是旧route fallback；无head时只有明确保留的既有legacy行为，不能把损坏head当无head。Workspace唯一性和oldRun/profile不变。若Root明确排除此功能，需明示project-level goal.start默认语义未完成，不能称H1完整。','建议追加第16路径internal/domain/client_configuration_test.go，仅末尾“public envelope仍未接线”阶段性断言改为合法null scope解码及缺trusted authority实际拒绝；同函数strict payload/default-only private stage拒绝session以及其余旧测试全保留。','14path的其它原production边界原则够用；backup_host_configuration.go暂无需扩、v2.go/SQL/SDK/旧broker/host vault实现不改。若改变sessionModel参数则先按G05列调用点额外独审。'],
 [ev('internal/domain/runtime_goal_bindings_windows.go',[10,98]),ev('internal/domain/client_protocol_goal.go',[252,298]),ev('internal/domain/client_configuration_test.go',[572,614]),ev(docs,[92,109],'frozen'),pr('/exact_proposed_source_scope')])
add('H01','REQUIRED_PRECISE_AUTHORITY_PORT','trusted Host身份必须由真实对象注入而非字符串',
 ['Host.InstanceID为host私有目录路径+OS identity.Ref摘要；boundPrincipal来自该Host状态。vault.record读取记录含ciphertext但不调用unprotect。','newV2Service有PID fallback；传入HostInstance字符串不能证明metadata authority。apps/control有无runtime和有coordinator两条composition。'],
 ['common domain定义metadata-only接口，真实Host实现验证WINDOWS_SID/本机identity、boundPrincipal==authenticated principal、数据库当前OWNER未撤销。默认与coordinator handler都注入同一Host；未bootstrap/nilport/PID-only拒绝持久配置。','不得在caller Tx内通过h.db开第二transaction进行身份查询，Go单conn会阻塞；DB授权由同caller Tx执行，port只用现成Host身份与Vault metadata。','client_id用于完整请求/Session writer和Workspace绑定，不凭客户端自报值产生owner授权。既有native bootstrap目前返回client_id但没有在此提案展示额外全局登记表；不得声称新增了未实现客户端身份注册。','同目录/同主体restart InstanceID稳定；新目录不采用旧owner配置，恢复旧历史refs可保留但不能自动取得当前可选配置或新Run权。'],
 [ev('internal/host/host.go',[85,172]),ev('internal/host/state.go',[10,50]),ev('internal/host/native.go',[172,198]),ev('internal/api/v2.go',[73,91]),ev('internal/api/server.go',[20,65]),ev('apps/control/main.go',[174,230])])
add('H02','REQUIRED_SETTLEMENT_MATRIX','Session 改配置不能只调用旧 clientTurnSettled 一个bool',
 ['clientTurnSettled校验queue/control与activeRun/effects/terminal projection，但noRun仅看Task状态；pending permissions来自原ResourceRequest，不可省略。','默认configure无Session不能阻塞或改写既有Run；session configure需当前writer lease与完整权威绑定。'],
 ['scoped handler明确核当前owner/grants、session creation attribution、workspace可见性、archived/sealed、expectedRevision/writerEpoch/writerClientID、lease未过期。','同Tx查实际Task/Run与原队列、control、resource effects、pending permission/handoff/resume reconciliation。active/paused/LOST、STARTED/UNKNOWN、pending noRun Task均busy；不接受caller settled字段。','只在完全settled时更新client_sessions.model_config_ref/revision/updated_at，保留task/run/history/profile/lease epoch/所有BudgetLedger与失败计数。错head或session CAS使两个修改均回滚。'],
 [ev('internal/domain/client_protocol_sessions.go',[389,440]),ev('internal/domain/client_protocol.go',[868,899]),ev(docs,[159,187],'frozen'),pr('/mandatory_controls')])
cases=[]
def case(id,trigger,expected,gate):cases.append({'id':id,'input_or_synchronization':trigger,'required_actual_outcome':expected,'gates':gate,'executed_here':False})
for c in [
 ('C01','default所有scope显式null，head0->1->2','typed COMPLETED verified_at null；3表+唯一journal；zero provider/worker/decrypt；Session/Run不变',['G01','G02']),
 ('C02','default混合scope/缺nullkey/空串/duplicate key或invalidUnicode','严格拒绝；不进入head/stage',['G01']),
 ('C03','同完整command重试但currenthead/epoch已变化','精确原结果；不reserve legacy，不新增config/revision',['G04']),
 ('C04','同principal+command跨method/project/client/payload、null-vs-value','COMMAND_ID_CONFLICT，零业务变更；多旧locator拒绝不任选',['G04']),
 ('C05','新Rejected command，fault在reserve/stage/head/session/typedresponse/commit边界','合法rejection仅原response+identity；真正error全Tx rollback，无orphan',['G02','G04']),
 ('C06','两个client同时相同head+sessionrevision CAS','恰一成功；失败不保留任何config/head/session副作用',['G01','H02']),
 ('C07','session scope成功，之后再改绑定多次','head+1/sessionrev+1；epoch、水位、旧Runprofile不变；每次旧配置history可验',['G02','H02']),
 ('C08','expired/foreignwriter/staleepoch/revision/archived/sealed/foreignprincipal','准确typed拒绝，无配置 mutation',['H01','H02']),
 ('C09','Task pending无Run/paused/LOST/active/UNKNOWN effect/pendingqueue/cancel/permission','SESSION_BUSY或原准确拒绝；不给settled标签放行',['H02']),
 ('C10','session.create显式可见但未qualified配置且无coordinator','离线Session durable create；model_config_ref固定，zero Run/dispatch',['G05']),
 ('C11','session.create缺/null/空ref','拒绝，不用head或latest填充',['G05']),
 ('C12','新creation response derivedsid以及exact replay','唯一真实创建归属+project+result/顶层sid一致；恢复后旧response仍可验',['G03']),
 ('C13','forged/foreign/missing persistedsid或其它method响应sid改变','拒绝；goal.start项目级顶层null保持',['G03']),
 ('C14','旧legacy Session与新typed Session删除/缺失typed row','只有真实legacy provenance分支保留；新typed失败绝不fallback',['G05']),
 ('C15','原legacy Session后合法scoped configure后重启','用最新合法binding事件链且不读当前hosthead代替；不保持永久legacy豁免',['G05']),
 ('C16','新head未qualified但旧唯一runtime仍qualified，project goal.start','固定新headref并拒绝unavailable，zero旧route执行',['G08']),
 ('C17','first NORMAL精确ref但provider/model/endpoint/credentialRev/profileHash/route重复或不符','effect PREPARED和HTTP前拒绝，原预算/Run历史不变',['G06','G08']),
 ('C18','真实匹配已独立qualifiedprofile；及现有legacy admitted session','保留currentRuntimeAdmission和原SDK/tool/budget守卫；不自动新资格',['G05','G06']),
 ('C19','credential missing/revoked/wrongprovider/kind/ref/foreignhost','metadata-only准确拒绝；不decrypt、不输出wrapped/digest/secret',['G06','H01']),
 ('C20','nullcredential/no route首次保存','按预先批准的null策略存未验证或准确缺凭据拒绝；不得要求先qualified',['G06']),
 ('C21','save后revocation与dispatch竞态','save不承诺跨Vault原子usable；原ModelCredential dispatch再验失败',['G06']),
 ('C22','baseURL slash/suffix/encoded/dot/query/userinfo与实际endpoint','只固定规则唯一映射；歧义拒绝，无联网尝试',['G06']),
 ('C23','status 0/1/99/100/101/200+配置、多shared credential','head+newest99 dedup；credential≤100；config head真实，历史不裁',['G07']),
 ('C24','旧不在status视图的合法ref被已有Session/新显式create引用','可按授权typed读取；无截断引起NOT_FOUND；历史API未实现不假称存在',['G07']),
 ('C25','new rawprincipal status与旧prefixed status exact replay','新globalidentity backup通过；旧不改字节/不自动backfill',['G04']),
 ('C26','default/scopedconfig+create/goalstatus/rejected各种globalidentity fullbackup/restore/rebackup','所有原响应+typed表保持，历史validators不过度比较currentSessionref',['G02','G03','G04']),
 ('C27','配置scope/hash/response/identity/session attribution被改或orphan','backup拒绝，不能放宽validator',['G02','G03']),
 ('C28','同host restart、新host dir、PID-only Handler、未bootstrapHost','同host稳定；新host不采用旧default；不可信port禁止configure',['H01']),
 ('C29','取消原ACK replay命中新增globallookup','原受保护路径仍可达；F08 immutable1811仍作为独立open，不吞掉、不绕过',['G04']),
 ('C30','全current相关 domain/API/Host/runtime/CLI回归','实际源向量/closedDB/raw/非零断言与fail/skip完整；旧unknown不重试',['G08'])]:case(*c)
review={'schema':'researchos.host-config-handler.independent-design-review.v1','status':'DESIGN_SCOPE_REVISION_REQUIRED','reviewer_id':'codex:/root/sources_parent_impl','author_reviewed':'codex:/root/command_queue_impl','model':'gpt-6-astra','reasoning_effort':'high','independence':{'independent_for':'Cmd new handler14 design and interface/scope proposal','not_certifying':'Reviewer-authored prior configuration11 and foundation facts are baseline inputs only; no self source acceptance, no Main composition acceptance.'},'proposal_ref':ev(P),'actual_main_head':(OUT/'head.stdout').read_text().strip(),'input_refs':[ref(OUT/'input.before.json'),ref(OUT/'input.supplement.before.json')],'frozen_schema_comparison_ref':ref(OUT/'schema.byte-comparison.json'),'findings':findings,'case_matrix':cases,
 'scope_recommendation':{'original14':[x['path'] for x in proposal['exact_proposed_source_scope']],'required_additional_test':['internal/domain/client_configuration_test.go: only obsolete public-unwired stage assertion at608-613; preserve all strict input/default-helper rejection assertions'],'recommended_additional_production':['internal/domain/runtime_goal_bindings_windows.go: only ResolveGoalBinding model-selection branch to enforce explicit currenthead for new project-level Goal Session'], 'recommended_count_for_complete_new_default_semantics':16,'not_automatically_authorized':True,'no_extra_backup_validator_required_if':['new host.status rawprincipal','legacy exactreplay never backfills identity','client_configuration read validates session history against originalscope','new session.create derived identity verifier uses original creation receipt/actualproject'],'conditional_scope_gate':'Changing shared sessionModel signature or requiring new external client/provenance registry needs exact additional callsite proposal before editing; no blanket authorization.'},
 'decisions_before_registration':['Fix G05 typed-versus-legacy provenance and no missing-row fallback','Fix G06 single deterministic endpoint policy and null-credential save policy; no fake no-key LIVE support','Approve G07 exact bounded status view without deleting historical rows','Approve G08 one narrow legacy-stage test and decide new default applies to project-level goal.start by adding exact resolver path','Record foundation2 method-specific changes and serialization of Execute with future F08'],
 'ordering':['Non-author Main composition review remains external prerequisite; this review does not sign it.','Root freezes final schema23/source vector and exclusively leases handler paths; configuration handler transaction/globalidentity first.','Independent handler source review and actual local realHost/API/backup controls; then Root merge/current regression.','F08 shared client_protocol.go starts only after handler finalfreeze+lease transfer, rebase and independent scope/source review.','CLI/Desktop producer changes and actual provider qualification are separate later scopes; saving configuration/fixture success is not usable provider or A04 acceptance.'],
 'actual_activity':{'product_tests':0,'HTTP':0,'worker':0,'MODEL':0,'private_DB_or_vault':0,'holdout':0,'source_changes':0,'SQL_changes':0,'F08_changes':0,'canonical_changes':0,'formal_increment':0},
 'failure_origins':{'new_product_failures':0,'tool_diagnostics':['capture missing guessed client_protocol_goals.go was recorded; corrected rg-discovered client_protocol_goal.go, no file fabricated','tool da8654 final rg no-match exit1; source reads successful; not a product failure'],'historical_failures':'No reset/retry or acceptance inherited; old F08 1811/unknown/provider failures remain outside scope.'}}
write('design_review.json',review)
after=[]
for e in entries:
 b=pathlib.Path(e['original']).read_bytes();after.append({'group':e['group'],'path':e['path'],'sha256':sha(b),'same_as_before':sha(b)==e['sha256']})
drift=[e for e in after if not e['same_as_before']]
write('input.after.json',{'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':after,'drift':drift,'drift_count':len(drift)})
assert not drift
write('handoff.json',{'schema':'researchos.readonly-design.handoff.v1','status':review['status'],'review_ref':ref(OUT/'design_review.json'),'input_count':len(entries),'input_drift':0,'input_after_ref':ref(OUT/'input.after.json'),'recommended_scope':16,'original_scope':14,'all_G01_G08_and_H01_H02_have_actual_source_refs':True,'source_ready':False,'product_acceptance':False,'tests_executed':0,'independence':review['independence']})
write('review.invocation.json',{'actualargv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(pathlib.Path.cwd()),'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operations':'public captured source+schema inspection, hashing, and exclusive receipt writes','product_execution':False})
# Validate exact refs and bounded line locations before sealing the new manifest.
checked=0
def walk(x):
 global checked
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x:
   p=ROOT/x['path'];assert p.is_file() and sha(p.read_bytes())==x['sha256'];checked+=1
   if 'lines' in x.get('locator',{}):
    a,z=x['locator']['lines'];assert 1<=a<=z<=len(p.read_text(encoding='utf8').splitlines())
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(review);walk(json.loads((OUT/'handoff.json').read_bytes()))
write('ref.audit.json',{'status':'RECEIPT_REFS_VALID_ONLY','checked_refs':checked,'hash_errors':0,'locator_errors':0,'product_acceptance':False})
manifest=write('manifest.json',{'schema':'researchos.receipt-manifest.v1','files':[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()],'excludes_self':True})
print(json.dumps({'review_ref':ref(OUT/'design_review.json'),'handoff_ref':ref(OUT/'handoff.json'),'manifest_ref':manifest,'input_count':len(entries),'drift':0,'ref_checks':checked},ensure_ascii=False))
