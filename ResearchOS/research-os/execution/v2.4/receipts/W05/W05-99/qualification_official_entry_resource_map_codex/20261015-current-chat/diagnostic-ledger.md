# CP518 命令、诊断与跳过记录

所有shell查询均通过ownE/invoke-readonly.ps1，**每次执行前**先落盘完整recipe、recipe_file、cwd、PowerShell版本及输出encoding；不dump环境变量。wrapper封完整混合stdout/stderr与shell exit；native rg/whoami/fsutil各明确记录真实LASTEXITCODE。初次Q00前用apply_patch建立wrapper与bootstrap脚本，没有先执行查询后补recipe。

分组：Q00 AGENTS+scope，Q01输入hash/两包文件位置，Q02有限source定位，Q03实际activation与启动源码，Q04注册枚举首次失败，Q04D解析诊断，Q04REPAIR/Q04R1保留原脚本并纠正重跑，Q05平台token，Q06精确文件/祖先，Q07实际launcher+精确service registry，Q08release/CLI/当前activation，Q09command registry/116hash/service映像元数据，Q10文档分类+compact ACE。Q11为own产物静态验证，Q12为封存；后两者不新增外部资源探针。

实际失败/不完整项：
- Q04 PowerShell解析缺一个else闭合花括号，exit1，未执行注册查询。原script/command/raw/result保留。Q04D定位，Q04R1使用新的-r1.ps1完成采集；没有覆盖失败原始文件。
- Q05 fsutil fsinfo volumeinfo C:、D:各exit1，Error5 AccessDenied。没提升权限、没重试变更；Q06 CIM读取卷格式/serial并单列为辅助数据。
- Q08 rg误指internal/protectedstore不存在，native exit2；其它指定目录结果保留，不能称完整成功。Q09精确定位到adapters/protectedstore后，Q10只读相关服务源码；无全仓初始化搜索。
- rg exit1在scripts扩展匹配、host/prepared特定关键词、AppRestart匹配中表示限定范围无匹配，并非缺失行为证明。
- Q02、Q06、Q08、Q10工具显示输出截断，own fullraw完整保存。Q06原始数据较大来自目标C包既有大量deny ACE；完整SDDL未压缩删减，另生成compact摘要。
- Q10 repo Desktop默认resources/control四路径找不到；raw保留UNKNOWN_OR_ABSENT和具体ItemNotFound文字，报告只做这些路径不存在判断，不外推其它安装。
- Service CIM返回PathName空/StartName null/StartMode Unknown但name匹配；Q07只读exact registry取得明确ImagePath/ObjectName/Start。没有把CIM空值误标无服务。
- 元数据读取与hash之间无保留句柄，所有ID/hardlink/ACL/volume均不声称原子快照。运行中的DB只GetItem/GetAcl/fsutil元数据，明确未hash/read contents。

隐私/范围：registry/task/service/shortcut只封存ResearchOS/known package匹配项，未封存其它业务注册值；命令字符串redaction函数保留flag与opaque hash（本次匹配数据没有出现需输出的密钥值）。不读ProcessCommandLine、当前业务DB、private service files、host credentials/vault/authority keys，不发HTTP/pipe/model请求，不执行读取到的launcher或source函数。谁ami仅允许的user/groups/priv，不收全环境。

完整性：两个包各58文件全量重hash是当前公开资源映射，不能充抵loaded bytes或所有官方入口。历史normal-coding-any引用与R1 fixtures分类保留。Root并行backup/source修复不受本作者修改；仅NEW ownE写报告、logger、raw与manifest。未修改冻结CP517架构、Source或共享checkpoint，formal0。

没有测试程序/产品探针/围栏/ACL写/启动/终止/重启/部署。所有新方案仍NOT_IMPLEMENTED_NOT_ACCEPTED，需Root审查与后续独立设计接受。

