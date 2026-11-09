# Desktop managed qualification client repair-v2 独立审查

**ACCEPT — SOURCE_AND_FIXTURE_ONLY**。候选 `956225e98e17c1d9e15d4787fe4dd366a687d2e4`，累计8文件、修复增量5文件。本轮未发现阻断项。

原 W05-DMQ-CLIENT-001 与 002 均关闭：真实 TTL 过期且无 CONFIRM/未决命令时可以在会话切换后准备新请求，并保留旧标识；主机切换后当前摘要和页面撤销旧授权，原主机回来仍须重新 STATUS。两项有实际 Chromium DOM 复测、原私有帧及截图。

6501/6501 绑定检查（6435完整构建输入及最终源码/Git/模块/UI资产）、11/11 bound 管理边界、7/7 新独立因果用例、2/2 DOM、23/23 UI-v5回归通过。未将作者声称的12项替代本轮实际11项。

原拒绝报告和反例保持冻结；旧零模型 Core 耦合与缺资源 smoke 用原清单复核引用，没有重跑，也没有升级证据层级。新构建未独立重建；本轮没有启动 Core/模型或完整 Electron。正常安装、真实资格调用、成功后 UNKNOWN 账本安全退出仍未接受；SOURCE+FIXTURE 接受不等于生产或正式验收。

0 actual model / external / public tunnel，formal/parent +0。候选和作者清单未改。新 Vite 缓存定向删除被自动审批审查 `blocked by policy` 拒绝，保留并排除清单，没有改用其他方式删除。
