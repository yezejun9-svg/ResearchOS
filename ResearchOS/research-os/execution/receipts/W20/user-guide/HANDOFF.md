# W20 user guide — frozen documentation handoff

`EXECUTED_PENDING_INDEPENDENT_REVIEW`。仅新增使用指南和本目录回执；未改 README、产品、API、规格、依赖或原截图。

指南源码提交：`8d8c0db8506f1e531916559c2b29b84606387e68`。
事实基线：`a418d503f29646f62010905f9dc9338630aa0108`。
授权：`b411ead` 登记的 `W20-user-guide-v1`；主 Agent 持有 README 链接及重打包。

`docs/installation/user-guide.md` 覆盖 11 个真实页面、入口与操作、角色前置、结果提交和独立验收的区别、来源缺口、未知费用、断线恢复、封存版本、双方草稿与导出，以及现有双主题和窄屏抽屉。特别核实：资源登记只检查请求状态与引用有效性，不能声称外部恢复已证明；背景候选封存还需额外角色；新想法与背景草稿的保存寿命不同；RUN_RESULT 不是当前页面的 Task 状态值。

机械检查实际退出码 `0`，输出 `GUIDE_PAGES=11 LINKS=51 SCREENSHOTS=45 MISSING=0`。`verify_links.ps1` 只读源码及既有文件、记录哈希和 PNG 元数据，生成 `link-check.json`；没有运行浏览器或产品测试。21 个事实来源文件与基线 Git blob 相同；51 个相对文件链接存在，45 张既有 PNG 均匹配原报告或 C26 清单哈希。当前 README 链接目标哈希固定于本事实基线；整合者随后修改 README 时，该历史哈希不代表最终包中 README 的哈希。

截图只是完整源码仓库中的外部证据。分发包不复制原图或完整 execution；指南明确需要在原源码仓库打开相对证据链接。项目入口没有现成独立截图（表格四个主题/尺寸单元留缺），工作台缺桌面深色图；未新拍或用设计参考替代。历史截图版本与当前事实基线不同，并已明示。C26 整轮失败、真实冻结/真实睡眠和真实手机未接受等限制保留。

整合顺序：指南源码提交，然后本目录证据提交。主 Agent 再串行添加 README 入口与生成最终分发包；相同 binary/script 的既有 fixture 证据是否复用由主 Agent按哈希判定，本轮没有执行这些流程。

`facts.json` 提供页面/操作/来源映射和实际命令结果；`link-check.json` 提供逐目标路径、SHA256、PNG 尺寸、原回执版本；`manifest.json` 覆盖本指南和本目录证据文件（自身除外）。本轮无新依赖、缓存或临时文件，无 cleanup 操作。最终结论交独立文档审查者。
