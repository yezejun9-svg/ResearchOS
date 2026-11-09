# 诊断与证据边界

本任务 after-intake 共11组有限读取/官方查询（R03-R10、W01-W03），上限12。R01/R02为intake；F01/F02仅生成与封存ownE交付，不是新增原系统查询。

- R01 FAILED：PowerShell中Get-FileHash不可用，未读AGENTS/scope内容；完整stderr与exit1保留。
- R02 SUCCESS：.NET SHA256确认scope精确hash后读取AGENTS/scope；D:/作品集/ResearchOS/AGENTS.md不存在已记MISSING，repo AGENTS存在。
- R03 SUCCESS：12个冻结输入bytes/hash全部匹配；资源/backup报告读取。
- R04/R05 SUCCESS_WITH_DISPLAY_TRUNCATION：完整raw保留；后续只窄读必要57路径/B语义，不将未展示尾部当全面审阅。
- R06 SUCCESS：manifest pin核对B兼容与部署文档，精确Source定位。
- R07 SUCCESS_WITH_DIAGNOSTIC：Python非法转义SyntaxWarning原样保留；rg native exit0，包含较多测试命中，不能当生产调用闭合。完整raw保留。其后对CLI CommandChecker做精确source读回。
- R08/R09 SUCCESS：精确D根/作品集/C home完整ACL与source读回；未触碰实际OS权限。R08显示截断；R09窄输出收敛关键ACL。
- R10 SUCCESS_WITH_DISPLAY_TRUNCATION：B75 frozen raw与CP511 constraints哈希匹配；非当前B-r2接受。关键private API在输出可见，完整raw retained。
- W01/W02/W03：预写请求后访问Microsoft官方资料；raw tool结果完整封存。W03查询过滤词写作site.learn.microsoft.com而非site:learn.microsoft.com，结果含第三方；只使用Microsoft primary结果，未采信第三方。GetApplicationRestartSettings多次打开有展示截断，不从空摘要作结论。
- F01：生成JSON、验证57唯一路径及权限/接受字段；不是产品测试。
- F02：验证own artifacts、冻结输入和完整命令索引/manifest；不是Source/native/实际接受。

Native能力缺口：same-handle身份/ACL reader、runtime restart reader、精确PE/script fence、dense deny和owner有效权限、双主体privileged恢复、跨boot持久保护。上述都可纳入已列Source/fixture工作；本次实现或执行次数均为0。

实际资源缺口：B-r2独立接受、Root精确API/组合基线、shared祖先授权和逐对象preimage/恢复、不同SID恢复主体、实际supported-set映像与动态注册闭合、Root online backup资格与实际usable restore、明确后续FullRestart窗口。当前Medium token和公开metadata不替代任何一项。

未执行：原DB/API/密钥/model/provider/进程查询、ACL写、service变更、启动/终止/Restart、Source/test/helper实现、保护Canary私有访问。无skip伪PASS，无历史计数重置。日志本身Python脚本仅处理文件证据，不是产品native helper。

所有ownE脚本/recipes/raw/报告均是复核所需证据，保留；未产生需清理的临时文件。Root独占共享状态，本作者未编辑checkpoint/ownership/handoff。

