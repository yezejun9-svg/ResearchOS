# C57 boot6 v12: business token privilege admission

## 影响与修复

独立复审指出，原业务 token 的 `TokenPrivileges` 只进入摘要，已分配但 disabled 的 `SeTakeOwnershipPrivilege`、`SeRestorePrivilege`、`SeBackupPrivilege` 仍可随真实 producer 进入 plan/arm。Windows 允许启用已存在而被禁用的 privilege；三项权限分别影响所有权/ACL 恢复及读取能力（[Microsoft privilege constants](https://learn.microsoft.com/en-us/windows/win32/secauthz/privilege-constants)、[changing privileges](https://learn.microsoft.com/en-us/windows/win32/secbp/changing-privileges-in-a-token)）。本轮只在 `boot_windows.go` 的真实业务 token 读取路径增设准入：读取完整 native `TokenPrivileges` 后，先验证数组长度，再按本机 LUID 拒绝三项权限的**任何已分配条目**，不依赖 ENABLED flag；通过后才生成权限摘要。

该检查位于官方业务进程 producer 和重启后 Explorer consumer 共同调用的 `tokenSecurityShape` 内。plan 的 `checkAncestorControl` 在写 `pre.json`/`PREPARED` 前调用它；arm 的同一检查在 `APPLYING` 前调用它。管理 token 的 `ensureOwnerRestorable` 独立读取其权限，不经过业务准入，合法的管理恢复能力保持。没有修改 JSON schema、公有参数或其他四个 boot6 文件。

## 验证与边界

`boot_windows_test.go` 使用本机 `LookupPrivilegeValue` 得到三项真实 LUID，再构造 `TokenPrivileges` 原生结构测试每项 disabled/enabled 两态；六个拒绝均通过。安全的 `SeChangeNotifyPrivilege` 输入通过，截断的 privilege 数组被拒绝。合成拒绝前后重新读取当前 token，原生权限字节相同。当前安全 token 经真实 `captureOfficialBusinessToken` producer 及 `inspectExistingBusinessProcess` Explorer consumer 调用通过。

这是对源准入和真实安全 token 路径的验证。没有创建用户、给实际 token 添加/启用危险权限，也没有执行危险 token 的真实 plan/arm 或 native bypass。全阶段前置顺序由源码调用链核对；不能把合成 LUID 拒绝称作真实危险 token 绕过复现。正式验收计数仍为零。

| 原始记录 | 退出码与含义 |
| --- | --- |
| `v12-dev-01.*` | 1；首次编译发现 `LookupPrivilegeValue` 要求 UTF-16 指针，原始失败保留。 |
| `v12-dev-02.*` | 0；焦点测试覆盖六种危险权限状态、安全权限、截断输入及真实安全 token producer/consumer。 |
| `final-v12-c-windows-tests.*` | 0；C 盘自有自然继承密集 ACL 夹具完整两包测试通过。 |
| `final-v12-d-windows-tests.*` | 0；D 盘自有夹具完整两包测试通过。 |
| `final-v12-linux-crossbuild.*` | 0；Linux amd64 交叉构建通过。 |
| `final-v12-diff-check.*` | 0；`git apply --cached --check --whitespace=error` 只读检查通过。 |

`final-v12-command-recipe.json` 在最终测试前记录命令和环境；`final-v12-pre-source-manifest.json` 记录测试前六源哈希；`final-v12-six-source-manifest.json` 验证测试后哈希相同；`final-v12-six-source.patch` 是相对已提交 `08d63ed8` 的二文件补丁。未 stage、commit、amend 或 push。v11 和旧提交原样保留。
