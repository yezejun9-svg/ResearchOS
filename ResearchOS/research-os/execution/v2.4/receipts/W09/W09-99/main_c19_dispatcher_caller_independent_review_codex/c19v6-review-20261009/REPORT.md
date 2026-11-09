v6 独立源码复审：ACCEPTED_SOURCE_ONLY。

v4 三项阻断与 v5 静态资源连续性阻断均已关闭。八个封存 A refs 返回并进入最终持锁集合，expected_dispatch 只取 A；独立原 AST 时序反例中 dispatcher/toolchain 在后续变成 B 时均触发 CONFLICTING_PIN，在启动前停止。八项晚到 B 和原 A 去重保留也已独立验证。

Canon Owner/Worker 活动租约、独审身份及四个精确 Source refs、Scope 字段和历史版本的反例回归通过。历史 CP369 档案与未来 CP370 当前向量仍分离；固定模式、TEMP/TMP、命令及进程闭合路径沿已核验的不变源码保留。

决定仅接受本次 Source，不构成 CP370 实际登记、dispatcher 执行或正式验收。没有 Native/dispatcher/provider 调用、Source/Main/Canon 修改或新原错误。原 987/991 保留两条 observed-only；未知原始字节不重建。SourceGuard finally closed、retained=0。
