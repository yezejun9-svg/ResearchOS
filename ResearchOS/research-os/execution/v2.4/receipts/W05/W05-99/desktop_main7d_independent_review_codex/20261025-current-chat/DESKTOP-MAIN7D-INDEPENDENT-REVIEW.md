# Main7d Desktop development tree 独立只读审查

结论：`build-validator.py` 的成功产物不能直接证明或完成真实 Core 启动。下一份最小实施 scope 应新增完整 development builder、明确隔离的 launcher 与边界测试，并只修改既有 `main/main.js` 的 smoke 判定/证据输出。`desktop-management.js`、`native.js` 和旧 `build-validator.py` 本轮没有必要修改。目标仍是 source-bound、repo-shaped development tree，不是安装器、签名发布或可重定位安装认证。

冻结输入为 Main commit `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`，tree `de59625ee5c1d360c741c95ec3f84b6f2764bb0e`；CP551 scope SHA256 `6872af4a2aa0f2268394a8e0867e328f6a443dca531f9d2215715485e6bcbc42`。四个指定文件均从git blob复制到自有回执快照；另只读两个main直接依赖host/http-wire，未扩大到全仓库扫描。没有GUI/Core启动、原DB/credential/ACL/进程读取、源码或卡状态修改。

## 三个具体阻塞点

| ID | 实证与文件行号 | 影响与最小处理 |
|---|---|---|
| D01 完整资源缺失 | `apps/desktop/build-validator.py:96-100`仅构建client-wire validator、negative child和validator test；112-138复制main/preload/React/openapi并生成client-wire descriptor。`main/main.js:40-46`默认读取resources/control下Core、verifier manifest和runtime。`main/lib/desktop-management.js:138-164,417-418`强制读取并校验这些资源。 | 该builder成功仅证明前端与validator产物构建；默认Core路径缺文件时start在spawn前失败，460-462返回BROKEN。新增build-development.py复用旧builder，再生成Core、真实verifier及installation manifest、Mu bundle+metadata+node和实际启动所需精确公共资源。外部Electron runtime可以固定引用或显式打包，不能宣称旧builder已复制它。 |
| D02 新目录尚不等于隔离启动 | `main/main.js:26-29`仅选Electron userData；36-46分别接受ambient discovery/data/Core/verifier/runtime覆盖，152-153还接受旧project/session。`desktop-management.js:421-427`拒绝已存在外部Host；但main:367-368仍随后调用独立ensureCore；直接依赖host.js:52-64在requireLaunchDisabled前仍可读discovery并probe已有Host。`native.js:58-74,91-103`按所选discovery.data_dir读session并可能连接对应bootstrap pipe。 | 不应以只设置USER_DATA或位于新worktree就保证不碰旧业务。新增launcher从新bundle清单计算全部绝对路径、限制选中新fresh运行根、清除ambient RESEARCHOS_/ROS_DESKTOP_及Node/Electron注入项，只放行所需系统环境并显式设置userData/data/discovery/资源路径。旧project/session/capture/legacy等不能意外继承。启动前缺资源/路径逸出/alias/运行根已有不匹配证据就失败，不能fallback原路径。 |
| D03 smoke exit0是假阳性可能，不含成功shutdown证据 | `main/main.js:403-407`native probe可省略；427的code只看renderer与可空probe，不检查management READY；429丢弃shutdown返回，只在失败时432/436打印记录。`desktop-management.js:773-790`本身已确认SHUTDOWN_ACCEPTED、actual child exit0及STOPPED，并返回process_exit_confirmed。 | 009执行冻结main的原smoke块（仅mock app/manager，无GUI/Core），复现BROKEN+probe缺失→exit0，BROKEN+probe.ok→exit0；READY+成功shutdown→exit0但没有成功事件。确需允许main.js这一个既有路径小改：smoke成功必须READY、nativeProbe.ok、renderer正确；保存成功shutdown返回并输出shutdown_confirmed，原失败/未知child逻辑保留。launcher强制两项smoke env并解析READY、native probe、ownedCore身份和shutdown证据，不能仅看exit0。 |

