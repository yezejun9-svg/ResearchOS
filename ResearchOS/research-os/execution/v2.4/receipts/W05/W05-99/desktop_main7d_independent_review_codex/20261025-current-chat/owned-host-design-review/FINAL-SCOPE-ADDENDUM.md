Root最后确认的CP558拟议14文件范围取代报告末段较早的exact14名单：

1. apps/desktop/main/main.js
2. apps/desktop/main/lib/product-layout.js
3. apps/cli/main.go
4. apps/cli/cli_contract.go
5. apps/cli/cli_doctor.go
6. apps/cli/cli_native.go
7. apps/cli/cli_verbs.go
8. apps/cli/product_host_windows.go
9. apps/cli/product_host_other.go
10. apps/cli/product_host_windows_test.go
11. tests/ui/desktop/product-host.test.mjs
12. tests/ui/desktop/product-layout.test.py
13. docs/installation/desktop-product-host.md
14. apps/desktop/build-product-layout.py

设计审查意见：该调整可接受。保留desktop-management.js原有活Core拒绝与private stdio权属检查；由CLI main.go仅在host-bound操作调用启动/等待，减少在共享只读discovery函数里隐式启动的风险。cli_native.go统一稳定路径仍必需。builder须实际编译CLI，不能只有Electron树；绝对verifier安装绑定在owned最终位置生成。CoreBuildID是版本信息，不能替代真实PID/creation/imageSHA、data root、安装身份与private READY对应关系。

报告中的七项设计要求和CLOSE-SEMANTICS-CLARIFICATION.md仍为本阶段必须覆盖的边界。Root将其登记为CP558硬验收项属于Root授权与后续执行；本审查没有改源、跑测试或native，也不提前通过实现。完成后必须以实际diff、构建和受影响证据独立复核，Root另登记owned native范围。
