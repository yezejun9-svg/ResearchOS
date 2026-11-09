import hashlib, json, pathlib, shutil, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parents[7]
OUT = pathlib.Path(__file__).resolve().parent
REL = 'execution/v2.4/receipts/W05/W05-99/cancel_finalization_closed_contract_revision_codex/e38a370a015346dfad46530b0fdd44f1'
SRC = ROOT / REL
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_bytes().decode('utf-8-sig'))
def write(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def ref(p):
    b=p.read_bytes(); return {'path':str(p), 'sha256':sha(b),'bytes':len(b)}
def copy(p, dest):
    b=p.read_bytes(); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(b)
    return {'source':str(p),'snapshot':str(dest.relative_to(OUT)), 'sha256':sha(b),'bytes':len(b)}

manifest=readj(SRC/'manifest.json')
assert sha((SRC/'manifest.json').read_bytes())=='a61ae5dc340f2f85f4e2b7cd9e95b99870e86bf32467cd7bb2437f41163c1d8e'
assert sha((SRC/'scope_proposal.json').read_bytes())=='a798158a34f413b135d1960a98233ddf5454bd92b80bc45357577803c43eb758'
verified=[]
for e in manifest['files']:
    p=SRC/e['path']; assert p.resolve().is_relative_to(SRC.resolve())
    b=p.read_bytes(); assert sha(b)==e['sha256'] and len(b)==e['bytes'],e['path']
    verified.append(copy(p,OUT/'copied_candidate'/e['path']))
verified.append(copy(SRC/'manifest.json',OUT/'copied_candidate/manifest.json'))
assert len(verified)==112
proposal=readj(SRC/'scope_proposal.json')
assert len(proposal['scope'])==20
extra=['AGENTS.md','go.mod','go.sum','internal/domain/store.go','internal/store/sqlite.go',
       'internal/domain/orchestration.go','internal/domain/durability.go','internal/domain/resources.go',
       'internal/domain/runtime_dispatch.go','internal/domain/runtime_qualification.go',
       'internal/api/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.schema.json',
       'internal/domain/contracts/client.protocol.domain.schema.json',
       '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/driver.go',
       '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/sqlite.go',
       '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/conn.go']
inputs=[]; missing=[]
for rel in sorted(set([e['path'] for e in proposal['scope']]+extra)):
    p=ROOT/rel
    if p.exists(): inputs.append(copy(p,OUT/'current_sources'/rel))
    else: missing.append({'path':rel,'meaning':'proposed new source, not implemented or authorized by this review'})
for p in sorted((ROOT/'migrations/sqlite').glob('*.sql')):
    if not any(x['source']==str(p) for x in inputs): inputs.append(copy(p,OUT/'current_sources'/p.relative_to(ROOT)))

def evidence(rel, start=None, end=None):
    p=ROOT/rel; q=ref(p); q.update({'line_start':start,'line_end':end}); return q
def candidate(name,start=None,end=None):
    q=ref(SRC/name);q.update({'line_start':start,'line_end':end});return q

findings=[
 {'id':'F08-V4-SCOPE-01','severity':'P1_DESIGN_BLOCKER','status':'REQUEST_CHANGES',
  'title':'合法重复引用与重复拒绝规则互相冲突',
  'evidence':[candidate('source-contract.md',19,25),candidate('closed-contract.md',111,113),evidence('internal/domain/store.go',242,300),evidence('migrations/sqlite/0002_domain.sql')],
  'actual_static_fact':'refs 对 relation 数组逐成员在同一 field 插入；domain_refs 无唯一约束。schema 合法重复成员可以产生相同引用行。source-contract:19 与 closed-contract 通用 missing-or-duplicate 拒绝措辞会拒绝这种 producer 输出，而 source-contract:25 要求完整 multiset。',
  'required_change':'明确仅有真实 PK 的 category 拒绝重复 PK；domain_refs 按实际版本 body 独立重建完整多重集，合法重复保留乘数，缺失/额外/乘数不符才拒绝。同步改所有 closed/source contract 含糊 duplicate-source 句，不能改 producer/schema 去重。',
  'minimal_scope':'可在现20内处理：private evaluator、SQL source multiset transport、既有新 proof/backup tests；无需 store.go 生产修改。',
  'future_controls':['合法重复关系数组完整 proof/backup 通过','删除一份、增加一份或换 target revision/hash 必须拒绝','其他有 PK 的类别重复键仍拒绝'],
  'execution':'NOT_RUN; source-derived design contradiction, not an executed product failure'},
 {'id':'F08-V4-SCOPE-02','severity':'P1_DESIGN_BLOCKER','status':'REQUEST_CHANGES',
  'title':'新24 Run 后续 epoch 的 dispatch origin 未与真实恢复 producer 闭合',
  'evidence':[candidate('closed-contract.md',81,85),candidate('source-contract.md',51,53),candidate('candidate.sql.txt'),evidence('internal/domain/orchestration.go',414,463),evidence('internal/domain/durability.go',360,399),evidence('internal/domain/resources.go',308,355),evidence('internal/domain/runtime_dispatch.go',96,113)],
  'actual_static_fact':'origin AFTER INSERT 对所有不在 old23 cohort 的 Run 生效，而不仅首次 epoch。真实 checkpoint/resource switch 保留 Run ID，重建 lease/epoch（switch 还改 runtime），prepareRuntimeDispatch 位于该次 RUN_CHANGED 之前。现合同要求 revision1 birth、exact current claim Task、original claim runtime/lease，却只给 old23 cohort 明确的 later-epoch 例外；没有说明 post24 later-epoch 如何把 birth 与当前 dispatch authority 分别核验。',
  'required_change':'为 post24 同 Run 后续 epoch 单列确定性规则：永久 birth/claim provenance 与本次 pre-dispatch Run/version/lease/runtime/admission/route-or-checkpoint 来源分开绑定；不得要求尚未发生的本次 event、不得把原 claim lease/runtime当本次值、不得因 origin 不匹配退回 legacy 或 latest profile。明确每个 dispatch 是否生成 epoch-specific origin，或只首次生成但给 subsequent dispatch 另一完整原事实校验；任何方案不得让旧 STARTED/UNKNOWN 通过新 epoch 消失而成为从未执行。',
  'minimal_scope':'优先在现20 的 SQL origin trigger/private proof evaluator/新 tests 中闭合，因为完整历史已在 sources。若所需当前 checkpoint/route 事实不能由既有32 categories独立重算，应明确增补源类别或精确 producer path 后再审；当前不能假定20已足够。禁止先改 durability.go/resources.go/runtime_dispatch.go。',
  'future_controls':['新24首次 native claim与qualification真实通过','同 post24 Run 的合法 checkpoint_resume / resource_switch 新epoch实际通过，birth保持原值且本次binding精确','old23 Run 新epoch允许但 origin始终无资格','缺/伪 birth、旧lease或runtime替代当前、跳epoch、未清旧UNKNOWN均拒绝','取消与新epoch调度竞争不得借旧命令取消后来的Run/重放已完成历史'],
  'execution':'NOT_RUN; unspecified contract branch with concrete producer-order evidence; not a proven SQL runtime failure'}
]
write('findings.json',findings)

assessments=[
 ('atomic_admitted_group','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','单root INSERT+AFTER成员/pins同statement物化；root和child不可替换；admitted deferred FK 精确绑定原 sole journal 五列与 global identity。FK只是存在性，原bytes/全schema/原hash另由真实 source tuple及 pure validator重算。'),
 ('atomic_final_group','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','final root与final_commit双deferred FK；commit只在journal completed后生成且BEFORE校验实际journal/control/materialization。组独立插入不能以ACK或空journal提交；不能把 reciprocal FK本身称byte proof。'),
 ('sole_journal','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','initial ACK/immediate completion/ACK->COMPLETED三个mode绑定actual OLD/NEW bytes、first header与Q/R/J各算法；固定列+typeof不变，UPDATE仅RowsAffected1；其他method/reverse/no-op原1811保持。'),
 ('legacy_and_native_origin','REQUEST_CHANGES','old23全Run cohort从objects/versions/dispatch union固定且不可回填，旧Run新epoch仅不生成origin是合理方向；post24后续epoch规则见F08-V4-SCOPE-02。'),
 ('cancel_before_launch','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','真正PREPARED未启动才可私有callerTx terminal producer；STARTED即使emptyPID也不具资格，保留clear/abort/idle/cleanup真实路径。新helper不伪造SDK/observations，不释放预算，不重派UNKNOWN。'),
 ('pure_udf_physical_connections','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','pinned modernc default Driver.Open逐physical connection注册其udfs；domain init先于任何Open且注册冲突panic。自建Driver不继承，为负例。三pureUDF不得DB/FS/时钟/Host/environment/network/cached flag。这是静态源码事实，未运行连接测试。'),
 ('pragma_guards','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','每个proof/journal/dispatch写要求foreign_keys=1；BEFORE INSERT collision避免recursive_triggers=0的REPLACE隐式delete洞。trusted_schema=0预期拒绝含unsafe UDF的写，不能称callback已执行；既有读边界另测。'),
 ('raw_bytes_and_schema','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','真实SQLite TEXT非volatile回调用GoString可截NUL，因此BLOB+源body hex严格解码有必要；所有duplicate/UTF8/surrogate检查在map前。原Q与JCS及rawR分离；使用固定原协议/schema镜像，最终handler source必须再绑定。'),
 ('response_limits','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','仅保持既有original Envelope/private-header限制；不得增加response/identity/witness/member1MiB或64KiB政策。合法>1MiB完整SessionSnapshot future control保持NOT_RUN。'),
 ('collision_and_replay_callers','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','path20 ensureClientQueue 在 caller Tx先查原row并保留generation/allstate，缺失才ID+普通INSERT；observeRuntime读取同key完整原body并保留observed_at，重复skip；原UPDATE-before-observation/auth/identity保留。domain_objects等其他合法UPSERT不改。'),
 ('immutable_inventory','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','实际candidate SQL覆盖9新tables、2views、root/member/pin/commit/legacy/origin/obligation与旧受保护PK/alternate UNIQUE collision；正式schema fingerprint只能来自未来实际SQL24，TEXT SHA不是schema hash。'),
 ('references','REQUEST_CHANGES','全版本与raw pin思路可用，但合法duplicate multiset矛盾必须消除；见F08-V4-SCOPE-01。'),
 ('public_upgrade_restore','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','需真实匹配old23 source build/程序哈希，source lock覆盖snapshot/migrate/recovery/validate/rename/report/final；public24 backup/restore/rebackup验证原history及允许restore deltas；WAL可读不代替oldwriter排他证据；原SQL1..23、旧22/23和13/14/20守卫不放宽。'),
 ('fresh_install_and_platform','DESIGN_SUPPORTED_PENDING_IMPLEMENTATION','Service.New先numbered后next_v24 additive在sameTx；未来fresh24必须实际验证引用client_sessions等view/trigger在additive之前的DDL/seed顺序。defaultdriver注册放已列common新文件，Windows-specific coordination只现Windows path；不能用skip替代。'),
 ('scope_dependencies','NOT_READY_TO_LEASE','20是候选范围，不是生产接受；handler现38仍未freeze，client_protocol/global identity/privateheaders和finalsnapshot需最终source重新绑定。两阻断修订后Root串行lease；未授权SQL24实现。')
]
write('closed_contract_assessment.json',[{'area':a,'status':b,'conclusion':c} for a,b,c in assessments])
write('exact_full_scope.json',{'count':20,'scope':proposal['scope'],'whole_scope_verdict':'REQUEST_CHANGES','no_extra_path_authorized':True,'protected':['SQL1..23','frozen schemas','API','CLI','SDK','all old receipts','canonical state'],'required_changes':['F08-V4-SCOPE-01','F08-V4-SCOPE-02']})
write('future_gates.json',{'all_not_run':True,'gates':proposal['future_gates'],'added_required_controls':findings[0]['future_controls']+findings[1]['future_controls'],'counts':{'SQL':0,'tests':0,'Node':0,'HTTP':0,'model':0,'paid':0,'private_or_holdout':0}})

diagnostics=[{'id':'readonly-location-6d8e57','actual_tool_chunk':'6d8e57','outer_exit':0,'native_exit':'not captured separately','message':'rg included nonexistent internal/domain/tasks.go; stderr os error2; subsequent commands made outer exit0','raw_retention':'original tool response remains in thread; no new invented raw log','product_failure':False},
 {'id':'readonly-location-17491b','actual_tool_chunk':'17491b','outer_exit':0,'native_exit':'not captured separately','message':'rg --files spec/v2.4 nonexistent; stderr os error2; later Get-Content returned outer0','raw_retention':'original tool response remains in thread (output truncated); no fabricated full output','product_failure':False},
 {'id':'readonly-output-24aa94','actual_tool_chunk':'24aa94','outer_exit':0,'message':'overbroad filename search and ConvertTo-Json output truncated; bounded later reads used for evidence','product_failure':False}]
write('tooling_diagnostics.json',diagnostics)
write('failure_origins.json',{'actual_failed_product_invocations':[],'static_request_changes_not_invocations':['F08-V4-SCOPE-01','F08-V4-SCOPE-02'],'tooling_diagnostics_ref':'tooling_diagnostics.json','do_not_invent_outer_exit1':True})
head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
stable=[]
for e in inputs:
    current=sha(pathlib.Path(e['source']).read_bytes());stable.append({'source':e['source'],'before':e['sha256'],'after':current,'equal':current==e['sha256']})
write('actual_read_audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(ROOT),'head':head,'candidate_manifest_verified':ref(SRC/'manifest.json'),'candidate_files':verified,'current_public_inputs':inputs,'new_paths_absent':missing,'after':stable,'drift_count':sum(not x['equal'] for x in stable),'scope_count':20,'SQL_EXECUTED':False,'tests_executed':False})
review={'schema':'researchos.independent-scope-review.v1','reviewer':'/root/w05_merge_review','independent_of_implementation':True,'decision':'REQUEST_CHANGES','scope':'F08 v4 entire20 design and closed contract; no source acceptance or SQL24 lease','candidate_proposal':ref(SRC/'scope_proposal.json'),'candidate_sql_text':ref(SRC/'candidate.sql.txt'),'main_head_observed':head,'findings':findings,'scope_ref':ref(OUT/'exact_full_scope.json'),'assessment_ref':ref(OUT/'closed_contract_assessment.json'),'read_audit_ref':ref(OUT/'actual_read_audit.json'),'counts':{'candidate_manifest_entries':111,'candidate_files_including_manifest':112,'proposed_paths':20,'product_tests':0,'SQL':0,'formal_acceptance_increment':0},'conditions':['修订两个完整合同矛盾后再确认范围，不需先执行产品来掩盖未定分支。','原12future gates仍NOT_RUN；没有可运行实现，不把文档检查当SQL/UDF或迁移PASS。','handler最终freeze及Root串行授权为开工前提；本receipt不写canonical、不修改原证据。'],'limitations':['仅静态合同与producer源码推理；两finding都不是已运行产品反例。','空Task Goal当前producer本身拒绝；本轮不另行宣称修复或引入该行为。','全数据库source bundle可能昂贵，future测试测量资源；不得以截断/新cap优化。','工具定位错误原outer0及未捕获nativeexit如实列tooling_diagnostics。']}
write('source_review.json',review)
files=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
write('manifest.json',{'schema':'researchos.public-receipt-manifest.v1','root':str(OUT),'listed_count':len(files),'excluded':['manifest.json','handoff.json'],'files':files})
write('handoff.json',{'decision':'REQUEST_CHANGES','review':ref(OUT/'source_review.json'),'manifest':ref(OUT/'manifest.json'),'findings':['F08-V4-SCOPE-01','F08-V4-SCOPE-02'],'candidate_proposal':ref(SRC/'scope_proposal.json'),'namespace':str(OUT),'mutations':'own public review receipts only','no_source_or_formal_acceptance':True})
print(json.dumps({'review':ref(OUT/'source_review.json'),'manifest':ref(OUT/'manifest.json'),'handoff':ref(OUT/'handoff.json'),'listed_count':len(files),'current_inputs':len(inputs),'drift_count':sum(not x['equal'] for x in stable)},ensure_ascii=True))
