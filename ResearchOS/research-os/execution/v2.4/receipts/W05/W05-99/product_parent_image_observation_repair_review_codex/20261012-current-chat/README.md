# Parent image observation 独立审查

**ACCEPT — SOURCE_AND_NATIVE_OBSERVATION_FIXTURE_ONLY**。候选 `040d297627e2cfc5de2d6b9e770acc7bdf4f9ab7`，仅2文件；无阻断项。

56/56绑定检查通过，覆盖45份原始receipt、原失败启动记录、2份Git源码及control/verifier来源元组。`exactImage` 函数逐字未变，启动/发布仍受128MiB限制；观察路径采用256MiB+1有界读取与前后大小/mtime检查，原PID/CreatedNS/hash及SameUser SID验证保留。

独立运行7父、6子测试通过，无失败/跳过。对仍运行的原Electron PID53188执行只读检查：204521984 bytes，同一OS路径在原128MiB函数被拒绝，在新256MiB观察函数通过，hash/CreatedNS/Alive吻合。错误身份、junction、非规范路径、大小边界和启动拒绝均通过。未发进程信号、窗口指令或kill。

作者最终两项control/Mu/verifier原生回归以冻结原始输出复核，未重新运行Core24或模型链。完整Electron真实首用与正式验收未接受；本轮真实及合成模型调用均0，external/paid/tunnel为0，formal/parent +0。最终二进制核验来源，未独立重建。

新缓存定向删除被自动审批审查以 `blocked by policy` 拒绝，已保留并排除证据清单；未尝试其他删除方式。
