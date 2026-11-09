# Owned dialog Tree 诊断专用控制器

状态 PREPARATION_ONLY_NOT_RUN，待独立源码复核。只在 C 新目录施工；正常04及之前冻结/实际失败不改，不重放 run02，不执行 GUI、helper 入口、UIA、Native、SDK 或模型。

复用已批准04的环境、source/bundle/pwsh pins、Job 外监督约定、原始 UTC deadline parser、真实项目入口及 owned PID/creation/image/discovery/nonce/unique HWND/prompt 约束。此包是独立诊断 profile，必须 diagnostic_only 为真正 bool true，runner 任务预算硬为0；正常04仍预算1且字节未改。

runner 在真实目录选择窗口阶段止步，已物理删除后续工作台/capabilities/harness/task/submit路径。无 probe 文件、工作区文件读取、token 注入、假能力/Task/event 或旧标签 fallback。即使 helper 意外返回 clicked_ok=true，runner 也拒绝，且没有模型后续分支。

helper 仅从已验证 HWND 的 UIAutomation FromHandle 查询 Descendants/ControlType.Tree。记录实际 count，最多16个候选，不过滤/去重/猜selector；每个候选只采ControlType、ProcessId、NativeWindowHandle、ClassName、AutomationId、IsOffscreen、Enabled、BoundingRect及至多96字符Name。属性不可用记录为 unavailable；NaN/Infinity保留为明示字符串。无 TreeItem 导航、Expand、Select、Value、文件或凭据读取；原普通选择函数定义未调用。

Tree count=0时，同次从同 owned HWND EnumChildWindows 采至多32个 handle/class/PID/visible/enabled，不取文本/items/values，不枚举UIA桌面。Win32原有ownership校验使用的固定prompt验证保留。所有采样前后重验dialog。sample结束无条件诊断阻塞，唯一点击分支为重新验证同owned窗口后的标准IDCANCEL；没有任何OK dispatch。ownership/取消不确定则不再点击，Root有界Job负责，不能作为成功。

helper预期exit2、reason DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK、无OK并正常ownedCancel；runner只在完整元数据+对应ownedCancel+app.close完成时exit0，状态 OWNED_DIALOG_TREE_DIAGNOSTIC_CAPTURED_NOT_PRODUCT_ACCEPTED。这只是诊断采样完成，不是产品、目录授权、模型或用户旅程接受。Root仍需exact Job/accounting确认Core全部退出。

为避免旧16K整串正则破坏JSON，本包先限制helper stdout完整UTF8至64KiB，再JSON parse，逐标量脱敏/安全序列化。超限、坏UTF8/JSON、unexpectedOK或Cancel未知都拒绝；不保存未验证原始正文，保留摘要与错误。stderr仍有界脱敏。

本轮19项Node和14项PowerShell纯检查及syntax通过。首轮null Current负例失败和定向修复/raw均保留；没有运行helper body/Add-Type/UIA。Root审定并填写新fresh scope后，才可执行一次实际GUI诊断。先拿本机candidate事实，再决定后续filter，不能从本包猜原因是0还是多个。
