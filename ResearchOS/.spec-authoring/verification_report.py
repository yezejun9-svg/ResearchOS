from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,sys
P=Path(__file__).resolve().parents[1]/'ResearchOS_Implementation_Package_v2.4'
V=P.parent/'ResearchOS_v2.4_verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
probes=[]
for f in sorted(V.glob('qoder-probe-*.json')):
    raw=json.loads(f.read_text(encoding='utf8'));out=json.loads(raw['stdout_redacted']);body=out['result'].strip()
    result=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',body))
    probes.append({'file':f.name,'sha256':sha(f),'requested_model':raw['requested_model'],'elapsed_seconds':raw['elapsed_seconds'],
       'exit_code':raw['returncode'],'input_sha256':raw['input_sha256'],'response':result,
       'agent_tools':raw['agent_tools'],'mcp':raw['mcp'],'product_acceptance':'NOT_RUN','goal_long_run':'NOT_RUN',
       'provider_reported_model_key':list(out.get('modelUsage',{})),
       'warning':raw['stderr_redacted'].strip()})
final=probes[-1]
assert all(sha(P/name)==h for name,h in final['input_sha256'].items())
answer=final['response']
assert answer['repository_root']=='D:/作品集/ResearchOS/research-os'
assert answer['first_step_id']=='W00-01'
assert answer['full_goal_path'].endswith('/ResearchOS_Implementation_Package_v2.4/08_AGENT_EXECUTION_GOAL.md')
assert '22' in str(answer['completion_guard']) and '42' in str(answer['completion_guard'])
probe_report={'scope':'READ_ONLY_ATTACHMENT_COMPREHENSION_NOT_GOAL_EXECUTION','requested_model':'Qwen3.8-Flash',
 'run_count':len(probes),'final_input_hashes_match':True,'review_status':'PARTIAL_STRICT_OUTPUT_CONFORMANCE',
 'verified':['CLI process returned normally','current repository and full Goal path identified','first step/title/required reads identified','22 parent tasks and 42 final cases plus independent acceptance understood','no inference that state file exists or is absent'],
 'remaining_difference':'Final response used null instead of [] for no dependencies. The first response also missed the displayed repository path; explicit path table and bootstrap wording were added before the final probe. The machine task selector supplies canonical dependencies and does not rely on model extraction.',
 'not_verified':['Qoder long-running /goal','ResearchOS runtime','provider backend identity beyond requested catalog route','cost accuracy when upstream usage fields are zero'],
 'runs':probes}
