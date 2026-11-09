# 唯一下一步资源包：既定文件ACL围栏适用性

以下是给Root另行定只读范围的recipe，**本轮均未执行**。采集输出必须绑定时间、host/SID、原scope、完整stdout/stderr/exit；拒绝访问记录UNKNOWN。不要把注册项列表本身当完整证据；结合当前产品支持的官方启动命令清单及实际部署负责人确认，才能声明集合完整。任意用户恶意自写程序不在本候选合同内，官方dev启动器/自动更新器不能因此排除。

## A. 明确文件位置

- 两个包：C:\Users\yqyyds\.codex\researchos-resource-cache\normal-coding-profile-c8b7adab-20261014；C:\Users\yqyyds\.codex\researchos-resource-cache\normal-verifier-replacement-4f4023-20261015。
- 已知通用Electron：D:\作品集\ResearchOS\research-os\apps\desktop\node_modules\electron\dist\electron.exe；其实际argv关联的app目录、package.json main、dist入口、资源control路径必须另行读取。不得直接禁止全局Electron。
- 原DataRoot：D:\作品集\ResearchOS\research-os\.local\live\current-chat-normal-desktop-first-use-20261012\data；DB为该root下researchos.sqlite，只采native metadata，不读业务内容或key。
- 官方命令来源只限package scripts、已知launcher/activation scopes、ops/backup、ops/supervisor/release_host、现有Desktop启动/管理重启调用点；不要全盘grep所有个人脚本。

最小只读命令示例：Get-Content -LiteralPath <已知package.json或launcher> -Raw；Get-FileHash -LiteralPath <每个已定位目标> -Algorithm SHA256；Get-Item -LiteralPath <目标> -Force | Select-Object FullName,Length,Attributes,LinkType,Target；Get-Acl -LiteralPath <目标或每一级祖先> | Select-Object Owner,Sddl。这些文件hash/ACL读取不证明loaded bytes，也不证明权限有效阻断。

## B. 注册与自动启动（仅先读registration，禁止触发）

具体key：HKCU/HKLM SOFTWARE\Microsoft\Windows\CurrentVersion\Run、RunOnce，HKLM SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run、RunOnce；已知产品协议/文件关联HKCU\Software\Classes和HKLM\Software\Classes中的产品确切键；HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit、Shell，以及Active Setup中实际产品登记项。系统全量registration可能有无关内容，Root须仅封存产品匹配项及“已检查范围”，不封存密钥/凭证。

最小命令：Get-ItemProperty -LiteralPath <上述确切Run/RunOnce键>；Get-ScheduledTask | Select-Object TaskPath,TaskName,Actions,Triggers,Principal；Get-CimInstance Win32_Service | Select-Object Name,PathName,StartMode,StartName。产品相关服务再读其HKLM\SYSTEM\CurrentControlSet\Services\<name>及FailureActions/Parameters，禁止start/stop。计划任务发现后只Export-ScheduledTask -TaskName <exact> -TaskPath <exact>到own receipts。

快捷方式位置：当前用户与公共Desktop/Start Menu/Startup（通过[Environment]::GetFolderPath解析）；Get-ChildItem -LiteralPath <exact folder> -Filter *.lnk -File -Recurse；WScript.Shell.CreateShortcut(<existing lnk>).TargetPath/Arguments/WorkingDirectory仅读，不Save、不Run。另读启动恢复/RestartApps实际配置及产品RegisterApplicationRestart调用/argv来源；注册表不存在不能证明无运行期restart注册。所需运行期证据若无法只读确定，标明Source/native fixture需补，不能推定不存在。

## C. native identity/权限边界（Root另立native只读卡）

Get-CimInstance Win32_OperatingSystem | Select-Object Version,BuildNumber,OSArchitecture 只定平台；whoami /user /groups /priv 只定业务/管理token。精确file IDs可用fsutil file queryfileid <exact-path>先作辅助；完整identity须既有已接受readonly helper以CreateFileW(metadata, OPEN_EXISTING, OPEN_REPARSE_POINT|BACKUP_SEMANTICS)和GetFileInformationByHandleEx(FileIdInfo)读取volume+128-bit ID，逐级no-reparse、最终路径和GetSecurityInfo。没有现成接受helper则明确工具缺口，不能临时执行未审native代码。root/DB只元数据；读完释放句柄，不能冒称跨Restartretention。

输出每个目标original descriptor、owner、继承/显式ACE、父目录DELETE_CHILD/WRITE_DAC/WRITE_OWNER、普通业务token与拟管理token的有效权限分析；确认硬链接/alternate paths/可写父级、更新/复制重建行为。静态AccessCheck/描述符分析是实施输入；实际CreateProcess/脚本读取拒绝必须由未来fixture验证。

## D. 包结构与完整性声明

每条surface输出：surface_id、来源（文档/registry/task/service/shortcut/直接命令）、原始argv、工作目录、env根解析、launcher/解释器、new-boot时的产品专属必读/执行文件、file ID/hash、祖先、ACL、普通/管理SID、自动重启/更新路径、为什么无法绕过该文件、维护helper例外。
若任何条目UNKNOWN或不存在专属必经文件，停止：不能把“仅发现两个PID”变成其余入口不存在。部署清单还需冻结新增副本/新launcher注册；准许更新必须使boundary失效并重新review，不能静默替换。

## E. Source前与actual前分界

Source前最小资源包充分条件：A-D完整且每条surface有专属必经文件；管理/恢复主体可行；平台与token明确；在线备份生产接口已识别且其另行接受路径可行。这足以定值现有57路径候选并独立设计review，不要求围栏已实现。
Source后fixture产生：有效权限拒绝、同SID正常入口覆盖、no-delete guard失败、cross-boot readback、partial apply/restore、helper crash、anti-replay。
实际arm前产生：真实安装全入口fence部署读回与非破坏验证、实际可用一致性在线backup、独立接受、恢复包；之后才可能请求用户完整Restart。
若资源反证本机制，则一次性明确不适用；不是继续泛架构循环的入口。

