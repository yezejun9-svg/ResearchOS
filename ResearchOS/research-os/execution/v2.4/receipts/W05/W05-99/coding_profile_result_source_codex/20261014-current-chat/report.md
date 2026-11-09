# Desktop CODING profile_ref Source 修复回执

已在指定 D 稀疏 worktree 提交 `a070f16d06fee609691992ba57ee046431f8f55f`，只改授权的两个文件。`acceptCodingResult` 现按 Core 的 `Artifact` VersionRef 验证四个精确字段：合法 ID、正安全整数 revision、合法 sha256；拒绝字符串、空值、数组、缺键、多键、错类型和坏值。接受后深拷贝并冻结引用，调用者之后不能改写 intent。其余请求、上下文、scope、次数与 STATUS 守卫未改。

测试 fixture 使用 Core 返回的对象形状。CONFIRM 后原 STATUS 返回同一个有效 ref；20 类无效 ref 无法成功结算。小数和超出安全整数的数字在私有帧解析层先被拒绝；用例另直接验证结果校验层也拒绝它们。`test03` 对两个相关 Desktop 边界套件运行 43 项，全部通过，native exit 0。`git diff --check` exit 0。原始命令、标准输出、标准错误和数字退出码逐次保留；首次 24/25 失败及全部设置/回执失败见 `failed-attempts.json`，未覆盖或归零。

`FINAL-report.json` 给出基线、提交、树、补丁、源码、测试和 Node 哈希。作者不签发独立接受；尚未 build、集成、运行产品 GUI/API/Core，也未再次 CONFIRM。正式验收增量 0。