put(P/'references/Qoder_Attachment_Probe_2026-10-01.json',probe_report)
base=json.loads((P/'references/Repository_Baseline_2026-10-01.json').read_text(encoding='utf8'))
repo=Path(base['repository_root'])
def git(*args):return subprocess.check_output(['git',*args],cwd=repo,encoding='utf8').strip()
assert git('rev-parse','HEAD')==base['head']
assert git('status','--porcelain=v1','--untracked-files=normal').splitlines()==base['git_status_porcelain']
assert all(sha(repo/name)==h for name,h in base['file_hashes'].items())
old=P.parent/'ResearchOS_Implementation_Package_v2.3'/'ResearchOS_Implementation_Package_v2.3';om=json.loads((old/'PACKAGE_MANIFEST.json').read_text(encoding='utf8'))
assert sha(old/'PACKAGE_MANIFEST.json')==base['source_package_manifest_sha256']
assert all(sha(old/e['path'])==e['sha256'] for e in om['files'])
report={'package_version':'2.4.0','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'scope':'SPECIFICATION_AUTHORING_AND_HELPER_TOOLS_ONLY','product_tests':'NOT_RUN','goal_long_run':'NOT_RUN',
 'execution_plan_sha256':sha(P/'contracts/execution.plan.json'),
 'independent_review':{'result':'NO_OUTSTANDING_P1_IN_REVIEWED_SCOPE','reviewed_plan_sha256':'1753953b9fea4a2321bf6ff6af34ffcc1f6c1e1408990476d7d040f82c28bfdb',
  'closed_findings':['real issue selection after onboarding fix','legal explicit writer takeover','continuation namespace/ADR protection','provider probe vs tool validation','existing task required for file saving','bootstrap state creation and write scope','direct qualification commands before dispatcher','parent/child scope and version-prefix agreement','93 exact parent checks and 63 case-key selectors','provider/restore dependencies and fixture UI integration boundary']},
 'checks':{'package_validation':'See ../PACKAGE_VALIDATION.json for final manifest validation','task_packet_tests':4,'qoder_tool_tests':4,
  'task_card_count':71,'parent_task_count':22,'acceptance_case_count':42,'protocol_fixture_count':106,
  'protocol_fixture_positive':76,'protocol_fixture_negative':30,'strict_jsonschema_validation':'Agent ran Draft202012Validator with FormatChecker; all 106 matched expected outcomes',
  'local_markdown_links':'PASS for active specification docs and cards; reference URLs are source citations',
  'launcher_check_only':'PASS: Qoder CLI 1.1.64 and exact catalog name Qwen3.8-Flash',
  'qoder_attachment_probe':'PARTIAL_STRICT_OUTPUT_CONFORMANCE; see Qoder_Attachment_Probe_2026-10-01.json',
  'offline_prototype':'8 Chrome DOM checks; 1440 light, 390/320 dark overflow checks. Offline prototype only.'},
 'preservation':{'repository_head':base['head'],'git_status_unchanged':True,'observed_repository_file_hashes_unchanged':True,
   'old_v23_manifest_and_all_registered_file_hashes_unchanged':True},
 'not_claimed':['New product implementation','real Desktop integration/installer','actual provider/source/holdout qualification','8-hour product recovery','Qoder Goal completion'],
 'cleanup':{'prototype_temp_directory':'C:/Users/yqyyds/AppData/Local/Temp/researchos-prototype-75785ee94f9d42f79e0a3c58fe47d0f4',
   'status':'AUTOMATIC_APPROVAL_REJECTED_CLEANUP','reason':'blocked by policy','associated_chrome_processes_observed':0,'retry_policy':'Stopped after recursive and then narrower exact-file cleanup were rejected; no workaround.'}}
assert report['execution_plan_sha256']==report['independent_review']['reviewed_plan_sha256']
put(P/'references/Authoring_Verification_2026-10-01.json',report)
(P/'references/Authoring_Verification_2026-10-01.md').write_text('''# v2.4 编制验证与限制

本记录仅证明规格与配套工具检查，不是产品通过。机器细节见[验证记录](Authoring_Verification_2026-10-01.json)，最终文件hash校验见[PACKAGE_VALIDATION](../PACKAGE_VALIDATION.json)。

71张卡、22父任务、42正式用例；93父门与63用例命令组合已精确绑定。23本地方法、14事件、106正负协议样例与产品/UI合同对齐。独立复核确认本轮列出的P1规格阻塞已修正。task_packet与Qoder工具共8项自检通过；伪接受、坏hash、非法ID、缺模型和超时进程树回收有检查。

本机Qoder CLI 1.1.64的CheckOnly通过，目录含精确Qwen3.8-Flash。两次禁用全部Agent工具/MCP的附件探针均正常返回；第一次发现路径和引导文字易误读，修订后第二次正确识别绝对路径、首卡、所需读取和完整完成门。第二次把“无前置依赖”输出为null而非[]，因此严格输出一致性记PARTIAL，未伪称全绿。实际施工的依赖来自机器plan/task_packet，不由模型从自然语言重建。见[探针详情](Qoder_Attachment_Probe_2026-10-01.json)。宿主提示一个skill config warning，但未阻断推理；未为此修改全局skills。

只读附件探针没有执行文件读取工具、施工/goal或任何ResearchOS产品操作。模型后端内部标识qfmodel、空usage/0成本字段不证明供应商实际模型身份或真实费用；只确认本次请求使用CLI目录中的指定模型路由并取得响应。

桌面离线预览做过8项Chrome DOM自检及1440px浅色、390/320px深色布局检查；它仍是示例交互。真实Windows壳、provider、打包、手机、独立holdout和8小时产品运行均待实施阶段验证。

已重查原research-os HEAD、Git改动列表、观察文件hash，以及旧v2.3 manifest和全部登记文件hash，均未改变。

自动审批拒绝了浏览器验证临时目录的递归清理，以及随后仅删除明确生成文件的较小操作，理由均为blocked by policy。已停止清理，关联Chrome进程只读确认0；残留绝对路径见机器记录。该残留不在交付包内。
''',encoding='utf8')
print('Authoring evidence written; no product or Goal completion asserted.')
