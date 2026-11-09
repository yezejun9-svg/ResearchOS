# v2.4 正式用例资源就绪盘点（只读）

当前快照：checkpoint rev 334，commands rev 39；父任务终卡 ACCEPTED 6/22：W00, W01, W02, W03, W04, W07。冻结42个正式case，当前有效接受0；本报告新增接受0。

Desktop169+Go3 的完整范围已构建，但独立scope复核与真实开发资格结果仍为 NULL；它不能替代42个正式case。B01 当前没有同路由可计费 token/思考输出的严格费用上限证据，只限制需要真实付费模型调用的 LIVE 资格；本机 FIXTURE 可继续。

冻结case模式：{"FIXTURE": 31, "LIVE_SERVICE": 2, "LIVE_WINDOWS": 7, "LIVE_WINDOWS_AND_SERVICE": 2}。非 FIXTURE case：A02, A04, A05, A08, A10, A11, A12, A13, A14, A15, A16。42项逐一的owner、冻结断言、证据和63条精确命令模板见 report.json/formal_cases。

当前命令登记 rev 39；至少一个冻结模板缺少可用精确selector的case：C02, C05, C06, C09, C10, C12, C17, C18, C19, C20, C21, C22, C25, A06, A07, A09, A10, A11, A13, A14, A15, A16。selector存在只说明调度入口，不能证明断言运行、要求的 LIVE 模式或独立签收。

Root 下一次可对当前 plan/state 运行 task_packet.py next，只读得到实际任务包。按同一算法的静态筛选，W05-99（IN_PROGRESS）优先，W09-99（NOT_STARTED）随后；本报告没有调用 task_packet。W09 依赖的 W03/W07 已 ACCEPTED，W09 本地证据索引和 FIXTURE 分支可独立推进。W06、W08、W12 等父任务仍有 W05/W06 依赖，不能越门签收。

正式验收必须执行冻结命令模板并保存原始运行回执、版本/输入、断言结果、独立复核和签收。现有 W04/W07 父门登记与42个正式case当前有效接受0并存，不能以父门文字推断case PASS。LIVE_SERVICE A05 涉及外部来源，不自动等于模型 B01；A08/A13/A14 等实际 provider 调用需各自核费用门。

本盘点只做本机文件读取。没有运行产品、CLI/桌面、浏览器、Go/Node/Git、模型、SDK、task_packet 或正式case，也没有修改canonical。两次本地只读汇总脚本形状假设失败，各有独立 failure-origin 原始回执；不会重试或重置计数。
