# 工作台换行修订独立补审

**APPROVED_SOURCE_FIXTURE_ONLY**，仅批准已证明的一个字节换行规范化；`pending_blockers=[]`，`formal_increment=0`，`product_journey_increment=0`。这不是新 SHA 的测试或编译通过记录。

修订包 manifest 实际SHA256：`43f076b3b0c13131017380e86708f6433bfa863104de73ae7c5ded3722e100e3`。其来源 freeze03 manifest 实际SHA256：`111157d419e8d8257e54d86ec5c06ec68418172beee5bfddac0e87a5f94b282d`。完整exact6新source_sha256在本目录review.json。

## 独立字节证明

直接读取旧freeze03与新amendment candidate的原始bytes，逐字节比较删除位置前后：

- 唯一变更：`apps/web/src/workbench.jsx`，零起始字节偏移32692、一开始行号419，删除单个`0x0d`，后续`0x0a`保留。
- 所在行：`  const [hostError, setHostError] = useState(null)`。改变的是完整语句之后的CRLF→LF换行，不涉及字符串内容、JSX内容或代码字符。无需AST或执行即可确认这次修改为机械换行等价；未伪称运行过parser。
- 旧文件75212 bytes、CR=1、LF=783，SHA256 `69d0ecbbbfed1e5b51a8c60186131eb2e39ea8909c15160cb7949d03120df095`。
- 新文件75211 bytes、CR=0、LF=783，SHA256 `08ca4e3f3b67660de3f52dbf7b687ae2a7e2e5e504716895032fb21d1ee87bf0`。
- 删除上述单一字节后的全部剩余bytes与新文件严格一致；其余五个candidate文件逐字节hash不变；六个baseline仍与freeze03及manifest完全一致。

逐文件新旧hash与独立比较结果保存在 `byte-audit.json`，不是只复述作者的mechanical_proof。

## 证据归属与集成边界

引用已封存 `researchos-workbench-assistant-final-review-20261105/review.json`，实际SHA256 `d35cf21f82a8a3c656322ee7e0655a9ae609156c95fb45f9885aee8073faa0b8`。它记录的Node73通过、49输入hash、Vite01成功、411输入/31源码/3产物hash一致，仍精确归属于旧freeze03 source SHA；本修订没有重跑或改写这些记录。不将旧73/Vite结果标成新08ca SHA的实际执行。

新SHA尚未实际编译；Root计划fresh build14编译新源码。这是独立非阻塞待验项，不要求为该机械换行重复tests03/Vite01。真实geometry仍独立非阻塞待验，模型旅程/取消实际资格/只读隔离/正式验收没有增量。

父任务报告原integration已copy+stage旧exact6，cached diff check在commit前exit2，整体已知退出，HEAD1ac/CP691未变；Root保留原journal/plan并计划只恢复已staged工作的commit步骤。本审查只记录此父任务上下文，未读取/写入索引或执行git命令，不证明stage或commit已完成。此次批准只覆盖修订包的新exact6与单字节delta，不能当作重跑原integration helper、重copy整卡、reset或unstage的执行记录。

01/02源码问题及本次换行格式诊断均保留origin_key/classification/detail，旧报告与冻结包不覆盖。新交付仅C盘；文件选择清单使用task-root相对路径，完整SHA可供归档。按现场资源约束全部文件审计串行、login:false；未遇本轮资源error，未启动Node/App/Core/Native/模型或任何测试。