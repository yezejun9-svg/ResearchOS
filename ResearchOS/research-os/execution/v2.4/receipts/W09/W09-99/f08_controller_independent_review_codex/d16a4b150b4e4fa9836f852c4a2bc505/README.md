W09 2098f823 controller bundle 非作者独审：REQUEST_CHANGES。

六项必要修正见 review.json：未知映像恢复执行窗口；失败路径 process_generations 事实遗漏；未解释资源失败继续；junction 非零/NULL 绕过 sealer Job closure；Root/CAS/独审授权未语义绑定；helper 角色未固定到 spec。

实际 roster 静态一致：49=41新+8原、45资源无关+4OS、预期89RUN/89PASS/49leaf。所有目标 NOT_RUN，正式/source/parent验收增量0。43-member 原包及四源pin核对一致。

纯IO/AST/source，不 import 或运行原controller/helper，不读取变化中的MAIN状态，不改源或canonical。新 failed tool=1：子审传回诊断的命令过长被CreateProcess(os206)拒绝，native NULL；完整原调用JS和错误保存在failure-origins.json。STOPPED。

