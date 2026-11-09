# CP552 Desktop complete tree 独立复核准备

状态：PREPARED_WAITING_FOR_FROZEN_CANDIDATE。本次仅读scope，没有读取builder中途源码，没有执行其测试/构建，GUI/Core运行0，formal增量0。此前REVIEW-*保持原样。

范围已足以处理D01–D03，未发现需要现在新增生产源码路径的缺口。以下是现有三项发现的具体复核方式，不新增永久矩阵或新的功能要求。

| 既有发现 | 冻结后核验内容 | 有限证据/边界 |
|---|---|---|
| D01 完整development资源 | 精确base+7path diff；旧build-validator及management/native原样；new builder/launcher/source/tool/Go实际编译依赖均入manifest；Core、真实verifier及manifest、Mu worker/build metadata/node、React与Core cwd migrations/contracts完整；外部Mu5083公共vendor和Electron引用显式标来源并绑定实际使用文件。 | 独立核验输入/输出文件hash与before/after，运行冻结focused bundle tests；检查缺失/tamper/tool/source drift失败门槛。Electron引用不能只锁exe而忽略实际加载DLL/pak/resources依赖。暂不运行Electron/Core验证。 |
| D02 隔离launcher | argv数组固定Electron、repo-shapedcwd；new fresh state与data/discovery/userData/资源绝对路径；逐组件regular/realpath/alias与越界校验；Windows env大小写折叠、重复key/collision，清除全部大小写形式RESEARCHOS_/ROS_DESKTOP_/NODE_OPTIONS/NODE_PATH/ELECTRON注入并显式赋值；缓存/temp归own state。 | focused tests应含小写/混合大小写注入、缺失/tamper、alias/逸出、已有state、重复启动。dry-run必须无state创建无spawn；失败在实际spawn前。测试只用自己的新夹具与注入fake spawn。 |
| D03 真实成功判据 | main仅smoke/非敏感identity/report小改；成功要求renderer+management READY+nativeProbe.ok；ownedCore来自当前management已核验PID/creation/image/host ID，不来自legacy ensureCore.spawns；shutdown_confirmed取成功shutdown返回且绑定同一owned identity。 | exact frozen smoke正反分支：BROKEN、无probe、probe失败、错误identity、shutdown拒绝/未退出不得成功。保留unknown child/异常处理；mock/source结果不能算真实Core退出。后续真实ownednative运行需要Root另行scope。 |

冻结输入到齐后才复制自有精确源码snapshot，核验commit/tree/base/diff7/source manifest与作者seal，记录全部补充测试hash及recipe。独立测试只针对上表与受影响最近邻；不复测C57，不读旧业务数据/凭据/进程/ACL，不改变Main/作者worktree或卡状态。若发现Source阻断及时回Root，由原builder处理，独立reviewer不修作者源码。

当前诊断：scope原始读取001 native0；002仅准备文档与哈希核对。没有候选测试失败或资源运行结果可报告。准备完成后等待Root发冻结候选，不轮询mutable源码。
