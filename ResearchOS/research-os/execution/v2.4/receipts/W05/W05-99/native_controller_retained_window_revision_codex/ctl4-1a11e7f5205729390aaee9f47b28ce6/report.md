# CTL4 retained review window coordination

状态：SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ACTUAL。

相对精确CTL3基准 a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a / 42696，只改三处常量：controller.started case_deadline_seconds 1260→1560；run_owned_observed timeout 1260→1560；serve loop monotonic deadline 1270→1570。文件长度仍为42696 bytes。逐项逆变换恢复旧Source整字节；Python AST也只有三个Constant数值不同，其余节点完全相同。

清理前提精确引用已独立Source接受的CL：HDF def8d9e965e4a3c38fb6082c965ac59bfb199b8c4c986cde3063ac98f11bd269 / 4115；其review HDF 7e0b451fed4eeae20941c285721a8b8f982993fecd8651b4f46b41e6353ae6c6 / 2406。该review明确指出旧inner1260/1270不足以覆盖main20+cleanup4，本包仅修此资源前提。

纯Source时间控制：1200+240=1440 < Go1500 < owned1560 < outer1800，owned1560 < loop1570 < outer1800。Go25分钟、主20分钟、cleanup4分钟、grant4分钟、private broker180秒均保持；outer30分钟是Root运行组合必须继续满足的既有前提，未在此文件中改写。测试只解析候选AST并检查常量关系，不导入或执行controller。

原FrozenInputs、隔离环境、guards、owned PID/native identity、签署/发布/释放的schema和流程全部未改。未启动API、native、SQL、Go、Git或model；未改Main/canonical/旧Source，没有新增机械失败。

Root必须在CTL4获得非作者审查后，为fresh native case生成新的config与FrozenInputs，精确绑定CTL4、相应独立审查和CL编译Source；旧Config继续指向CTL3，不能用这份Source包宣称旧runtime已修复。该时间协调检查不等于native保留窗口已合格；Go全局timeout或外层生命周期异常仍可中断，specific fixture release仍需Root真实检查和显式批准。

