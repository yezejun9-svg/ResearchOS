# CP518 官方启动入口只读资源闭合

结论：**已完成本轮允许的一次性资源采集；既定 OFFICIAL_ENTRY_FILE_DACL_FENCE_V1 对两套固定包的专属文件仍有潜在适用性，但完整当前官方入口覆盖与跨重启防替换尚未成立，不能由本报告直接签发 Source C。** 这不是永久机制不可能，也没有转向新机制。actual_authority=false，Source C authority=false，formal_increment=0。

本报告只声明实际读到的资源。Source/native fixture、实际部署和用户完整Restart证据尚不存在，不能倒置为本轮采集必须先具备的条件。

## 已闭合的事实

| 资源 | 本轮实际结果 | 能说明什么 |
|---|---|---|
| 两个已知包 | normal-coding-profile-c8b7adab-20261014 与 normal-verifier-replacement-4f4023-20261015 各58文件，合计116重新SHA256 | 当前公开文件字节；不是loaded image或完整入口集合 |
| 当前普通启动链 | CP494 launch.json：exact Electron + current package apps/desktop，same DataRoot/userData，smoke=false；launch_and_wait.py hash743b7014792f9b0904ae134acdc4fa3fdc77076c611fdc0f002a25def85ffeb0 | 这是已封存实际启动记录与当前源码，不是新读ProcessCommandLine |
| Desktop专属入口 | 两包package.json均指向main/main.js；main.js hash1a55e7f9f0afaeccb5dae268b5dbca987092addbab70c9bac367fc46bb00ced1；management spawn exact Core | 可列出脚本读/PE执行的具体候选阻断点；只禁止launcher快捷方式不够 |
| 精确文件/祖先 | 67对象GetItem/GetAcl/fsutil queryfileid均成功，未发现reparse；公共文件另读SHA与hardlink list | 分次open/read/close辅助事实；没有same-handle连续性、持久guard、lease或native Wait |
| 原root/DB/lock | file IDs分别0x...09000000458114、0x...09000000458116、0x...09000000458115；DB无内容读取、无hash | 仅原数据对象元数据；不能据此声称一致性backup或当前quiet |
| 平台/token | Windows 11家庭版中文版10.0.26200 x64；SID末尾1001；Medium IL、Administrators deny-only、Admin role=false | 当前观察器不是已提升管理部署主体；native elevation type没有自行PInvoke读取 |
| 卷 | C/D经CIM均NTFS，serial F830534F / EE413C31；fsutil volumeinfo两次AccessDenied exit1 | fsutil失败保留；CIM是辅助卷元数据，不拼接冒充同句柄volume identity |
| 指定注册表 | HKCU/HKLM 32/64 Run/RunOnce、Classes open-command、Winlogon Userinit/Shell、ActiveSetup逐范围0产品匹配 | 仅所查范围/过滤条件内零匹配；不等于无动态AppRestart |
| Task/shortcut | 211 tasks零产品匹配；当前/公共Desktop、StartMenu、Startup共6范围零匹配 | 不触发任务、不保存快捷方式；重叠目录计数不当唯一快捷方式总数 |
| Service | 312 services中ResearchOSVerifierCanary匹配；registry ImagePath指向C:\ProgramData\ResearchOSVerifierCanary\broker.exe，Start=3，独立virtual account | 真正已注册的独立保护验证服务，不是当前package runtime-verifier.exe，也不是release_host一次性fixture |

全部逐目标ID/hash/完整SDDL保存在file-ancestor-metadata.json；file-ancestor-compact.json只是有选择的ACE摘要，不能替代完整AccessCheck。C包链有大量历史显式/继承deny ACE，完整原始描述符必须保留，不能为了围栏用一个“干净allowlist”覆盖掉既有隔离规则。

## 入口分类与候选适用性

