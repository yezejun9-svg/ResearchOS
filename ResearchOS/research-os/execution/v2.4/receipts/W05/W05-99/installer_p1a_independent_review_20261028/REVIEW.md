# Installer P1a independent review — NEEDS_REVISION

候选 `6cf0457072bdd1d730dae961474d4d885a2cdd1b` 的静态 payload、全量 inventory、跨位置身份和只读 JS loader 复验通过，但源码存在 3 项写入边界缺口，本轮不批准整合。正式增量 **0**。

| Finding | 位置 | 结论与最小修复 |
|---|---|---|
| P1A-R1 · P1 | `finalize/main.go:352–358` | `Lstat` 后的 `os.Rename` 在 Windows 会覆盖已有目标。独立原语测试已复现。这不满足 marker create-new/atomic last。改为同卷、不覆盖目标的原子提交，并测试目标已存在及受控竞争。作者并发免责声明不能替代硬要求。 |
| P1A-R2 · P1 | `build.py:143–149` | `Path.absolute()` 保留 `.local/../../`，词法 `is_relative_to` 为 true，实际 resolved 路径已在 `.local` 外。拒绝非canonical路径，并在任何写入前核对输出/回执的授权根、祖先 reparse 和互相重叠。仅做路径判定复现，未执行越界构建。 |
| P1A-R3 · P2 | `build.py:216–220` | 指向已有回执目录时，build 拒绝 create-new，但异常处理仍向该目录添加 `failed.json`。实际隔离复现已确认。仅在本次成功获得目录所有权后写失败回执；早期拒绝不得写入既有目录。 |

建议修改仅涉及原授权路径中的 `build.py`、`finalize/main.go` 及对应两个测试文件；无需扩展源文件范围。保留本轮失败与原候选证据，修复后用新提交和新回执补验。

已确认 exact5 范围、clean HEAD/tree、所有源码 blob 摘要以及 Python/Go/Node 锁定摘要。原 marker 的 133 个 inventory 文件经核验；仅剔除位置相关 verifier metadata 后产出 132 个 payload 文件，五个 binary role、运行时、合同、licenses 和源构建元数据完整保留。四个源目录额外 cache db 仍保留，摘要与原记录一致，未进入 payload。

manifest 可确定性重建，摘要 `2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c`。按作者 module-mode 参数独立编译得到相同 finalizer 摘要 `5bb69149ddb8ccc3a81bc5c940498534af53322ad99c3eb1978862500284179d`。首次 GO111MODULE=off 编译的差异完整保留，已定位为构建配置差异。

两份作者 finalized root 全量摘要复验通过。另用精确 finalizer 在两个新建中文/空格根完成真实 payload 的静态 finalization；均为 133 inventory + marker、正确的最终 verifier 路径/hash，payload identity 相同，installation identity 不同。真实 JS `loadProductLayout` 对四根只读加载通过。Go consumer 的字段、排序、摘要算法和大小约束按精确提交源码核对；未运行 Go 产品完整 loader 或产品入口。

Go 作者测试和新增边界测试通过；新增 8 个 stage 拒绝、8 个 manifest 拒绝，以及 Windows rename 语义观察。hardlink 与 junction 实际覆盖；file symlink 因当前 Windows 权限不足明确 SKIP。顺序运行时已有 marker 保持不变、成功时 marker 最后可见且无 temp；这些成功不覆盖 P1A-R1 的并发缺口。

没有安装、registry、PATH、用户数据、迁移、原生产品启动、C57 或正式验收操作。未运行 Git gc/repack/全库 fsck；作者此前 bad-tree 事件未修复。源码审查与静态复验不能替代实际安装事务、维护门、崩溃恢复、原生生命周期或正式 22/42 验收。

所有命令、stdout/stderr、独立探针、输入绑定、marker/verifier 快照和摘要见 `EVIDENCE-MANIFEST.json`；机器可读结论见 `REVIEW.json`。

清理限制：包含绝对路径边界检查的专属 scratch 清理命令被执行层自动审批以 `blocked by policy` 拒绝启动，未提供更细理由；命令内检查及删除均未执行。确切命令和目标见 `scratch-cleanup.json`。未绕过；Root 随后明确要求保留临时缓存和两份 fixture payload，用于 revision 差异复验。
