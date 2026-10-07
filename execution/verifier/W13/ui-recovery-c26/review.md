# C26 UI recovery 独立范围审查

结论：`PASS_BOUNDED_SOURCE_WITH_PARTIAL_BROWSER_EVIDENCE`。这接受的是本次源码边界及公开证据的准确归类，不是完整 C26 验收。完整 C26 保持 `NOT_ACCEPTED`，五次原始 runner 保持 `exit 1 / FAIL`，不升级正式命令、验收或运行权限。

## 冻结与哈希

源提交 `11501378b116663a9652c82058809a7fba76553d`；证据提交 `6993ce4e831ef98b4c577aef7d43ec64350d29cb`。后者相对前者只新增本次 evidence 目录内 65 个文件。输入 `manifest.json` 的 SHA-256 为 `b69cefa724c29f7cecbec024326e795c6ceb42443e0fe6ffe2d2ec1495c842e5`。

独立核对 292 个冻结输入（2 个产品改动文件、7 个测试入口文件及其余已登记输入）与 source commit；64 个证据文件与 manifest/evidence commit，全部匹配。五次 before HEAD、两产品文件的历史 Git 字节、child report hash、原始 build/browser 文件绑定和已完成检查计数全部一致。详情见 `binding-audit.json`；审计脚本仅读取列明的公开文件和 Git 对象，没有执行产品或测试 helper。

`api.js` / `hooks.js` 从产品提交 `4d3654b27d0e5e8c0b33537daf626179eafe68b0` 至冻结源提交及全部五轮运行字节一致。SHA-256 分别为 `f133e1817696d0a873e705a19bd42fe504793343a2e1b48a9ae651511ad0d145` 和 `0e564a17369cf659d65d3dfffe85db759c53cf2d60d45103c9eb1124a415ef5c`。

## 产品源码审查

此前完整调用链预审见 `preliminary.md`，本轮确认源字节未变。45 秒无字节 watchdog 覆盖等待响应头和读取流，heartbeat 只更新传输活动时间；onOpen 不更新业务 lastSync。超过 20 秒的 wall-clock tick 间隔、visible、persisted pageshow 与 resume 会使旧 transport 失效并重新取当前项目快照。snapshot、event、onOpen 及读取后解析都有连接 abort 防护，清理路径取消 reader、释放锁、清 timer 和监听。

在本次改动边界内没有发现阻断产品缺陷。45 秒是阈值，执行依赖浏览器调度；不能解释成页面实际暂停期间也有独立实时执行能力。同项目迟到 callback 的防护目前由源码支持，后续真实恢复测试未完成。

## 可接受的有限观察

冻结 composite 的 11 个位置划分准确：8 项有限观察、1 项降级观察、2 项未验证。原始 run 中出现完成检查，不改变该 run 的整体 FAIL。

| 范围 | 本次接受的结论 |
| --- | --- |
| 既有登录、项目、投影、通知、精确成果链 | 第二轮已执行的相关检查可按相同产品字节复用；没有重新运行完整页面或状态矩阵 |
| event 重放、foreign/gap/410、offline、跨项目 | 既有运行记录可复用；最终把旧 helper 的 5 秒改为最多 15 秒等待的改动明确 `NOT_RUN` |
| 正常 idle | 47.009 秒内 3 次真实服务 heartbeat，opens=1、GET=28 均不变，进度文本不变 |
| 显式静默流 | 两轮分别于 45,009 ms 中止，lastSync 年龄 46,220 / 46,229 ms，重新取快照后 UI/服务水位 1→2 |
| 旧 freeze 项 | 只证明 CDP frozen/active 请求后水位追平，不证明实际冻结 |
| 真实 freeze / resume / 同项目迟到帧 | `NOT_VERIFIED`；22 秒请求期间 timer 仍约每 5 秒运行，lifecycle=[]，没有建立停顿前提 |
| 最终无未处理异常检查 | 失败的 phase 未走到该终点，`NOT_VERIFIED` |

静默流是一次显式注入的 ReadableStream，浏览器仍 online、服务产生真实 Requirement；不是物理网络故障或 OS sleep。该分支的迟到帧来自外项目，不能单凭它证明同项目 abort fence。第二次 freshness 在约 37 秒观察后仍未发生第二次 abort，既未达到 45 秒阈值又无超过 20 秒的 timer gap，因此不能据此判为产品恢复缺陷。

## 未升级事项

`full_phase_after_final_test_change=NOT_RUN`；真实浏览器冻结、physical OS sleep、physical phone 未验证；`test.ui.recovery` 未在正式 command registry 绑定。上游 Chromium/Playwright 机制解释是作者给出的假说依据，本次接受结论只依赖本地保存的 timer/lifecycle 记录，不额外认证该上游因果解释。

本独立审查没有执行新 browser/test/native/provider/private/helper，也没有读取或删除两个 policy 阻止清理的 ignored `__pycache__`。旧证据、产品源码、canonical 与 spec 未改写；缓存清理限制保持单独记录。所有写入仅位于本 verifier 目录，报告冻结后停止写入。