officialsurfaces.json逐条列出S01–S14和历史H01。现行普通launcher会明确清除Core/verifier/runtime-assets override和smoke环境变量，实际CP494记录也使用默认包路径。Desktop源码本身仍支持这些override，所以“这次没有override”不能推出所有正常开发/维护启动都没有替代路径。

两包的main/main.js和researchos-control.exe是已定位的产品专属文件，可以进入既定机制的后续Source/fixture。共享Electron不能整机禁止；其D盘路径与上层目录存在Authenticated Users Modify，单靠包脚本hash或一次句柄保护不能证明重启期间解释器/祖先不被替换。原DataRoot也在这条D盘祖先链内。本轮没有尝试替换，不声称已被攻击；这是实际ACL与持久信任前提的缺口。

C用户目录与包链主要允许operator/System/Admin写，其他隔离SID deny规则密集；仍不能把operator-owner的WRITE_DAC和普通文件可写性当成已部署不可撤销围栏。未来若采用可信same-SID操作员范围，须保持完整现有安全合同，明确普通官方更新/重建/再部署被冻结，不能顺便把恶意任意同SID程序列为无限证明义务。实际普通支持入口若动态未映射，则只把该入口记UNKNOWN并阻塞完整边界；不得默认不存在。

CLI与backup有明确官方源码入口，但本范围未提供当前安装映像/launcher映射。不能将源码文件名当实际exe，也不能把所有历史.local fixture扫描成“生产副本”。repo Desktop默认resources/control文件本次返回路径不存在；这只说明该默认位置，不证明其它override未部署。online backup源码契约由Root另行采集，本作者不重复分析。

docs/installation/README明确ops/release build/start与release_host是R1 development/disposable fixture，新空fixture root、无普通LIVE激活、不是SCM生产安装。这些保留为source/fixture入口，不虚构其当前生产运行。cp470更早normal-coding-any-a7ec7ebf只作为历史引用，Root确认非现行启动；本轮没有把它擅自加作第三个当前包。

ResearchOSVerifierCanary则有真实registry与broker.exe，不可因CIM PathName空而遗漏。源码将它固定到ProgramData的受保护验证环境，独立service SID。对交互用户SID做deny并不能据此证明对service SID的启动阻断。当前没有依据把它认作原DataRoot的Core启动器，也没有读取其私有配置/凭据/pipe；其与本恢复边界的相关性应由Root按既有接受合同分类，不能由本作者自动停服务或扩围栏。

## 有限剩余项，不开启新架构循环

1. 一个已接受的精确readonly native identity helper：同句柄volume+128-bit file ID、最终路径、no-reparse/ACL/ancestor连续性。现有fsutil能给ID文本，但不能升级为该能力。输入中未提供这样一个独立接受helper；本轮没有编写/执行临时Go/C#/PInvoke补探针。
2. Root冻结当前支持的官方launcher/直启/维护集合，决定source-only CLI/backup/override分支是否属于本次允许原root运行的集合；属于则需要具体映像/路径，不属于保留来源与排除理由。不是证明任意用户复制的所有二进制。
3. runtime AppRestart状态仍UNKNOWN。目标first-party源码没有匹配RegisterApplicationRestart/setLoginItemSettings/app.relaunch调用，但不能代表Electron/runtime/OS无登记。需要精确受审reader或以后fixture证明重启恢复argv仍必经冻结产品文件。
4. 管理部署/恢复主体与D盘祖先持续防替换需明确；现有普通token及开放祖先不能当成已经具备。不得隐式修改D:\、作品集或用户home共享ACL，也不得沿用尚未接受STOP/B helper的安全结论。
5. Root的在线backup接口分支独立处理；未来实际可用一致性backup、真实fence部署读回与独立接受是arm前门槛。当前不要求它们已经实现，也不询问用户Restart。

上述缺口以pending-resources-and-toolgaps.json为准。资源采集完成不等于设计接受或Source权限；没有实际OS权限变更、产品launch/stop/restart、DB/API/model/privatekey操作。

