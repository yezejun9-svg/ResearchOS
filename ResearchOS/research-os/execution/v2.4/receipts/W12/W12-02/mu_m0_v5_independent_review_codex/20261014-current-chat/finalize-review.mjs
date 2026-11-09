import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const dir = path.dirname(fileURLToPath(import.meta.url));
const source = 'C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012';
const freeze = source + '/.local/v5-final-20261013-r2';
const mirror = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W12/W12-02/mu_m0_v5_final_source_codex/20261012-current-chat';
const prior = 'C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v4-independent-review-20261012';
const expectedManifest = '41ac355e5a71b3092748c0c1061cb7cfd7c562b3cc158b89154f1a9f7e22c127';
const sha = b => createHash('sha256').update(b).digest('hex');
const hash = p => sha(fs.readFileSync(p));
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const fresh = (name, value) => fs.writeFileSync(path.join(dir, name), typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
function verify(p, expected) { const actual = hash(p); if(actual !== expected) throw Error('Hash mismatch: '+p); return actual; }
function inventory(root, relative='') {
  return fs.readdirSync(path.join(root,relative),{withFileTypes:true}).flatMap(e=>{
    const name = path.posix.join(relative,e.name);
    return e.isDirectory() ? inventory(root,name) : [{path:name,bytes:fs.statSync(path.join(root,name)).size,sha256:hash(path.join(root,name))}];
  }).sort((a,b)=>a.path.localeCompare(b.path));
}
const before = inventory(dir);
const manifest = read(dir+'/received-manifest.json');
for (const p of [dir+'/received-manifest.json',freeze+'/v5-final-manifest.json',mirror+'/v5-final-manifest.json']) verify(p,expectedManifest);
for (const item of manifest.source9) for(const p of [source+'/'+item.path,freeze+'/source/'+item.path,mirror+'/source/'+item.path,dir+'/inputs/'+item.path.replaceAll('/','__')]) verify(p,item.sha256);
verify(freeze+'/compiled-inputs-census.json',manifest.compiled_input_census_sha256);
verify(mirror+'/compiled-inputs-census.json',manifest.compiled_input_census_sha256);
const authorInputs = read(freeze+'/compiled-inputs-census.json');
for (const [p,item] of Object.entries(authorInputs)) verify(p,item.sha256);
for (const [name,item] of Object.entries(manifest.bundles)) {
  verify(freeze+'/bundles/'+name+'.mjs',item.bundle_sha256);
  verify(freeze+'/bundles/'+name+'.metafile.json',item.metafile_sha256);
}
for(const [name,expected] of Object.entries(manifest.harness)) for(const prefix of [freeze+'/harness/',mirror+'/harness/',dir+'/author-harness/']) verify(prefix+name,expected);
for(const [name,expected] of Object.entries(manifest.raw)) for(const prefix of [freeze+'/raw/',mirror+'/raw/',dir+'/author-raw/']) verify(prefix+name,expected);
const independentInputs = read(dir+'/all-compiled-inputs-final.json');
for(const item of independentInputs) verify(item.path,item.sha256);
const commands = fs.readdirSync(dir).filter(n=>n.endsWith('.command.json')).sort().map(n=>{
  const r = read(dir+'/'+n);
  if(!Number.isInteger(r.exit) || r.signal !== null || r.error) throw Error('Missing successful process termination record: '+n);
  verify(dir+'/'+r.name+'.stdout.txt',r.stdout_sha256);
  verify(dir+'/'+r.name+'.stderr.txt',r.stderr_sha256);
  return {record:n,...r};
});
for(const f of read(dir+'/fixture-provenance.json')) { verify(dir+'/'+f.destination,f.sha256); verify(f.original,f.sha256); }
const priorRaw = prior+'/candidate-41.stdout.txt';
const priorText = fs.readFileSync(priorRaw,'utf8');
const controlLines = priorText.split(/\r?\n/).map((text,i)=>({line:i+1,text})).filter(r=>r.text.includes('deferred-custom-resume'));
if(controlLines.length!==2 || controlLines.some(r=>!r.text.includes('"calls":2') || r.text.includes('"error"'))) throw Error('V4 N5 control changed');
fresh('v4-n5-control-reference.json',{path:priorRaw,sha256:hash(priorRaw),lines:controlLines});
fresh('resume-evidence-audit.json',{
  at:new Date().toISOString(),action:'Read existing terminal exits and hashes; no test/build rerun',
  received_manifest_sha256:expectedManifest,source9_verified:manifest.source9.length,
  author_compiled_input_count:Object.keys(authorInputs).length,author_bundles_verified:Object.keys(manifest.bundles).length,
  independent_compiled_input_count:independentInputs.length,command_records_verified:commands.length,
  source_and_mirror_match:true,compiled_input_drift:[],commands,
  historical_files_before_finalization:before,
});
const batch='v5-boundary-registered-independent-agent-registered-independent-session-registered-negative-session';
const findings=[
  {id:'V5-J',priority:'P1',title:'数组 discriminant 绕过内容联合类型及字段白名单',
   source:[{path:'packages/agent/src/agent.ts',start:278,end:307}],fixture:{path:'v5-boundary.test.ts',test:'V5-J content discriminants must be strings, with closed per-kind fields'},
   actual:'user、assistant、toolResult 的 content.type=["text"] 均被 restore 接收；unregisteredPayload 随后仍可 export。',
   cause:'String(content.type) 通过 kinds 检查，但 switch(content.type) 不匹配字符串分支且没有拒绝 default，完整字段验证被跳过。',
   reproduction:'复制合法 idle checkpoint；给三类 message.content 插入 {type:["text"],unregisteredPayload:{marker:"synthetic-private-data"}}；restorePauseState 后 exportPauseState。三个 rejected 均 false，unknownRetained 均 true。',
   required:'discriminant 先验证 string，再严格匹配 literal；default 拒绝；所有 typed content 路径复用校验。复查其他枚举的隐式转换，保留正常 text/image/thinking/toolCall 控制。',evidence:[batch+'.stdout.txt',batch+'.command.json']},
  {id:'V5-K',priority:'P1',title:'闭合 custom schema 把继承键当作已登记字段',
   source:[{path:'packages/agent/src/agent.ts',start:423,end:435},{path:'packages/agent/src/agent.ts',start:372,end:375}],fixture:{path:'v5-boundary.test.ts',test:'V5-K closed trusted custom schema rejects inherited Object.prototype names'},
   actual:'普通 unregistered 字段拒绝；constructor、__proto__、toString 三个未声明 own 字段接收，携带的合成 JSON 数据仍可重新导出。合法 custom 数据控制通过。',
   cause:'key in schema.properties 把 Object.prototype 继承名视作声明；后续仅遍历 schema 的 own entries，未校验这些 payload 字段。optional/必填查询也使用 in。',
   reproduction:'登记只含 role/value/timestamp 的 object schema；在合法 payload 上分别定义 enumerable own constructor/__proto__/toString，值为合成 JSON 对象；restore 后检查 export 对象 own property。',
   required:'声明查询、optional 校验及必填数据查询采用 own-property 语义；显式声明的同名合法字段仍按 schema 验证。未证明原型污染或代码执行，不扩大结论。',evidence:[batch+'.stdout.txt',batch+'.command.json']},
  {id:'V5-L',priority:'P2',title:'旧恢复绑定跨阶段存活，阻断可信回调选择后续登记模型或工具',
   source:[{path:'packages/agent/src/agent.ts',start:1674,end:1698},{path:'packages/agent/src/agent.ts',start:1705,end:1721},{path:'packages/agent/src/agent-loop.ts',start:435,end:451}],fixture:{path:'v5-boundary.test.ts',tests:['V5-L next-turn trusted model selection preserves uninterrupted behavior','V5-L next-turn trusted tools selection preserves uninterrupted behavior']},
   actual:'无暂停控制均完成 2 次模型调用；恢复仅调用 1 次并报 Restored model binding changed before dispatch 或 Restored tool subset changed before dispatch。合法 next_tool 无法执行。',
   cause:'verifyRestoredDispatch 闭包永久捕获旧 modelBinding/toolNames/signature；可信 prepareNextTurn 更新 config/context 后没有提交下一阶段绑定。',
   reproduction:'第一响应进行中请求暂停并恢复；finishTurn 继续，原有 prepareNextTurn 返回已登记 next model 或只含已登记 next_tool 的 context；比较未暂停控制。',
   supporting_failure:'strengthened-N5: effects=[one,two] 但 calls=1 并有工具子集绑定错误；V4 原记录 calls=2 且无 error。旧 N5 断言仅检查效果，不能证明完整恢复。',
   required:'恢复旧 prepared/request/response/tools/pendingFinish/finish 阶段必须保留 checkpoint binding；仅在其完成后，通过可信 prepareNextTurn/prepareRequest 建立新阶段绑定。登记身份必须独立于可变模型/工具实现；每次 dispatch 继续检查；不可简单清除 guard 或把 mutation 重新签名为可信。',evidence:[batch+'.stdout.txt',batch+'.command.json','strengthened-n5.stdout.txt','strengthened-n5.command.json','v4-n5-control-reference.json']},
];
const results=[
 {name:'original-replays',tests:50,pass:47,fail:3,exit:1,note:'原 V4 fixtures 原样重放；三项缺 custom schema 注册；原失败保留，不能改写为通过。'},
 {name:batch,tests:16,pass:12,fail:4,exit:1,note:'登记兼容版本 10 个测试通过旧断言；J/K/L-model/L-tools 失败；M/N 通过。10 个旧断言中 N5/session 未要求最终模型响应。'},
 {name:'strengthened-n5',tests:1,pass:0,fail:1,exit:1,note:'只增强调用数及无错误断言；最终响应缺失，计入 V5-L，不另造根因。'},
 {name:'original-agent-40',tests:40,pass:40,fail:0,exit:0},
 {name:'worker-2',tests:2,pass:2,fail:0,exit:0},
 {name:'targeted-tsgo',exit:0,note:'类型检查，不等同运行正确性。'},
];
const report={
 schema:'researchos.mu-m0-v5-independent-review/1',status:'FINAL',verdict:'REQUEST_CHANGES',at:new Date().toISOString(),
 reviewer:{agent:'/root/mu_v5_review_resume',role:'independent reviewer; no candidate source writes',model:'inherited session model; not independently attested',model_policy:'AGENTS prefers gpt-6-astra high for independent review; no unverified model label asserted'},
 candidate:{path:source,base_commit:manifest.base_commit,freeze,root_mirror:mirror,manifest_sha256:expectedManifest,source9:manifest.source9},
 integrity:{audit:'resume-evidence-audit.json',author_compiled_inputs:2129,author_bundles:10,independent_compiled_inputs:independentInputs.length,existing_terminal_records:commands.length,rerun:false,historical_results_preserved:true},
 findings,results,author_claim:{candidate:'51/51',agent:'40/40',worker:'2/2',status:'Frozen author evidence verified by hash; not independent acceptance'},
 preserved_controls:{M:'transform/convert/getApiKey/prepareNextTurn mutation: 4/4 blocked before next provider dispatch',N:'extra registered excluded tool not executed; allowed tool executes; 2 model calls',V4:'E/F/G/H/I and registered-only controls retained unchanged; see original-replays'},
 fixture_adaptations:{document:'fixture-adaptations.md',changes:'Only exact schema registrations added to three separately named fixtures; original payloads/assertions/callbacks preserved',limitation:'Registered N5/session PASS is only the old assertion result, not final-response success'},
 repair_contract:'state-contract-v5-addendum.md',
 next_action:'Root may initiate scoped V6 source repair of V5-J/K/L using this final review; fresh independent review required after new freeze. This review does not grant wider write scope.',
 acceptance:{m0_independent_accepted:false,installed_sdk:false,m1_m2_implemented:false,real_provider_calls:0,real_external_tool_effects:0,real_credentials:0,formal_increment:0,formal_cases_accepted:0,formal_cases_total:42,all_22_parents_open:true,parent_acceptance:false},
 reproduction:{node:commands.find(r=>r.name===batch).exe,commands:[`node --test --test-reporter=tap "${dir.replaceAll('\\','/')}/v5-boundary.mjs"`,`node --test --test-reporter=tap "${dir.replaceAll('\\','/')}/strengthened-n5.mjs"`],note:'Commands document reproductions; finalization reused recorded exits and did not rerun or overwrite raw logs.'},
};
fresh('report.json',report);
const md=`# Mu M0 V5 独立复核 — FINAL / REQUEST_CHANGES

V5 不予独立接受。冻结候选存在 **2 项 P1、1 项 P2**，需要 V6 修复后重新冻结并独立复核。当前材料足以启动限定范围修复；未修改候选源、Root Canon、安装 SDK 或正式状态。

冻结 manifest SHA-256：\`${expectedManifest}\`。候选基线 \`${manifest.base_commit}\`；9 个源文件、作者 2129 个实际编译输入、10 个冻结 bundle、Root 镜像、作者 raw/harness，以及独立编译的 ${independentInputs.length} 个输入均核验一致。恢复本次工作时读取既有 ${commands.length} 个完整进程退出记录，stdout/stderr hash 全部吻合；未重新执行或覆盖历史结果。细项见 [resume-evidence-audit.json](resume-evidence-audit.json)。

## 阻断项

${findings.map(f=>`### ${f.id} — ${f.priority} — ${f.title}\n\n${f.actual}\n\n根因：${f.cause}\n\n源位置：${f.source.map(s=>'\`'+s.path+':'+s.start+'-'+s.end+'\`').join('；')}。\n\n复现：${f.reproduction}\n\n修复边界：${f.required}${f.supporting_failure?'\n\n补充证据：'+f.supporting_failure:''}\n\n证据：${f.evidence.map(x=>'['+x+']('+x+')').join('、')}。`).join('\n\n')}

## 测试结果及历史保留

| 记录 | 结果 | exit | 解释 |
|---|---:|---:|---|
| 原样重放 original-replays | 47/50 PASS，3 FAIL | 1 | 三个旧 fixture 缺 typed custom schema 注册；原始失败保留 |
| registered + J–N | 12/16 PASS，4 FAIL | 1 | 登记适配 10 PASS；J/K/L-model/L-tools FAIL；M/N PASS |
| strengthened-N5 | 0/1 PASS，1 FAIL | 1 | 工具效果成功但最终回复未到达；归入 V5-L |
| Agent 原有回归 | 40/40 PASS | 0 | 独立重放记录 |
| 合成 worker 协议 | 2/2 PASS | 0 | 仅 M0 合成协议 |
| targeted tsgo | PASS | 0 | 不代替运行验收 |

作者冻结 51+40+2 的通过记录已核验来源，不能消除本轮反例。以上运行有重复用例，不相加为新的接受总数。三份 registered fixture 仅增加既有数据的明确 schema 注册，diff 已复核；详见 [fixture-adaptations.md](fixture-adaptations.md)。旧 N5 和 session 的通过断言只要求效果完成，其 raw 已出现 binding error/calls=1。增强 N5 添加最终调用数和无错误检查后真实失败；V4 同一流程 raw 为 calls=2、无 error，引用及 hash 见 [v4-n5-control-reference.json](v4-n5-control-reference.json)。

## V6 修复及复核边界

必须保留已恢复旧阶段的 model/config/context/tool-subset 绑定及每次实际 dispatch 校验；原 prepared/response/pendingFinish/finish 的 callback 和已提交效果不得重放。仅在旧阶段完成并经过原可信准备回调后，提交新的阶段绑定。禁止通过清空 guard、扩大为全部 registry tools，或对已经变异的实现对象重新计算 signature 来绕过安全检查。

V6 回归至少保留 J/K 矩阵、L 两种合法切换的无暂停控制、M 四个异步 mutation 拒绝、N 排除额外工具，以及 N5 的最终回复/调用数/无错误/消息恰好消费一次。具体契约见 [state-contract-v5-addendum.md](state-contract-v5-addendum.md)。本报告只支持 Root 启动当前授权范围内的 V6 修复，不扩大 same9 写入范围。

复现使用现有 node 和 \`node --test --test-reporter=tap v5-boundary.mjs\`、\`node --test --test-reporter=tap strengthened-n5.mjs\`；完整既有命令与退出记录在 audit/各 command.json。本次 FINAL 只收口，不重跑。

本轮没有真实 provider 调用、真实外部工具效果或真实凭据。M0 未独立接受，M1/M2、真实 worker/Core RESUME、手机流程、生产安装均不能由本轮推导。正式增量 0，保持 0/42，22 个父任务全部 open。CANCEL 后新 turn 须 newRun；PAUSE 可 sameRun 增 epoch；不擅自把所有恢复规定为 newRun。
`;
fresh('report.md',md);
for(const item of before) verify(dir+'/'+item.path,item.sha256);
fresh('manifest.json',{schema:'researchos.mu-m0-v5-independent-review-final-manifest/1',status:'FINAL',verdict:report.verdict,at:new Date().toISOString(),candidate_manifest_sha256:expectedManifest,report_sha256:hash(dir+'/report.json'),report_md_sha256:hash(dir+'/report.md'),prior_artifacts_unchanged:true,files:inventory(dir),excludes:['manifest.json (self hash)'],formal_increment:0});
console.log(JSON.stringify({status:'FINAL',verdict:report.verdict,findings:findings.map(f=>({id:f.id,priority:f.priority})),source9:9,author_inputs:Object.keys(authorInputs).length,independent_inputs:independentInputs.length,commands:commands.length,report_sha256:hash(dir+'/report.json'),manifest_sha256:hash(dir+'/manifest.json')}));
