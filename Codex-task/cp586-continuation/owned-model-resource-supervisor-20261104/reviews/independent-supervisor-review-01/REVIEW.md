当前冻结 supervisor v1 需要修改，不能支持另立真实启动 scope。本轮是独立源码缺陷，不是权限或 automatic approval review 拒绝。

SUP-P1-001 位于 supervise.py:117-140，关键是129行两个 try 之间。纯 fake 反例在 Popen factory 返回同一对象后、进入 wait 的保护区前注入一次 KeyboardInterrupt；异常逃逸，fake process events 为 []，wait180、kill、wait5 都没有发生。wrapper 因而可能失去对仍运行 controller 的外层有界控制。R4 的独立 Job-close 修复结论不变，但它仍有 logger mutex 可令 controller 挂起的 P2，故此窗口实质阻断本轮 supervisor 目标。

反例代码见 run-pure-review.py:158-181，实际 raw 见 offline-checks.json 的 cancellation_gap_probe。该 raw SHA256 为 e1dfaf5eb2e7b2adde736108a345b80b997bdb17df3d44416155f1283495d21f，工具终态 e8d40e、读回 c2eeaf。所有对象均为内存 fake，没有真实 Popen。

21条普通 mock 断言（作者13条、独立 Dscope/CP gate 与消费顺序8条）及 py_compile 都通过；该退出0不代表反例通过，也不代表源码 PASS。独立 harness 同时审计拒绝真实 process/network 入口，实际尝试为0。

最小修复应在新 revision 中先 process=None，把 factory 赋值和第一次 wait 放在同一 try，except 按是否已取得原始对象分流：未取得则构造 UNKNOWN；已取得则同对象 kill1 + wait5，UNKNOWN 不得晚升级。回归应在已取得对象到首次 wait 之间的真实 line/opcode 边界注入取消，不能仅平移旧129行号。

旧16 pins、旧 failed-attempt-01、原R4全部 pins与两份独立报告必须保留。新 revision 可以使用自己的 manifest/scope ROOT，但全局 supervisor attempt 必须仍为原 owned-model-resource-supervisor-20261104/attempt-01，R4 run-01、exe/scope和43861不变，不能获得第二次次数。

最终读回确认 supervisor16/16、R4 prepared15/15+source7/7、旧76/76不变；global attempt-01 与 R4 run-01 都不存在。真实 Popen/controller/native/model/GPU/HTTP、D/Main/CP写入均为0，正式进度0/42。Root 已接受阻断并授权最小 revision-02；须新冻结、独立复核后再考虑 Root 单独的 D scope/checkpoint。

