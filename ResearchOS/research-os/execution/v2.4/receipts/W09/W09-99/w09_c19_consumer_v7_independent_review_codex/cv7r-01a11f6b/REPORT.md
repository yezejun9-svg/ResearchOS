# v7 Consumer Caller 独立 Source 复核

结论：SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE。Source 变更通过，actual 尚未执行；本报告不给予执行授权。formal accepted delta = 0，C19 仍只算一个 formal case。

独立脚本对完整 caller 做九处显式替换的正向构造、完整字节逆向还原和整模块 AST 逆向比对，其他所有函数 AST 不变。独立构造 source.choice、derived consumer contract 和 calling contract，三份完整序列化字节均一致；同时逐项核对作者四份 opcode inverse 的全部旧/新字节。

五个目录绑定匹配 r3 v7 candidate、producer、producer temp、consumer output 和 consumer profile。六个 overlays 中只有 closure 换成已独立接受的 v7；Source21 名单保持不变并含 closure。CP365/OW169 只保留为历史来源；当前四份 canonical 未读取、未锁定、未写入。新 vector 仍只有 schema/checkpoint_revision/refs 三个键；CP 是正整数且与精确 vector 中 checkpoint 内容一致，OW 是精确 pinned path_ownership 内容中的正整数，bool 不通过。不增加 ownership_revision vector 键，不把未来 revision 写死为 366/170。纯 predicate 控制覆盖 CP1、365、366、367、大整数、类型、零负数、缺字段和多字段。

producer pre-run、Root scope 和请求必须引用同一个精确 vector。完整新 packet/report/tool-run、Source21、raw copy mapping、两份不同 route 的新非作者 ModeDecision 与同一独立 review、Root scope 精确 refs 的原有约束均未变。新路径与 run/source 绑定拒绝旧 v6 packet 的直接复用；任何未来新 producer 的真实完整性与 ModeDecision 资格必须另行审查，本次未虚构这些材料。

两路固定为 test.research.fixture 与 test.retrieval；每路 3 formal assertion IDs、5 native IDs，formal dispatcher/registry/Main adoption 均未执行。caller 中成功闭合要求两个 owned jobs 都关闭，所有 acquired guards 在 finally 清理。原环境白名单、producer TEMP/TMP、禁止 producer 自动重跑等行为不变。

验证：176 个独立控制通过，103 个有限精确输入通过真实 SourceReadGuard 持有期间哈希检查；全部 acquired handles 已释放，retained=0。Python 与 outer exit 均为 0。未运行 Source 构造脚本、actual caller、component consumer、Go、SQL、Git、API 或模型；只运行独立静态/内存 predicate review 和真实只读 guard。Source 作者的 148 checks 与 81 inputs 已核对，未把作者结果当成独立实跑。

本轮机械失败 937：首次只读 Get-Content 的路径漏 research-os，outer 1，Python/native/model exit 均 NULL。原始命令和结果另存 immutable failure-origin.937.original-tool-io.json；随后使用精确路径继续，该失败不因最终通过而清除。原始 review 工具 IO 已封存。

STOP / FINAL。Root 可据现有目标决定下一步登记与实跑；需要新的 producer independent qualification、ModeDecision/common review 和 exact Root consumer scope。本 Source 判定不替代 actual 结果，也不变更四份 canonical。

