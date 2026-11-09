# Bridge03：真实后端作者与固定物理 C TEMP

本版本仅修复 Task98 的 BRIDGE-ROLE-001 和 BRIDGE-TEMP-002。继承 bridge02 的六 route、RUN_CURRENT_CM40、current Source21、独立 mode、CAS、有限 lease、OwnedJob 及原始失败保存合同。bridge01/02 与 Task98 两个反例、已通过 18/24 项检查保持原字节，不复测为新运行资格。

## 真实作者

Source 的 canonical 元数据为 codex:/root/attach_restore_independent_review；Main 角色使用固定真实 backend /root/attach_restore_independent_review。生成的 Root Scope.source_actor、SOURCE_AUTHOR proof.actor_id、roles.source_authors 必须使用该 backend；canonical 字符串仅放在 source_author_canonical 和 Source HDF 中。不能改写旧 capture，不能把 Root 作为 Source 作者。独立 review 必须拒绝 canonical 或 backend 形式的自审。

所有 stage 的真实 Root request 新增 source_hdf_ref、source_mf_ref、consumer_launcher_ref。新独立 Source decision 必须精确绑定这三项和既有 source_ref。来源 HDF/MF 位于本 Source 命名空间，包含实际 bridge 与 launcher。Root 实际发行的 Scope 携带 generation=bridge-20261010-03、两项 Source package refs 和 source_review_ref。SOURCE_AUTHOR 的真实 Root-thread peer delivery 可以通过 Main 已有 source_hdf_ref binding 链验证；本 Source 不生成未来 Scope、角色 proof 或 Final。

## 固定环境和资源证据

唯一允许的共同 TEMP/TMP 为：

    C:\Users\yqyyds\.researchos\w09-native-v5

Root 启动每个 bridge Python 前，须把真实进程 TEMP 和 TMP 都显式设置为上面的完整字符串，再使用锁定 Python 的 -I -S -B -X utf8 启动。适用于 seed、propose、activate、consume、roles、publish-registration、assemble、capture、check、derive。Bridge 在导入 Main 前检查物理路径和当前 tempfile cache；缓存不符直接拒绝，不修改或清除缓存来掩盖环境。

所有 request 新增 bridge_temp_parent、resource_parent_ref、resource_audit_ref、resource_owner_sha256，精确对应 Source 中固定的 Root resource-only receipt、实际 host audit、RESOURCE_OWNER.json marker。Root grant 的 request-body hash 绑定这些内容。每个进程核验原始 Root header/call/result 的字节、offset、SHA、项目身份、两个真实物理父目录及 marker；resource witness 不构成执行授权。

环境读取仅对这一目录和这一固定 marker 开例外。通用 physical()/checked() 仍只允许仓库/既有 PLAN；不能借 environment metadata 读取任意 C 文件。系统 Temp、D 盘、盘根、其他 C 目录、AppData 虚拟化路径、symlink、junction、reparse、resolve alias 全部拒绝。仓库输出范围不变。

consume 的 isolated_environment.TEMP 和 TMP 必须与共同父目录完全相同；USERPROFILE、LOCALAPPDATA、APPDATA 仍走原有仓库目录限制。每条 consumer 保持一次 OwnedJob/一次 Python，在新 consumer_launch.source.py 中先验证实际 TEMP/cache 和资源来源，再在同一进程执行未修改的 Main dispatcher。launcher 路径/SHA/bytes 必须经独立 Source decision 和 Root request 绑定；dispatcher 文件仍按既有可信 pin 校验。launcher 不启动 Native/Go，不改变 Main verify_mode，也不移动旧 Native 根。Main 实际 mode 门仍要求真实 owned state 位于当前进程共同 Temp 之下。

调用：

    <locked-python> -I -S -B -X utf8 w09_root_bridge.source.py <stage> --request <absolute-json> --sha256 <sha256> --bytes <bytes>

consumer 的实际父层 argv 现在是：

    <locked-python> -I -S -B -X utf8 consumer_launch.source.py <bridge-sha256> <bridge-bytes> <command-key> <check-id> <case-id>

launcher 给 Main dispatcher 还原原有产品 argv，原始父进程 argv 和 OwnedJob 结果照实记录。禁止将 launcher preflight 当作 Native、mode qualification 或 formal acceptance。

NF5 当前资格、四个实际 Native、独立 mode、Root Scope、最终 role registry 和 formal Final 均由后续真实工作提供；本次 Source 不预填。ROOT 仍是唯一 Main/Canon/Scope writer。

