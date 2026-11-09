# React frontend intake — bounded source mapping

状态：READ_ONLY_INTAKE_COMPLETE；source_edit_authority=false；actual_authority=false；formal_increment=0。仅供 Root 冻结实施卡，不签发父任务接受。未启动应用、Core、provider、worker；未读取原 dataRoot/config/secrets。以下为源码观察与整改建议，不是浏览器实测。

## 结论与最小整改

产品已经使用 React 19.3.0、react-dom 19.3.0、Vite 8.3.1、Node >=24（apps/web/package.json:6-17）；无需换框架。首卡围绕「当前项目 → 当前会话/目标 → 下一步操作 → 结果与证据」统一页面，不引入新的状态库或重写服务协议。

建议明确编辑集：
- apps/web/src/main.jsx：拆出导航与 AppShell；保留 routeOf/useRoute、AuthGate/PairingGate、shared 查询、事件恢复、反馈、主题和键盘焦点行为。让项目入口、会话区、结果区共用清晰层级。
- apps/web/src/screens.jsx：沿用全部 Screen 分派；Projects、Workbench、Settings 的结构统一；业务详情页只换公共呈现，不删功能。
- apps/web/src/workbench.jsx：主要重排 NativeWorkbench 的 JSX，抽取 SessionSidebar、ConversationPanel、WorkspacePanel；保留命令生命周期、project/generation 防串写、host/session 重读。资格与编码授权逐步展开，不得隐藏阻塞或绕过明确确认。
- apps/web/src/continuity.jsx：浏览器对话接续使用同一套视觉组件，但保持自己的 V2 transport；不要强行接入 window.researchos。
- apps/web/src/style.css：统一 shell、层级、表单、响应式、空态/错误/加载/只读；保留可聚焦、44px移动目标、reduce-motion。
- 新增 apps/web/src/components/ui.jsx、apps/web/src/components/app-shell.jsx；如抽出路由/labels/Link，新增 apps/web/src/navigation.jsx，切断 screens.jsx -> main.jsx -> screens.jsx 现有循环。新建目录前按 Root 项目约定登记目录责任。

保留但首卡原则上不改协议逻辑：api.js、hooks.js、operations.js、v2client.js、Pairing.jsx、profile-draft.jsx、resource-recovery.js/.jsx、session-continuation.jsx、preview.jsx。仅在确实需要统一外观时改其 JSX/classes，单独点名变化；不改 frozen spec/v2.0/ui/design-tokens.json，若视觉方向与固定token冲突，采用app层语义token且由Root确认卡范围。

首卡无需改 Desktop/Core/backend。只有新增原生能力、改变路由允许表或协议字段才另开卡；不能借视觉整改扩大IPC能力。不要以仅有 mock 数据的新dashboard代替以上真实页面。

## 实际入口、状态与页面

