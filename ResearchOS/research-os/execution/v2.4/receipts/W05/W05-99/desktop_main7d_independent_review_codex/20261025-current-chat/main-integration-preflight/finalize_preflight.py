import fnmatch,hashlib,json,pathlib,subprocess
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');OLD=E.parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
inputs=['AGENTS.md','apps/desktop/package.json','execution/commands.json','execution/v2.4/commands.json','execution/command_dispatcher/dispatch.py','tests/ui/check/main.py','ops/ci/ui.py','execution/import_manifest.json','spec/v2.0/PACKAGE_MANIFEST.json','execution/v2.4/path_ownership.json','execution/v2.4/receipts/W02/W02-99/parent_driver.py']
out=E/'references';out.mkdir(exist_ok=False);refs=[]
for rel in inputs:
    p=R/rel;raw=p.read_bytes();target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    refs.append({'path':rel,'source':str(p),'copy':str(target),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
owner=json.loads((R/'execution/v2.4/path_ownership.json').read_bytes())
seven=json.loads((E/'MAIN-SEVEN-PATHS-INDEPENDENT.json').read_bytes())
aliases=[]
for name,item in owner.get('aliases',{}).items():
    paths=item.get('paths',[])
    related=[p for p in paths if any(fnmatch.fnmatchcase(row['path'],p) or row['path'].startswith(p.rstrip('/')+'/') or p.startswith(row['path']) for row in seven['seven_paths'])]
    if related:aliases.append({'alias':name,'owner':item.get('owner'),'related_paths':related})
registry=json.loads((R/'execution/v2.4/commands.json').read_bytes())['commands']
assert registry['desktop.shell_launch']['state']==registry['desktop.installer_build']['state']=='UNBOUND'
assert registry['test.ui.routes']['argv']==['-X','utf8','tests/ui/check/main.py']
assert 'scripts' not in json.loads((R/'apps/desktop/package.json').read_bytes())
policy={'project_AGENTS_sha256':sha(R/'AGENTS.md'),'nearest_nested_AGENTS_found':False,'desktop_package_main':'main/main.js','desktop_package_scripts_absent':True,'desktop_shell_launch':'UNBOUND','desktop_installer_build':'UNBOUND','test_ui_routes':{'state':registry['test.ui.routes']['state'],'argv':registry['test.ui.routes']['argv'],'selectors':registry['test.ui.routes']['selectors']},'test_auto_discovery':False,'manifest_registration_for_exact_7_source_merge_required':False,'reason':'Existing package entrypoint unchanged; imported spec manifests are frozen; existing registry dispatches explicit BOUND argv/selectors and does not enumerate added standalone tests. Development commands remain unregistered.','owner_aliases_related_to_scope':aliases,'shared_changes':'CP555 scope/lease/ownership/checkpoint integration remains Root serial responsibility; no command binding or formal selector changes implied.'}
put('REGISTRATION-POLICY-REVIEW.json',policy)
source_seal=OLD/'complete-tree/R3-REVIEW-SEAL.json';native_seal=OLD/'native-proof/NATIVE-PROOF-REVIEW-SEAL.json'
assert sha(source_seal)=='2981911af85ea4163389592041a9474f0ed5ed8e027ba5ac131e3912560b939c'
assert sha(native_seal)=='3d72854b82043931e4190d55b7803e0456a4a27f5cf15d2f7642363db409a1c9'
freeze=json.loads((OLD/'complete-tree/r3-fixed-inputs/SOURCE-FREEZE-03.json').read_bytes())
for row in seven['seven_paths']:assert row['candidate_sha256']==freeze['seven_file_hashes'][row['path']]['sha256']
put('INPUT-REFS.json',refs+[{'source':str(source_seal),'sha256':sha(source_seal)},{'source':str(native_seal),'sha256':sha(native_seal)}])
def git(*args):return subprocess.run(['git','--no-optional-locks','-C',str(R),*args],capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().strip()==seven['head']
assert not git('diff','--cached','--name-only')
assert git('status','--porcelain=v1','--untracked-files=no').decode().splitlines()==seven['tracked_dirty_paths']
for row in seven['seven_paths']:
    p=R/row['path']
    if row['change']=='A':assert not p.exists()
    else:assert sha(p)==row['main_sha256']
for ref in refs:assert sha(ref['source'])==ref['sha256']
put('FINAL-READONLY-BASELINE-CHECK.json',{'main_head':seven['head'],'index_empty':True,'tracked_dirty_count':20,'tracked_dirty_paths_unchanged_during_review':True,'seven_paths_unchanged_during_review':True,'registration_reference_hashes_unchanged':True,'source_writes':0,'application_starts':0,'tests_executed':0})
diagnostics=[]
for path in sorted(E.glob('[0-9][0-9][0-9]-*/result.json')):
    row=json.loads(path.read_bytes())
    if row['native_exit']!=0:diagnostics.append({'read_step':path.parent.name,'native_exit':row['native_exit'],'result_sha256':sha(path)})
put('DIAGNOSTICS.json',{'read_nonzero_results':diagnostics,'explanations':{'003':'Read probe treated tests/ui/check as a file and guessed nonexistent bootstrap/platform_manifest.json; corrected by actual Git file discovery. No source test ran.','005':'rg search returned no matches (exit1); preceding known registry/source reads succeeded.','006':'rg search returned no matches (exit1); preceding source/metadata reads succeeded.','007':'Guessed nonexistent execution/command_dispatcher/main.py; actual tracked dispatcher dispatch.py subsequently read. No source test ran.'},'001':'Initial full untracked Git filename listing was excessively large; retained raw metadata output. Later review used exact seven path queries and tracked-only status. No listed data/database file was opened.','source_failures':0,'tests_executed':0,'application_starts':0,'cleanups_or_denied_action_retries':0})
report='''# Desktop Main integration — independent preflight

**结论：PASS_FOR_EXACT_SEVEN_PATH_LOCAL_FAST_FORWARD；当前阻断项0。** Main `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e` 是候选 `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419` 的直接父。Root登记CP555精确整合scope后，可执行本地 `git merge --ff-only ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`，保持未提交成果和现有平台登记。

## 精确路径

| 路径 | Main现状 | 可整合性 |
|---|---|---|
| apps/desktop/build-development.py | 文件及索引均不存在 | 新增无碰撞 |
| apps/desktop/launch-development.mjs | 文件及索引均不存在 | 新增无碰撞 |
| apps/desktop/main/main.js | 工作文件=7d父blob，路径无dirty | 修改无碰撞 |
| docs/installation/desktop-development.md | 文件及索引均不存在 | 新增无碰撞 |
| tests/ui/desktop/development-bundle.test.py | 文件及索引均不存在 | 新增无碰撞 |
| tests/ui/desktop/development-launcher.test.mjs | 文件及索引均不存在 | 新增无碰撞 |
| tests/ui/desktop/development-smoke.test.mjs | 文件及索引均不存在 | 新增无碰撞 |

索引为空；原20条tracked dirty均在七路径之外，并在复核结束时保持一致。七个候选blob的SHA与已审r3冻结表逐项匹配。详细字节、索引entry、路径状态见 `MAIN-SEVEN-PATHS-INDEPENDENT.json`。此结论不授权stage已有dirty、reset/clean、push或重试曾被拒绝的临时文件删除。

## 登记与规则

实际生效的项目规则是 `research-os/AGENTS.md`；七路径祖先下没有额外AGENTS。规则允许本地原子整合，要求保护旧修改，明确共享锁/路由/命令登记由主Agent串行整合，并区分开发夹具、真实运行和正式验收。

本次无需修改 `apps/desktop/package.json`：既有main仍为 `main/main.js`，未新增依赖或package script。`execution/import_manifest.json` 和 `spec/v2.0/PACKAGE_MANIFEST.json` 属于导入规格记录，不应为实现新增文件改写。完整开发输出的生成manifest已独立封存；源码fast-forward不迁移或重写该输出。

`execution/v2.4/commands.json` 中 `desktop.shell_launch`、`desktop.installer_build` 仍为UNBOUND。dispatcher `dispatch.py` 仅对明确BOUND的argv/selector执行；既有 `test.ui.routes` 调用 `tests/ui/check/main.py`，后者按W13-01/C23路由固定driver或legacy workflow，不自动发现新加的三个独立测试。合并这七文件不要求更改commands或把新测试挂入正式selector。已有source/build/native证据来自其明确的直接调用，不能被描述为已由通用W13 dispatcher覆盖。若以后要提供平台可调度构建/启动命令或正式测试路由，应另行登记owner、精确argv/环境/selector及验证，不能把当前UNBOUND默认为已绑定。

W02父gate的路径检查验证现存BOUND handler和已登记owner路径；没有“新增每个源码/测试文件都必须注册command或manifest”的规则。本轮未改这些共享登记。Root的CP555 scope、owner/lease与checkpoint整合仍是执行前独立的串行步骤；本复核不代写共享状态。

## 证据复用边界

可引用既有source/build seal `2981911af85ea4163389592041a9474f0ed5ed8e027ba5ac131e3912560b939c` 和有限owned native seal `3d72854b82043931e4190d55b7803e0456a4a27f5cf15d2f7642363db409a1c9`，条件是整合后Main HEAD精确为ecc28、tree精确为 `1d44a02c9483fc529b08ffe81895ec443920bdd1`、七个实际文件仍等于r3 blob，原输出manifest `e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620` 与原始回执保持不变。直接fast-forward保持相同提交/blob，因而没有单纯为branch指针移动重跑build/native的理由。

复用仍只能说明“这些源码曾生成该绑定开发输出，该输出完成了那次新状态目录的owned smoke”。它不是合并后重新构建/重新运行的证据，也不证明带原20条dirty的Main完整工作树与干净候选源码完全相同。尤其不要在dirty Main直接重跑新builder：它会拒绝七路径之外的修改；后续重新构建应使用适当干净隔离源码，不能为运行builder清掉旧成果。原location-bound bundle和原fresh-state运行不能换路径或换状态冒充新证据。

整合后独立检查只需确认精确commit/tree/seven blobs、原20dirty/48保护refs、C57未merge及计数/commands登记未被改写。此前诊断、file-symlink权限skip、development-only及有限native边界全部保留；不升级C57原恢复、installer、W13/W20全项或正式v2.4接受。

## 复核留痕

本轮只写 `main-integration-preflight` 独立回执；Main/source/shared state修改0、测试运行0、GUI/Core启动0、清理/拒绝重试0。发现阶段的003/007路径误查及005/006搜索无匹配非零结果原样保留于DIAGNOSTICS，均不是候选测试失败。所有规则/dispatcher/registry/manifest读取均有原始输出和实际文件hash refs。
'''
with (E/'MAIN-INTEGRATION-PREFLIGHT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
print(json.dumps({'verdict':'PASS_FOR_EXACT_SEVEN_PATH_LOCAL_FAST_FORWARD','blocking_findings':0,'report_sha256':sha(E/'MAIN-INTEGRATION-PREFLIGHT.md'),'registration_required':False,'source_and_native_evidence_reuse':'Exact same committed blobs and original output only','read_diagnostics':len(diagnostics)}))
