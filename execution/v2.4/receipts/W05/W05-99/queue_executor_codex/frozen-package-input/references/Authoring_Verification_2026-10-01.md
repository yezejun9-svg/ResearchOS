# v2.4 编制验证与限制

本记录仅证明规格与配套工具检查，不是产品通过。机器细节见[验证记录](Authoring_Verification_2026-10-01.json)，最终文件hash校验见[PACKAGE_VALIDATION](../PACKAGE_VALIDATION.json)。

71张卡、22父任务、42正式用例；93父门与63用例命令组合已精确绑定。23本地方法、14事件、106正负协议样例与产品/UI合同对齐。独立复核确认本轮列出的P1规格阻塞已修正。task_packet与Qoder工具共8项自检通过；伪接受、坏hash、非法ID、缺模型和超时进程树回收有检查。

本机Qoder CLI 1.1.64的CheckOnly通过，目录含精确Qwen3.8-Flash。两次禁用全部Agent工具/MCP的附件探针均正常返回；第一次发现路径和引导文字易误读，修订后第二次正确识别绝对路径、首卡、所需读取和完整完成门。第二次把“无前置依赖”输出为null而非[]，因此严格输出一致性记PARTIAL，未伪称全绿。实际施工的依赖来自机器plan/task_packet，不由模型从自然语言重建。见[探针详情](Qoder_Attachment_Probe_2026-10-01.json)。宿主提示一个skill config warning，但未阻断推理；未为此修改全局skills。

只读附件探针没有执行文件读取工具、施工/goal或任何ResearchOS产品操作。模型后端内部标识qfmodel、空usage/0成本字段不证明供应商实际模型身份或真实费用；只确认本次请求使用CLI目录中的指定模型路由并取得响应。

桌面离线预览做过8项Chrome DOM自检及1440px浅色、390/320px深色布局检查；它仍是示例交互。真实Windows壳、provider、打包、手机、独立holdout和8小时产品运行均待实施阶段验证。

已重查原research-os HEAD、Git改动列表、观察文件hash，以及旧v2.3 manifest和全部登记文件hash，均未改变。

自动审批拒绝了浏览器验证临时目录的递归清理，以及随后仅删除明确生成文件的较小操作，理由均为blocked by policy。已停止清理，关联Chrome进程只读确认0；残留绝对路径见机器记录。该残留不在交付包内。

打包后对工作区内 .spec-authoring 和新包 tools/__pycache__ 的清理也被自动审批以blocked by policy拒绝；已停止，没有改用其他删除方式。两处均未进入ZIP；绝对路径见机器记录。
