# 桌面施工入口更正

2026-10-01用户明确：交给桌面端Agent执行。v2.4入口修订2改为Qoder桌面Agent/Goal，取消CLI启动前提；00/08/17/20/21、GOAL_START、construction_host、W00-03及模板hash已同步。71卡/22父任务/42正式用例与产品范围不变。

官方资料链接见20。此轮只修订规格，没有启动桌面或CLI施工，没有新的模型调用。旧Authoring_Verification及Qoder_Attachment_Probe是入口修订前的CLI历史证据，其输入hash不代表当前入口，更不证明桌面运行。旧独立plan审查之后仅变更W00-03宿主核对动作，DAG/写范围/验收门未变；当前静态完整性见PACKAGE_VALIDATION。

之前被拒绝的临时文件清理未再尝试，残留位置仍见原记录；不纳入ZIP。

本地同名嵌套目录为旧版解压副本，保持原样；新版清单、检查和ZIP均排除该目录，避免混入旧CLI入口。
