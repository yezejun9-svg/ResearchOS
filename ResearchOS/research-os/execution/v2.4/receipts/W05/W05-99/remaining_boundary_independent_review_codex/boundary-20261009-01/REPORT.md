W05 最小剩余边界已明确，当前仍为 COMPONENT_PARTIAL，正式验收增量为 0。

1. dev13 的 13 PASS 和 H20 已独审的原收据可按原范围复用，不重跑。当前 A21 测试写入 PUBLIC_FIXTURE 程序字节，未证明真实21/22发布程序。
2. 新增一个连续公共20→21→22→23→24链；每段使用上一段真实输出，保存每段schema、ledger、typed rows、快照与返回/落盘报告一致性。现有23 fixture直接调用内部迁移，不是连续公共链。
3. 补 A21 公共入口的实际DDL后、发布前失败；必须有达到阶段的证据，验证源不变、目标/成功报告未发布、临时候选清理，已生成的认证快照按合同保留。
4. 复用现有 typed 六父例/八叶例源码与本地 synthetic TLS 资源，新运行由 Root 对账每个子代的 binary/PID/FILETIME/父子关系/raw/exit/Job。dev13 未选择这些父例，现有 helper 子代PID/exit仍为空。
5. 这些组件通过后仍需独立对照 W05-G01/G02/H08/P01/U02 与 A04-01..06。C11/C15 的冻结最终负责人是 W12，不能混作W05正式全例。

完整精确refs、源码行段、最小实施/验证断言、可复用资源与限制见 review.json。本次只写本 review namespace，SourceGuard已closed、retained_handles=0；没有新Native/Go/model运行、没有自验收。