| 责任 | 代码锚点 | 当前行为/必须保留 |
| --- | --- | --- |
| React bootstrap | apps/web/index.html:4; src/main.jsx:169 | #root -> App，唯一生产入口 |
| URL/导航 | main.jsx:18-35,145-165 | /、/p/:id；cycles/tasks/releases/experiments 选择页与详情；evidence、knowledge、team、resources、settings；query/search、history/back、深链 |
| 主状态 | main.jsx:89-143; hooks.js:3,39 | 页面本地state；shared profile/state/progress/releases/notifications；revision刷新；SSE/轮询恢复；theme独立localStorage |
| 浏览器认证/设备 | main.jsx:153-154; Pairing.jsx:5,42,55 | 内存token；/pair challenge；reader/controller；refresh同一幂等请求、过期/撤销；设备管理 |
| 项目入口/首次使用 | screens.jsx:61-66; workbench.jsx:156-183 | 浏览器真实createProject；Desktop选本地授权目录、返回project/workspace引用、已有身份接续 |
| Native会话 | workbench.jsx:385-565 | selectProject -> host.status/session.list/context -> openSession；新建/分页；模型/工作区选择；writer租约接管；发送NORMAL/STEER/FOLLOW_UP；PAUSE/RESUME/CANCEL；消息/工具/权限/产物 |
| 浏览器接续 | continuity.jsx:36-120; v2client.js:31-57 | /continuity 独立V2客户端；session/goal/workspace/provider相关producer及草稿/冲突；Desktop此路由归回workbench |
| 目标/任务/运行 | screens.jsx:29,69,88; session-continuation.jsx:11-58 | IdeaForm、真实goal/task引用；Task详情及run状态；不能把运行完成等同任务验收；goal批量完整性与project归属验证 |
| 研究详情 | screens.jsx:80-186 | cycle、release、evidence、experiment、knowledge、team、resources、资源预算/请求/恢复 |
| 配置与恢复 | screens.jsx:193-200; profile-draft.jsx:6; resource-recovery.js:7 | RunPolicy CAS；ProfileDraft冻结编辑基线/冲突；资源恢复读取当前request/task/run/runtime并生成受控报告，不能直接改状态 |
| 原生产物 | preview.jsx:7; workbench.jsx:568 | hash/ref验证、受控文本/图片/PDF/HTML预览与下载；不得仅用外链替换 |
| 原生资格/配置 | workbench.jsx:44,186,260 | host.configure pending跨卸载、original-host核对；qualification/coding prepare-confirm-status；不能以配置保存代表运行资格 |

UX割裂由源码推断：main.jsx固定导航+阶段rail占用工作区，默认Electron窗口1180px会进入压缩导航；screens.jsx:215按native桥接切换完全不同的首页；浏览器另有continuity入口而Desktop隐藏；NativeWorkbench:530-564先放配置/资格/编码授权，再会话，再文件，主任务被长表单切开；Header/Section/Panel/Empty在多个文件重复；screens.jsx有49KB、workbench.jsx有57KB且多处长行JSX，样式集中20个压缩行，不利于保持一致。并未把这些推断当成已经观测到的视觉缺陷。

## Desktop生产连接与打包

apps/desktop/package.json:6 指向 main/main.js。main.js:35 把 WEB_DIST 指向仓库 apps/web/dist；:364-365注册 ros-app 协议；:392-393默认打开 ros-app://desktop/，只有显式 ROS_DESKTOP_LEGACY_WORKBENCH=1 才打开legacy HTML。:369-376保持contextIsolation、sandbox、禁nodeIntegration、同origin导航和禁止新窗。

