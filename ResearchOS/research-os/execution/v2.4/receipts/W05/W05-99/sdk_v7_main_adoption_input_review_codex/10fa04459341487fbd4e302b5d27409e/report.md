SDK v7 五 Go Main adoption 输入核验

五个 Main 文件均精确匹配各自原基线，五份 proposal 均尚未集成；当前无文件内并行改动冲突。

| Main 路径 | 当前 SHA-256 | proposal SHA-256 |
|---|---|---|
| internal/host/vault.go | 75c00d534582c933839305c6e2e55190b82706111f2d33e3abe62e4f51c6a94c | 5bcf6aed6515bd991e5e7222999994e3d9192a6bd8f5a32b4669d4c67c0a6b50 |
| internal/host/host.go | 65848ad3476ccaf6dd2e76cf0753cf8c7257e2762bc9f115dcd0d1675aeb02cd | 6387df33f531be14d32c439095f9ebcf079fb7ae2c27697c98cdc9a554fb5dc7 |
| apps/control/main.go | 1f22bf62899b122d319cacd6cd1b6e2cee3f3995824367e21d94b12a483eaedc | 9a519be38a1c09a819864073eedf0eaf9941c4c75f95ded0c3e89143012da9b1 |
| internal/domain/runtime_qualification.go | 4b376196886f7202fa05f2e54d4083531651a459970276e05ac6c8203a879111 | 420aaec664f877806af079d47cf5e5a0cc4950f2cdc42b8ae1dc16ef7a4c5c54 |
| apps/cli/cli_stream.go | 58d541c2a7a07a2c55dc1af693f94f39067efb9440e48488dcf1352bfbd62eec | 87bfbd69972e674ae5255455ed26ce82ece167d8bb67155beed0cd52c05b9e6f |

五份完整 forward/inverse、历次 Go patch 和 Source 原件见 audit.json。整合前应再次核对五个当前 SHA；以最终 v5 proposal 为写入内容，不回放旧版本补丁。

未找到 SDK v7 专用整合 helper。旧 exact38 helper 固定旧提交链、38 路径和 321/149/422 authority，只能参考读取/pin 机制，不能原样执行。

保留其他 Main/dirty 成果、canonical4、旧 receipts 和 vault；v7 runner 不属于这五个 Main 写入路径。此次没有 Go/CLI/SDK/model/Git/CAS 执行，也没有重复 Source 控制测试。

metadata 失败672已保留完整原件：误猜 v3 统一 inverse 文件名。基线复核与 patch 核验随后按实际文件完成。
