import fs from 'node:fs';import path from 'node:path';import{fileURLToPath}from'node:url';import{createHash}from'node:crypto';import{spawnSync}from'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url)),source='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012',freeze=source+'/.local/v6-final-20261014-r3',prior='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v5-independent-review-20261013';
const sha=b=>createHash('sha256').update(b).digest('hex'),hash=p=>sha(fs.readFileSync(p)),read=p=>JSON.parse(fs.readFileSync(p,'utf8')),fresh=(n,x)=>fs.writeFileSync(dir+'/'+n,typeof x==='string'?x:JSON.stringify(x,null,2)+'\n',{flag:'wx'});
function verify(p,h){if(hash(p)!==h)throw Error('hash mismatch '+p);}
const received=read(dir+'/received-manifest.json'),audit=read(dir+'/freeze-audit-after.json');
verify(dir+'/received-manifest.json','9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9');
const old=read(prior+'/manifest.json');for(const f of old.files)verify(prior+'/'+f.path,f.sha256);
const commands=fs.readdirSync(dir).filter(n=>n.endsWith('.command.json')).sort().map(n=>{const c=read(dir+'/'+n);if(c.exit!==0||c.signal!==null||c.error)throw Error('run not passed '+n);verify(dir+'/'+c.name+'.stdout.txt',c.stdout_sha256);verify(dir+'/'+c.name+'.stderr.txt',c.stderr_sha256);return{record:n,...c};});
const inputs=read(dir+'/all-independent-inputs.json');
const candidateAgent=inputs.filter(f=>f.path.replaceAll('\\','/').includes('/mu-pause-checkpoint-m0-v2-20261012/packages/agent/src/'));
const candidateSession=inputs.filter(f=>f.path.replaceAll('\\','/').endsWith('/mu-pause-checkpoint-m0-v2-20261012/packages/coding-agent/src/core/agent-session.ts'));
const installedAgent=inputs.filter(f=>/qualification\/v2\.4\/mu\/packages\/agent\/(?:dist|src)\//.test(f.path.replaceAll('\\','/'))||/node_modules\/@earendil-works\/pi-agent-core\//.test(f.realpath.replaceAll('\\','/')));
if(!candidateAgent.some(f=>f.path.replaceAll('\\','/').endsWith('/agent.ts'))||candidateSession.length!==1||installedAgent.length)throw Error('wrong source provenance');
for(const f of inputs)verify(f.path,f.sha256);
for(const f of received.source9){verify(source+'/'+f.path,f.sha256);verify(dir+'/inputs/'+f.path.replaceAll('/','__'),f.sha256);}
const git=spawnSync('git',['diff','--name-only'],{cwd:source,encoding:'utf8'});if(git.status!==0)throw Error('git diff names failed');
const dirty=git.stdout.trim().split(/\r?\n/).filter(Boolean);const outside=dirty.filter(n=>!received.source9.some(f=>f.path===n));if(outside.length)throw Error('tracked source outside exact9: '+outside.join(','));
fresh('source-provenance-final.json',{at:new Date().toISOString(),source9:received.source9,candidate_agent_inputs:candidateAgent,candidate_session_inputs:candidateSession,installed_agent_inputs:installedAgent,independent_input_count:inputs.length,all_independent_inputs_rehashed:true,tracked_modified_paths:dirty,git_diff_names_exit:git.status,prior_v5_manifest_sha256:hash(prior+'/manifest.json'),prior_v5_artifacts_verified:old.files.length,prior_v5_unchanged:true});
const historical={
 original_custom:read(freeze+'/independent-agent-independent-session-negative-session.command.json'),
 monorepo_types:read(freeze+'/monorepo-tsgo-existing-dependency-limit.command.json'),
 biome:read(freeze+'/biome-final.command.json'),
};
for(const[key,c]of Object.entries(historical)){const r={key,path:freeze+'/'+c.name+'.command.json',sha256:hash(freeze+'/'+c.name+'.command.json'),...c};historical[key]=r;}
fresh('historical-limits-reference.json',{source:'Frozen V6 author evidence, hash-verified; not rerun in independent review',records:historical,original_custom_result:'7/10 PASS, 3 FAIL due to undeclared custom schemas; retained',monorepo_result:'exit 2; model catalog/type dependency errors; not full-workspace type acceptance'});
const report={
 schema:'researchos.mu-m0-v6-independent-differential-review/1',status:'FINAL',verdict:'SOURCE_FIXTURE_ACCEPTED',at:new Date().toISOString(),
 reviewer:{agent:'/root/mu_v5_review_resume',model:'gpt-6-astra',reasoning_effort:'high',model_metadata_source:'Root explicitly supplied current dispatch configuration',independent:true,source_writer:false},
 candidate:{source,freeze,manifest_sha256:hash(dir+'/received-manifest.json'),patch_sha256:received.patch_sha256,author_report_sha256:received.report_sha256,base_commit:received.base_commit,source9:received.source9,scope_sha256:received.scope_sha256},
 scope:'Finite differential M0 source/fixture review resolving V5-J/K/L and preserving M/N and checkpoint/queue/finished-effect controls. Not production acceptance.',
 integrity:{author_actual_inputs:audit.author_compiled_inputs,author_frozen_bundles:audit.author_bundles,author_frozen_files:audit.author_files,independent_actual_inputs:inputs.length,independent_fresh_bundles:fs.readdirSync(dir).filter(n=>n.endsWith('.metafile.json')).length,installed_agent_inputs:0,source_drift:[],prior_v5_artifacts_unchanged:old.files.length,terminal_command_records:commands.length},
 resolved_findings:[
  {id:'V5-J',status:'RESOLVED_IN_FROZEN_V6',source:[{path:'packages/agent/src/agent.ts',start:278,end:310}],proof:'Original reviewer three-role array-discriminant matrix rejects every case and retains no unknown payload. V6 validate/export/restore and stopReason/sampling tests pass.'},
  {id:'V5-K',status:'RESOLVED_IN_FROZEN_V6',source:[{path:'packages/agent/src/agent.ts',start:374,end:380},{path:'packages/agent/src/agent.ts',start:426,end:438}],proof:'Original unregistered/constructor/__proto__/toString matrix rejects every undeclared field; registered valid payload accepted. Own declaration/optional/required controls pass.'},
  {id:'V5-L',status:'RESOLVED_IN_FROZEN_V6',source:[{path:'packages/agent/src/agent.ts',start:1748,end:1791},{path:'packages/agent/src/agent-loop.ts',start:435,end:501}],proof:'Both old L controls match uninterrupted two-call sequences. prepareNextTurn/prepareRequest legitimate registered model/tool selections complete. N5 finishes with final response, two calls, no error, effects/results/custom context once, empty queues; same and fresh AgentSession variants pass.'},
 ],
 new_findings:[],
 security_evidence:{registration:'Constructor model signatures are captured separately from mutable model objects. Tool signatures and execute/prepareArguments/requestPause references are retained; resolution rejects drift.',source_refs:['packages/agent/src/agent.ts:932','packages/agent/src/agent.ts:1553','packages/agent/src/agent.ts:1596','packages/agent/src/agent.ts:1628'],phase:'Old binding checked before trusted preparation; commit validates old identities, resolves next registered identities and commits phase; following dispatches remain guarded.',dispatch_refs:['packages/agent/src/agent-loop.ts:674','packages/agent/src/agent-loop.ts:685','packages/agent/src/agent-loop.ts:692','packages/agent/src/agent-loop.ts:847','packages/agent/src/agent-loop.ts:921']},
 executions:[
  {id:'v6-regression-67',tests:67,pass:67,fail:0,exit:0,evidence:'v6-regression-67.stdout.txt',includes:'Fresh V6 source tests + unchanged reviewer V5 J/K/L/M/N, strengthened N5, registered compatibility and V4 controls'},
  {id:'v6-phase-boundary',tests:3,pass:3,fail:0,exit:0,evidence:'v6-phase-boundary.stdout.txt',cases:[{id:'V6-P',proof:'New model/tool phase checkpointed again, restored to third instance; calls=3 initial/next/next, next effect/result once, original user once, prepares=2 finishes=3, final assistant and no error'},{id:'V6-Q',proof:'prepareRequest attempts to re-sign current/next model, next tool metadata, or same-toString replacement execute are rejected: 4/4 before next provider and zero tool effects'},{id:'V6-R',proof:'After legitimate phase commit, async transform/convert/getApiKey mutation of next model blocked: 3/3, calls remains 1'}]},
  {id:'original-agent-40',tests:40,pass:40,fail:0,exit:0,evidence:'original-agent-40.stdout.txt'},
  {id:'worker-2',tests:2,pass:2,fail:0,exit:0,evidence:'worker-2.stdout.txt'},
  {id:'targeted-tsgo',exit:0,evidence:'targeted-tsgo.command.json'},
 ],
 commands,
 fixture_provenance:'fixture-provenance.json; old reviewer fixtures copied unchanged. New v6-phase-boundary authored independently within the changed lifecycle scope.',
 history:{v5_verdict:'REQUEST_CHANGES preserved',v5_raw_and_manifests:'all 157 prior manifest members verified unchanged',v6_old_unregistered_custom:'7/10, three schema failures retained in frozen author evidence; not erased or counted accepted',monorepo_tsgo:'Frozen author exit 2 remains; only targeted types independently passed',biome:'Author exact9 exit0 frozen evidence hash verified; no independent write/format action'},
 acceptance:{m0_source_fixture_accepted:true,production_m0_accepted:false,m1_m2_accepted:false,installed_sdk:false,phone_ready:false,live_provider_qualified:false,real_provider_calls:0,real_external_tool_effects:0,real_credentials:0,formal_increment:0,formal_cases_accepted:0,formal_cases_total:42,all_22_parents_open:true,parent_acceptance:false},
 next_action:'Root may record finite M0 source/fixture acceptance and plan separately authorized integration qualification. This does not install candidate or authorize production modifications.',
};
fresh('report.json',report);
fresh('report.md',`# Mu M0 V6 独立差异复核 — FINAL

结论：**SOURCE_FIXTURE_ACCEPTED（仅有限 M0 源码与合成夹具接受）**。V5-J/K/L 已在冻结 V6 中修复；旧 M/N 安全控制、旧 checkpoint 阶段、工具效果和队列消费回归仍通过。本轮没有新增阻断项。

冻结 manifest：\`${report.candidate.manifest_sha256}\`。精确 9 源、作者 2134 个实际编译输入、15 个冻结 bundles、101 个冻结文件均已核验。本轮独立从 V6 candidate 源新编译 13 个 bundles，追踪 2132 个实际输入（与作者差异来自复核 fixture 集合）；未使用 installed agent SDK 或旧 V5 bundle。前后源 hash 无漂移；V5 manifest 的 157 个成员全部保持原样。见 [source-provenance-final.json](source-provenance-final.json)、[freeze-audit-after.json](freeze-audit-after.json)。

## 已解决问题

| 原问题 | V6 变化与独立证据 |
|---|---|
| J / P1 类型标识强转绕过 | agent.ts:278 先要求 string，再检查 literal，switch default 拒绝；三类 message 的原数组反例全部拒绝。validate/export/restore、stopReason/sampling 控制通过。 |
| K / P1 继承字段绕过闭合 schema | agent.ts:377、429、434 使用 own-property 查询；constructor/__proto__/toString 及普通未知字段全部拒绝，合法登记字段仍通过。 |
| L / P2 旧绑定阻断合法后续阶段 | agent.ts:1748 的阶段 guard 保留旧身份；agent-loop.ts:435–501 在可信 prepareNextTurn/prepareRequest 后明确提交新绑定。原 L 两类恢复与无暂停序列一致，加强 N5 最终成功。 |

模型登记签名在构造时固定，工具登记同时固定签名及函数引用；提交新阶段先校验旧身份，再解析已登记的新身份。每次模型/工具 dispatch 仍检查。没有通过清空 guard、信任篡改后重算签名或开放整个工具 registry 换取通过。

## 实际验证

| 独立运行 | 结果 |
|---|---|
| 实际 V6 源 + 原 reviewer 回归 | 67/67 PASS，exit 0 |
| 新阶段边界 P/Q/R | 3/3 PASS，exit 0 |
| 原 Agent 回归 | 40/40 PASS，exit 0 |
| 合成 worker 协议 | 2/2 PASS，exit 0 |
| 定向 tsgo | exit 0 |

旧 V5-J/K/L/M/N 与 strengthened-N5 fixture 按原字节复制、新编译运行。M 的四种异步 mutation 仍拦截；N 只执行 allowed 工具、excluded 返回错误。N5 同实例和新实例恢复均到达最终 done 回复，调用数 2、无 error、两项效果及结果 ID 恰好一次、延迟 custom context 恰好一次、队列为空。

新增 P 验证合法下一阶段再次暂停并第三实例恢复：模型序列 initial/next/next，3 次调用、工具效果及结果各一次、原始 user 一次、prepares=2、finishes=3、最终回复完成。Q 在 prepareRequest 中尝试篡改当前/下一模型、下一工具元数据和同 toString 的替换函数，4/4 在下一 dispatch 前拒绝且无工具效果。R 在新阶段提交后通过 transform/convert/getApiKey 异步篡改新模型，3/3 拒绝且调用数维持 1。见 [v6-phase-boundary.stdout.txt](v6-phase-boundary.stdout.txt)。

## 保留限制

原未登记 custom fixture 的 7/10、三项失败仍保留于作者冻结包；没有改写为通过。全仓 tsgo 的 exit 2 和模型目录/依赖类型错误也保留，不能宣称全仓类型通过。exact9 Biome 为作者冻结 exit 0 证据，本轮只核验，不执行写入格式化。详见 [historical-limits-reference.json](historical-limits-reference.json)。

本轮依据 Root 明确提供的 dispatch 元数据记录 gpt-6-astra/high。结论仅覆盖本次 same9 M0 源码修复与合成夹具；没有安装 SDK、生产 M1/M2、真实 provider/外部工具调用或手机验收。正式增量 0，仍为 0/42，22 父任务全部 open。后续集成与真实资格验证须单独记录，不能把此结论晋升为产品正式接受。
`);
function inventory(prefix=''){return fs.readdirSync(dir+'/'+prefix,{withFileTypes:true}).flatMap(e=>{const n=path.posix.join(prefix,e.name);return e.isDirectory()?inventory(n):[{path:n,bytes:fs.statSync(dir+'/'+n).size,sha256:hash(dir+'/'+n)}];}).sort((a,b)=>a.path.localeCompare(b.path));}
fresh('manifest.json',{schema:'researchos.mu-m0-v6-independent-review-final-manifest/1',status:'FINAL',verdict:report.verdict,at:new Date().toISOString(),candidate_manifest_sha256:report.candidate.manifest_sha256,report_sha256:hash(dir+'/report.json'),report_md_sha256:hash(dir+'/report.md'),files:inventory(),excludes:['manifest.json (self hash)'],formal_increment:0});
console.log(JSON.stringify({status:'FINAL',verdict:report.verdict,report_sha256:hash(dir+'/report.json'),manifest_sha256:hash(dir+'/manifest.json'),members:read(dir+'/manifest.json').files.length}));
