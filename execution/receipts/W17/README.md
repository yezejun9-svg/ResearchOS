# W17 开发施工回执

最终源代码 `14a332f`，实现链 `47dc4b7 → eeea38b → 8e5c221 → 0411d2a → 14a332f`。这是开发执行回执，独立审查未由施工者签发；没有启用公网或真实手机验收。

- `development-current/report.json` 精确汇总测试命令、结果、原始日志哈希和正式门缺口。
- `development-current/go-tests.jsonl` 是施工中的全量诊断：206 个 test/subtest 通过，2 个失败。coverage owner 登记遗漏已修；原 W10 native 测试缺 `RESEARCHOS_GO` 已用锁定工具补齐。保留原 FAIL，不写成全量最终通过。
- `development-current/targeted-after-fix.jsonl` 重跑两个失败和 W17，全部通过。没有因此重复全套。
- `development-current/final-focused.jsonl` 针对最终设备 role 响应头小改，重验 W17、gateway、coverage，全部通过。
- `browser/20260930T130555Z/report.json` 是最终当前源的实际双 Chromium 流程：复制链接、真实配对、只读权限提示、窄屏抽屉、离线恢复、服务端授权/降级同步、撤销后清会话并显示重新配对。业务 API 和 SQLite 真实，polling 元信息注入为明确夹具。源哈希保持不变、浏览器异常 0、HTTP 负例和截图均保留。
- 之前三个 browser 回执保留溯源。`20260930T125949Z` 因 Windows subprocess 默认 GBK 解码构建输出失败；随后显式 UTF-8 修复。`125959Z` 和 `130429Z` 成功但被最新包含动态权限/撤销 UX 的回执替代。

截图和日志不含实际凭据。一次性 URL 的 fragment 只存在测试进程变量/浏览器内存，不写回执。临时 credential、SQLite、控制进程已清理；项目依赖 node_modules junction 为可复现构建保留。

未完成：真实跨网手机、公信 TLS 与实际 edge forwarded-header 行为（A10/A11）；完整 C02 共享/检索/ContextBundle 矩阵；C22 独立 OS 主体对文件、缓存、搜索、备份、进程、正式受保护服务的完整隔离验收。本轮 C22 只读取公开假 canary 元数据，不接触正式 holdout，不改变 W11 资格。

下一步入口审查与候选命令见 `ops/remote_access/README.md`。Quick Tunnel 不能作为长期地址保证；本轮没有新账户、域名、VPS 修改或对外公开部署。
