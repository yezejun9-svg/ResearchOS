# MXC availability Rev04 — canonical public paths only
状态：PREPARATION_ONLY_NOT_AUTHORIZED。未登记scope、未执行MXC/Native CLI/模型/setup；rev03保持冻结。本包等待Root独立增量审查。

Root发现 C:/nvm4w/nodejs 是指向 C:/Users/yqyyds/AppData/Local/nvm/v24.9.0 的NVM链接。rev03 ordinary()会拒绝该ancestor alias。Rev04保留严格alias拒绝门，只将公开安装二进制绑定实际canonical目录：

- NODE = C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe
  SHA256 5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6
- CODEX = C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe
  SHA256 9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42

唯一wrapper差异：上述两个常量及唯一scope_id=mxc_availability_20261105_e91c。makeEnvironment函数逐字不变；由常量派生的固定PATH相应采用canonical安装目录。normal profile/HOME/APPDATA、ownedTEMP、drop API/proxy/NODE_OPTIONS/CODEX_HOME规则不变。内层executable、外层Node executable和公开input pins同步到canonical路径。

cmd固定路径/SHA、原f13、bounded-capture.mjs字节/hash、official12argv、35s soft/45s f13 hard/5s cleanup、16进程/2048MiB、单次spawn、无setup/model/重试全部不变。strict ordinary()仍逐祖先拒绝isSymbolicLink和realpath不等，无junction豁免。

本次验证仅：
1. canonical-static-check.mjs 对wrapper固定的5项公开输入检查真实路径和每个ancestor，全部PASS；不读取私有认证或用户配置。
2. Node --check wrapper语法PASS。
3. wrapper与rev03做精确replacement差异断言；capture模块逐字/hash一致；argv/budgets完全一致。
4. 实际外层input pins重新读取hash吻合，rev03 MANIFEST全部成员无漂移。
未重跑此前流suite。rev03已有13项独立virtual-IO验收来源：
C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-mxc-availability-security-review-rev03/REVIEW.json
SHA256 5c050272594be2815b4bbb17a7d94a18be431e49c8801af304cb2b5fbc273d34
其结论是APPROVED_SOURCE_FIXTURE_ONLY，不代表Native实际执行。

Root登记步骤仍为：独立审查后生成本目录mxc.scope.json，设置ROOT_REVIEWED_EXACT_COMMAND并计算最终hash；填入外层f13模板argv及inputs，authorization同样需Root审查授权；在未修改的f13 scopes目录登记最终scope，调用原CLI。模板中ROOT_FILL_REGISTERED_INNER_SCOPE_SHA256不可直接执行。capture helper pin仍必须在f13 inputs中。

run_root位于原f13 runs/mxc_availability_20261105_e91c/mxc。后续Node才会新建空cwd、owned tmp与durable bounded诊断，当前无run/CONSUMED或registered inner scope。
本包只移除已证实的alias前置阻断；不宣称MXC已就绪、不启动本地echo、更不放行产品或模型重试。结果仍availability-only、resource_ready=false、formal/product增量0。既有globalHarnessinvoke1及FAILED记录不变。

