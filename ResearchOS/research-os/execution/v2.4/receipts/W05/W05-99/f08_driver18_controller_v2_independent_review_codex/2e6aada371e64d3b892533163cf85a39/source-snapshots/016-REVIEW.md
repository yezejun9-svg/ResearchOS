## Review Summary

**Verdict: REQUEST CHANGES.**

driver18 执行准备的 partial17 roster、I16 三阶段和独立 source/resource 接受边界已写清楚，但 controller 的成功退出包装必然变成 exit 1，必须修正后才可进入 Root 的实际 prepare/execute。内层 3300 秒截止还需传递到子调用。所有结论为静态源码审查，未执行候选、Go 或 SQL。

### Critical Issues

- **D18-C01：成功退出被捕获成失败。** driver18_controller.proposed.py:255–258 在 try 内调用 sys.exit(main())，随后 except BaseException 会捕获 SystemExit。即使 main() 返回 0，入口也会输出 ENTRY/SystemExit(0) 并 sys.exit(1)。因此 prepare 可以写出 successful prepared/result 文件，但其真实 controller exit 必为 1；launcher:59 的 job_ok 正确拒绝它，后续合法 execute grant 无法形成。最小修正：try 内只计算 exit_code=main()；异常分支保存真实 ENTRY 诊断并确定失败返回码；将 sys.exit(exit_code) 放在 try/except 外。不要改 launcher 把 1 当成功，也不要仅凭 prepared.json 的 reported success 放行。

### Important Issues

- **D18-I01：3300 秒 inner cap 只限制开始时间。** controller:143 在每次调用前检查 elapsed<3300，但 :150 仍传完整 seconds，:193 的 build 为600，:224 的 test 为750。例如 t=3299 开始的 I18 仍被允许运行750秒，直到3600外层被终止；实际总时长超过声明的 inner cap。最小修正：建立固定 absolute inner deadline，每次 native 调用以剩余时间和600/750取最小值，并为 helper 的5秒 cleanup 保留预算；请求记录同时保存 nominal/effective timeout。证据收尾和最终资格也要拒绝已过期的 inner completion。outer3600 与 cleanup5 保持原 Root scope，不靠外层 timeout 代替内层 deadline。

### What's Done Well

- partial17 的执行名单固定为 I01–I16、I18，共17案例、30 native calls；仅显式 PARTIAL_17_EXPLICIT 可以执行。I17 保持 OPEN_NOT_AUTHORIZED，未声称 all18 PASS。
- prepare 与 execute 独立 grant，execute 固定 prepared.json bytes/ref 和 source/resource refs；UNBOUND scope、缺 authority validator/resource catalog 均在目标启动前拒绝。真正 Root authority adapter、actual canonical copies/CAS tuple、resource closure仍明确 OPEN，没有 implemented authorized:true 替身。
- 新 work/隔离 modcache/空 build、qualified version replace、旧 driver 无 replace、实际 Go graph/module dirs、WORK/importcfg/archive/buildinfo/exe均有具体入口；继承环境限制为公开白名单并固定 offline Go设置。没有旧 exe/cache binary 复用路径。
- I16 的三个独立进程由同一受控 caller 串联。producer 在 trusted_schema OFF 写 x7 后关闭并拒绝 sidecars；旧 probe 不注册 UDF，验证精确 schema、missing-function 原 cause code1 与 count1不变；controller 保留原 closed file 前后字节、原报告与真实 stdout一致、各 native/job事实；第三阶段原 TestDriverI16 核 x7/count1，真实 insert9/count2，再封 closed copy。没有把 phase-only report 当案例 PASS，完整额外 SQL inventory 也未假称执行。
- I18 直接调用原 TestRegisteredFunctions，原 func_test.go SHA85e63e33…/35317B 未改；两段1000×200ms循环仍完整，750秒测试预算没有缩短原断言。
- debug helper 的未知 image/module 拒绝、精确文件句柄 bytes、process generation/exit账、active limit min(process_cap,16) 与5秒cleanup有实际源边界。normal outer helper 保留实际 exit和Job关闭；Python/OS记录诚实声明 point-in-time only。

### 必须保持的接续条件

修正仅进入新的作者 namespace，重新封 controller/scope refs、必要有限 roster/合同与独立 review。Root driver18 authority adapter 和 actual source/resource grant 仍需另行完成，不能用本报告授予执行。先实际 prepare成功及封存，再由 Root校验真实 completion/native/job/manifest 后发行精确 execute grant；不复用旧 grant、旧UUID或未成功 prepared。I17 来源映射与另行 source writer 不混入这17案例。

### Verification Story

已按测试 intent/合同在前，读完整 controller/launcher 与 I16程序，再核实际 helper调用、caps和源输入。作者 manifest34成员+self35均重哈希，选定55份实际 refs与只读副本在 inputs.before.json，收尾核前后无漂移。沿用已封 fd09/fullfork/ZIP独审的精确 refs，不重复审1899个源文件。没有执行本候选或 target，未跑Go/gofmt/AST/typecheck/build/SQL/driver/HTTP/Node/SDK/model；没有编译或案例通过声明，正式接受仍0增量。

本轮 metadata 新非零 origins为0，原工具命令与返回诊断见 commands.original.json/commands.supplement.json。旧 fd09/mapping/cleanup/所有历史失败计数均未改。
