# Installer P1a revision01 — NEEDS_REVISION

候选 `60d2787e15e4a87b291f08c853d3738600c83734` / tree `bb0ace8936b34a45b5de03c845250b3a18c37417` 的 exact4 clean 与源码摘要已核对。原 **R1–R3 已按静态范围复验关闭**，但新增 **R4：构建工具固定绑定本轮临时 scope**，本轮仍不批准整合。正式增量 **0**。

R1 改为同目录 `MoveFileW` 不覆盖提交。实际 Windows 成功、已有目标、提交前目标出现均通过；独立探针还确认拒绝时 temp 和目标字节均保留，315 字符 canonical root 提交成功。这里只证明 marker publication，不代表安装事务、维护门或掉电恢复合格。

R2 的 dotdot、overlap、junction 边界测试通过；源码现已在写入前验证 canonical 路径、现存祖先 reparse、授权根直属子目录、互不重叠和 create-new。R3 仅在独占 mkdir 后记录目录身份，失败回执以 `xb` 写入。已有目录保持不变、首条失败不被覆盖、foreign inode 拒绝均有本轮证据。

**P1A-R4 · P2（阻止本轮接受）**：`build.py:24–25,163–169` 把 cp570 的绝对文件路径和摘要写死。相同 scope 字节换路径，或提供新授权根的后续 scope，都会报 `revision scope differs from approved exact4 authority`。CLI 只有 `--scope`；内部 `authorized_roots` 测试注入不构成新的受信 scope CLI 通道。因此该工具离开本轮目录、历史回执迁移或进入下一次授权构建时就不能工作。

最小后续只需修改 `build.py` 与对应 Python 测试：由已授权调用方显式提供 scope 和外部预期摘要，先核对原始字节，再验证 scope 合同/worktree/授权根；继续保留 R2/R3 全部边界。禁止以“对任意输入自算摘要”代替授权。原 P1a 的 frozen source marker/product provenance 固定绑定可继续保留。

新增测试应证明两份不同且显式受信的 scope 无需改源码即可选择各自授权根；错摘要、空摘要、畸形 scope 在写入前拒绝；dotdot/reparse/overlap/preexisting receipt 仍拒绝。

本轮只跑 5 个 Python 回归测试、针对性的 Go publication 测试和新增小探针，没有重复全量 relocation。payload manifest 摘要未变，新 finalizer hash 与作者回执相符；新生产 finalizer 未独立重编译，Go publication 源码已独立编译执行。没有产品原生启动、安装、registry、迁移、共享状态修改或正式验收。先前 symlink 权限 SKIP 仍保留，不据当前 junction PASS 替代。

旧封卷保持原摘要。scratch 按 Root 要求保留，没有重试先前被拒绝的清理。证据、命令和完整输出见 `EVIDENCE-MANIFEST.json`。
