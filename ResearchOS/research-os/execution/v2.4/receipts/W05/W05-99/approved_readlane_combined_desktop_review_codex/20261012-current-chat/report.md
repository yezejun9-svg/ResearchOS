# Read lane 组合 Desktop 包独立审查

结论：**APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION**。组合包源码/输入/组分/权限核对通过，renderer 原始记录缺口已用两次独立新运行补证。可由 Root 在另一个明确 scope 中进入正常APP原会话验证；本结论不是实际资格、installer或产品正式接受。

组合来源为 UI/新 validator `070e6cda24ec2fadca104873534febcedfb7ddc0`、复用 Core control/verifier `cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8`、Mu `8dfebe36508ac0c2508735bb866756dab9283e74`。Main `91218bdd3901bae94a2c1c90521a4d133c59026d` 与 UI Source 的 committed tree 均为 `eee694bdad48a45282cf9884f9b5ef21ee0a76e3`；自 C381 累计只改 ipc.js、main.js 和 HTTP 边界测试三文件，且逐字节等于本轮 V2 独审54/54时冻结的源码。

| 核对 | 独立结果 |
| --- | --- |
| 完整包 | 58文件，共175776752字节；无缺件、额外文件、hash/size差异或 symlink/junction。每个复用/拷贝成员与所声明源文件一致。 |
| UI | 14个 Main/preload 模块在 Source、fresh build、package 三处字节一致；18个 React 输入快照与 Source 一致，3个编译产物与 descriptor 和包一致。 |
| 公开契约及迁移 | 32个包文件与 Source 和 Main 当前公开文件一致；两 schema hash 与 transport 的固定协议摘要一致。 |
| 完整编译绑定 | 6444项输入全部重新hash，输入digest为 `75662533d355546c5e436cb22354cfb6fc05ac5a1a4c1b7a24ff97ba35fe85bb`；WORK1844与archives680合计2175个去重文件全部hash/size通过；Go/Vite argv、cwd、工具hash、编译raw和离线环境均核对。 |
| 新 validator | hash `e9a9ce0e267399f91ee2ea2b3e877049a79f26785c4498fc4f10a3584905ab52`，descriptor `920c738cb92a8cc9d49977111febf7760f3d05f03e5bbff1ce236b6e17ebeadb`；实际 Go version -m 显示070e、modified=false和本次input digest。 |
| Core 复用 | control `326f70d5…`、verifier `28ea9cc1…` 字节等于旧审核包；实际 metadata 均为CB、modified=false；旧Core Source当前HEAD仍CB且clean。 |
| Core旧凭据更正 | 原manifest bddb…、correction12eb…、supplement f672…合读，有效tree为 `2936ca3097bc2c2d6cd6fd2e9af40756d25d32f8`，未把原手抄错误e8当权威。 |
| Mu及工具 | worker `2a8e7013…`、Node及build记录与旧固定组件一致，Mu pin8df；Go1.27.1、Node24.9.0记录及锁定工具hash一致。Electron只核对锁定37.10.3包元数据/文件hash，本审查未启动它。 |
| installer | 新manifest ddf8f817… 指向新C包绝对 verifier 路径、正确hash、SourceCB、arguments=[]；独立PowerShell7.6.5 Get-Acl确认owner当前SID1001、protected、唯一非继承FullControl Allow。 |
| 受保护工作 | preflight-v2的9个Main工作文件原字节全部不变。它们含用户原dirty/未提交成果，不要求这些字节出现在干净Source；不将Main工作目录误称clean。 |

构建器的validator测试与四入口253/253日志、原始stdout/stderr摘要均独立核对；253为coding21 + management11 + React5 + HTTP180 + qualification34 + renderer2，未因补跑增加unique或formal计数。本轮未重复整套测试。本轮先前54/54是对相同源码和当时bound validator的独立边界实跑；当前fresh validator的253项记录由builder执行并在此审查，不混称为本审查再次执行。

CP444 scope 要求 renderer 原始记录不能互相覆盖。初次四入口虽有独立入口目录，HTTP入口内React与legacy仍共用electron.stdout/stderr/invocation.json，最终只保留legacy native原件。该缺口已明确指出，Root限定builder追加两个精确单用例、各自独立目录的append-only补证，不改Source、原manifest、旧raw或包。补证 manifest `171ad2ec…` 已独立验过，137个raw成员全部hash/size通过：React PID23208、legacy PID64088，记录各自OS creation time、锁定Electron命令行、独立stdout/stderr，两个原子进程numeric exit均0，Node各1/1且exit0；WIRE_ROOT均为本次最终包。原2299件四入口raw及原manifest保持不变。初次React原件仍标为缺失，新补跑是补充观察，不冒充旧原件恢复。React stderr的fixture未注册current handler信息仍完整保留。

旧V2首轮React fatal及numeric exit4294930435、此前构建失败和收集器诊断继续保留；后续通过不抹去旧失败。新installer保护命令曾把ordered hashtable通过Select-Object显示为null，这只是compact stdout显示问题；本审查依据原ACL对象的独立实际读回判定，不依据null摘要。

包保持组分来源声明：UI/validator是新070e，Core是原CB，Mu是8df。不存在把全部二进制标成新Main构建或混入Mu M0 V4的依据。构建result仍保留 BUILT_NOT_TESTED/source_acceptance=false历史生成状态，后续测试和独审由独立记录证明，不篡改构建阶段记录。

本审查未启动正常APP、Core、worker、verifier，未访问真实SQLite或密钥，未发起API/外部网络/模型/工具动作，也未改Source/Canon。后续正常APP原数据Session、重新取得lease、PREPARE60秒及原确认，仍需Root另scope执行并观察。private management frames、verifier stderr/native numeric wait本轮仍missing；不得从Electron退出或SQLite状态推导这些缺失事实。包审查通过仅表示可进入Root后续受控activation范围，installer、真实资格、产品/父任务及formal接受增量保持0。

独审诊断：首次保护脚本多加了“干净Source也应等于Main原dirty9文件”的断言，遇到domain_test差异后撤销该不适用要求；修正版只核对授权保护的Main原字节并单列Source实际值。原脚本及修正版都保留，未改动任何受保护文件。一次宽范围文本查询输出过大和一次不存在runtime目录的只读查询，不构成产品失败。

补证核验脚本第一次假定单参数 `--test-name-pattern=...` 和旧式stdout字符串字段，实际argv为分离参数且stdout为结构化引用；修正版按原始invocation格式核对通过。两份核验脚本保留，未重跑renderer或改写任何builder原始记录。