app-protocol.js:106-128 提供dist静态文件和无扩展名SPA回退（丢失asset必须404）；:131-167只代理OpenAPI允许的 /v1/*，凭据由主进程附加，GET可更新认证后重试，写操作401不得自动重放。V2由 preload/v2 IPC到同一Core命令契约，不是把/v2/command当成ros-app HTTP路由。

构建已确认引用：ops/ci/build.py:38、ops/ci/ui.py:55 使用 node apps/web/node_modules/vite/bin/vite.js build；ops/release/build.py:299-312构建web并装入发布物 web/dist/；ops/release/start.ps1:29设置RESEARCHOS_WEB_DIR=web/dist。该阅读证明web发布路径，不证明Electron安装包发布闭环；desktop package.json没有package/build脚本。本轮不宣称存在已验证Desktop installer。

## 不可回归契约

1. URL深链、back/forward、项目切换、设备角色和native/browser分流不能丢；所有原路由保留可达入口。
2. api.js:38-41 的Authorization分流、If-Match、Idempotency-Key；hooks.js:67-83 的序号去重/缺口重取/410恢复；错误、部分加载、草稿冲突不可覆盖成成功或空列表。
3. v2client身份、revision、writer epoch、幂等键、未知结果和COMMAND_PENDING；NativeWorkbench current.generation防止异步结果写入另一项目；writer lease判定与断网禁写。
4. ModelConfiguration pending/outcome及原host核对；Coding commit后重读host/session/context；明确confirm与未确认关闭保护保持。
5. ProfileDraft保持冻结基线、不自动新revision重试；ResourceRecovery保持实时ref和产物证据；SessionContinuation必须读完目标全部task_ids并核对归属。
6. 产物hash/ref、HTML sandbox/CSP与受控下载；权限审核真实回执；focus trap/Escape/返回焦点、aria-label、reduced-motion、移动布局。

## 可立即给Root的preview路线

没有专用无API完整产品preview路由；preview.jsx是ArtifactPreview组件。纯Vite服务不注入native桥。
- 仅查看认证页：独立端口Vite preview，GET /；不填token不会进入业务查询。/pair显示配对页，不提交不会消费challenge。
- 查看原工作台外观：独立浏览器context，在页面加载前拦截 /v1/** 与 /v2/**，完整返回disposable fixture并禁止请求fallthrough；填入fixture token后走原React路由。Desktop NativeWorkbench还需要page.addInitScript注入仅fixture window.researchos接口；不得让此stub进入生产入口。两者只证明真实组件的视觉/交互，不证明真实服务行为。
- 服务联通验证：使用完全隔离的临时Core/SQLite/owner/dataRoot/port/userData/discovery夹具。现有 tests/ui/w1303/preview_run.py:45-49 有隔离环境设置，:75-86确实启动临时Core，preview.cjs:37-40确实启动Electron，故不是纯静态路线。直接开 apps/desktop 会运行desktopManagement.start()/host.ensureCore()，不适合作为无native预览。
- apps/web的build-only脚本不含dev/preview脚本；Root可从apps/web cwd执行现有node + node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port <disposable> --strictPort，先确认端口只属新服务。本轮未启动。

## 验证命令与完成边界

建议实施卡新增 tests/ui/frontend-redesign.cjs，使用既有Playwright安装及fixture方式：一份流程矩阵同时覆盖浏览器和native-shaped fixture；以真实服务隔离夹具补端到端，不新引入测试框架。关键交互为新建项目/首次配置、旧项目打开、session新建/接管/发送/暂停/恢复/取消、goal/task详情、ProfileDraft冲突、资源恢复、设备配对撤销、产物预览、离线恢复与多尺寸键盘操作。

精确已知命令（仅建议，全部 NOT_RUN）：
- cwd=apps/web: npm run build
- cwd=repo: node --test tests/ui/desktop/w13-react.test.js
- cwd=repo: node --test tests/ui/desktop/http-wire-boundary.test.mjs tests/ui/desktop/desktop-management-boundary.test.mjs tests/ui/desktop/coding-authorization-boundary.test.mjs （只有该相关路径实际变更时扩展）
- cwd=repo: python -B -X utf8 tests/ui/w1303/preview_run.py （真实临时Core/Electron产物回归；跑前核对其toolchain pin和隔离环境）
- cwd=repo: python -B -X utf8 tests/ui/w1303/check.py （综合观察会跑matrix/preview/workspace/permission/accessibility/transcript，非每次CSS改动都重跑；不能当正式接受）
- cwd=repo: python -B -X utf8 ops/ci/ui.py / ops/ci/build.py 为现有CI入口引用；未展开全部参数和副作用，Root按现行登记命令使用，不能直接视作本轮已验证。

交付需要新版真实组件截图/DOM/控制台结果，以及真实隔离fixture操作记录。build成功、mock视觉通过、native边界通过、独立审查、父任务正式接受分别记录。当前只完成源码映射。

## 查询与证据

first intake + 6 query groups，总计7组，原始stdout、recipes、nativeexit在同目录。group01记忆registry缺失（未使用记忆结论）；group02根package.json不存在导致中止，.github不存在；后续精确路径完成。group02扫描AGENTS文件名范围过宽、group04验证文件名清单误含qualification目录，仅列文件名、没有读取其源码内容，保留诊断，不据此扩大授权或作结论。group03/04/05终端展示截断，但完整输出已保存raw。

没有读取指定Input #3历史revalidation内容；当前源码为主要证据。Main commit来自scope声明，未运行Git独立验证。Root接手前需按当前Main重新冻结哈希，尤其Source43并行施工状态。本目录manifest只表达读取时文件hash，不签署源未变化或任务接受。