009的冻结main SHA256 `1a55e7f9f0afaeccb5dae268b5dbca987092addbab70c9bac367fc46bb00ced1`；原smoke块SHA256 `782617ae276428d44d77f00214251acebeea9779c679b72c65a4d50787e223b4`。这是实际执行原JavaScript分支的隔离模型证据，**不是Electron/真实Core native smoke**。

`main.js:409-410`的host_launched_by_shell/spawns来自禁spawn的legacy ensureCore；真实Core由desktopManagement:440发起。因此不能要求现有spawns==1来证明ownedCore。推荐同一main小改只输出已通过management currentHost/identity核验的非敏感control PID、creation、image hash、host ID；不得输出session/token。之后shutdown_confirmed绑定该owned identity。管理私有协议和native credential读取方式保留。

## 建议最小源码 allowlist

1. 新 `apps/desktop/build-development.py`：编排旧validator builder、精确Core/verifier/Mu/runtime公共输入与完整资源生成；create-new输出，完整before/after/工具/输入/输出清单；不就地补丁旧产物、不安装依赖。旧build-validator.py的既有绑定和校验继续保留。
2. 新 `apps/desktop/launch-development.mjs`：产物清单及受支持路径验证、fresh运行根、环境白名单、显式data/discovery/userData/Core/runtime路径、native smoke监督与记录。提供不启动进程的dry-run输出用于边界测试；argv数组执行固定Electron，不经shell拼接。
3. 既有 `apps/desktop/main/main.js`：仅上述smoke成功条件、ownedCore非敏感证据、成功shutdown_confirmed输出；禁止改变private protocol、业务权限或失败退出安全分支。
4. 新 `apps/desktop/tests/development-tree.test.mjs`：完整资源inventory、路径/环境隔离、精确smoke分支和报告验收的有限正反测试。若Python builder测试确需独立脚本，Root可另列一个明确测试文件；不默认扩大生产代码范围。

bundle保持 `apps/desktop`、`apps/web/dist`、`spec/v2.0/contracts` 等当前repo-shaped布局。client-wire descriptor绑定main/preload清单，因此main改动必须先冻结源码再构建；禁止构建后手改main而不重建descriptor。新builder本身、launcher、选定source commit+最小delta都必须加入总manifest；不能只继承旧builder的输入摘要并冒称新编排代码也已绑定。

Mu构建若使用common Main公共5083 vendor/cache，按Root当前允许的来源逐字节核对并在总manifest明确标为外部公共输入，记录真实路径/hash；不能写成新worktree自身内容。此审查没有读取该vendor或断言本轮Mu资源已生成。

## 有限验证与下一步

- 第一阶段不启动GUI/Core：构建成功且输入零漂移；逐一验证default资源路径与管理installedResources要求闭合；新launcher dry-run的cwd/argv/env只指向新bundle和自有fresh运行根，注入旧discovery/data/Core/project/session等环境时应忽略或拒绝；资源缺失/tamper、路径alias/逸出、非fresh根应在spawn前失败。
- smoke逻辑测试只执行冻结代码块或注入fake manager：BROKEN、native probe缺失/失败、READY但shutdown拒绝/未退出必须失败或保持明确未退出；成功需READY+native probe+renderer+匹配ownedCore+shutdown_confirmed。测试不得把mock shutdown当真实退出。
- 下一份明确允许自有native运行的scope才启动一次自己的Electron/Core，绑定PID/creation/image与独立data/discovery，要求真实renderer→validator→host.status返回成功，以及私有SHUTDOWN_ACCEPTED→owned child exit0→STOPPED→shutdown_confirmed；不得对原Core/原数据操作。未出现确认退出时保留该owned实例证据并交Root处理，不扫杀其他进程。

## 捕获与诊断

001-009检查均预写recipe并保存raw stdout/stderr/native exit，native均0；009只执行上述原JS片段，没有进程spawn/GUI/Core。初始读取CP551 scope及旧review wrapper的bootstrap只在工具记录保留（chunk ca34be），没有补称预写recipe。003/004工具展示截断但落盘raw完整。记忆检索只有无关接口文档命中，未用作本次项目事实依据。源码冻结/只读证据不能算Source修改接受或W20/W13/formal接受；formal增量0。
