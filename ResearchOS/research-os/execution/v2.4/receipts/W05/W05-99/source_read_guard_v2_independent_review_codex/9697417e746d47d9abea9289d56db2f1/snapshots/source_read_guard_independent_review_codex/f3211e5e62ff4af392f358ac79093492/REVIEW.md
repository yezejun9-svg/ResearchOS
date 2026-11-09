# SourceReadGuard v1 独立源码审查

结论：**REQUEST_CHANGES**。发现一项本地路径边界问题；共享模式参数、同一buffer验证、部分失败关闭和close重试语义在源码与纯内存替身控制范围内通过。不能据此授予整个controller READY或证明实际Windows cleanup。

Source：source_read_guard_codex/68ac03921c9c4efd821c178dd934e16e/source_read_guard.py。
Source SHA-256 e61a1b078a40b7d8bda1116944c42e0ddd37644ad5689917a164b6c5d67d9c96 / 10646 bytes。
Manifest 099113490f7f894f0bcdc23e3d92ce31de1e4d4cac4883ec0dbc31d24f8f0a7c / 1899 bytes。
非作者审查者：/root/w05_merge_review。

## 🔴 R1 / P2：正斜杠 UNC/device 绕过打开前的本地路径检查

位置：source_read_guard.py:29–35 的 _canonical；acquire 在预检查后创建API并打开路径。

_canonical 只用反斜杠前缀判断设备路径和UNC，但 ntpath.splitdrive 保留原始分隔符。例如 //server/share/a.py 的 drive 为 //server/share，不匹配 drive.startswith("\\\\")，tail 又以/开头，因此被接受；随后normpath将其转换为UNC。//?/C:/guard/one.py 和 //./C:/guard/one.py 同样绕过。

独立控制把这三个路径交给真实候选方法、但使用纯内存API替身。三个输入都调用factory一次、open一次，之后才在final-path检查失败并关闭。这证明“不合规路径在任何打开之前拒绝”的承诺不成立。未打开真实网络或设备。CreateFileW文档明确允许正反两种分隔符，因此不能依靠Windows替代该preflight限制。[Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

建议：在拆分前统一分隔符，要求drive严格匹配ASCII盘符加冒号，并要求rooted tail；拒绝UNC/device等其他命名空间。保留final-handle检查作为第二道验证。以上三个负例必须在API factory和open调用均为0时拒绝，再封为新的不可变修订。

## 已通过的限定控制

- 构造和模块加载不创建API/文件句柄。候选AST仅允许已检查的导入；ctypes由审查者proxy替换，禁止真实DLL加载。作者pure_controls.py只作为输入快照，本审查未运行。
- 具体_Win32API adapter通过Python内存函数替身执行，其CreateFileW实参为GENERIC_READ、share=1、OPEN_EXISTING、FILE_ATTRIBUTE_NORMAL和不可继承句柄。没有FILE_SHARE_WRITE或FILE_SHARE_DELETE。按Microsoft API契约，这种共享设置拒绝不兼容的写入/删除访问，删除权限也包含rename；实际机器行为仍需Root探针。[Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
- final-path、size、ReadFile和再次size都使用同一held handle；length和SHA256检查后才发布raw，get_buffer返回该已验证对象。正确处理normalized duplicate，冲突pin在factory前拒绝。
- extra字段、digest格式、负数/bool size、per-file和total cap、相对路径、反斜杠UNC/device等已有拒绝分支通过。空文件pin也可验证。one-shot拒绝再次acquire，close清空buffers。
- 第二文件在open/final-path/size/read/size-change/short-read/hash各阶段失败时，已打开句柄均逐个尝试关闭。原acquire failure保留，观察中verification=FAILED，不能被后续成功close改写为成功获取。
- CloseHandle替身失败时保留原handle且closed=false、retained_handles_count>0；后续close重试成功才清除handle。错误列表保留历史，但当前closed和retained count依据现有句柄计算。
- 特别验证：第一次关闭失败、第二次成功后，entries全部closed=true、retained=0、closed=true，而errors仍有历史项。**不能把非空历史errors误判成仍有未清理句柄**；Root应分开记录曾经失败与当前释放状态。

controls.json包含28项通过控制、3个R1复现输入及关闭观察原文；independent_controls.py为审查者控制源码。执行exit0仅表示审查控制完成，结论仍为REQUEST_CHANGES。所有candidate acquire均使用内存替身；real_winapi_calls=0、candidate目标文件读取=0、native Job=0、provider=0、Main/canonical写入=0。读取本次Source/manifest及写入自己的证据目录属于审查I/O。

## 后续仍需的实际证据

修复R1并独立复审后，Root才运行授权的真实Windows探针：兼容子进程读取、持有期写入/rename/delete拒绝、final-path与pin一致、部分获取失败释放、重复close以及Job清理之后释放全部句柄。Root C4必须在任何Source消费者前持有完整Source/Python tuple，并在完整Job cleanup后才close；guard自身导入前的信任绑定也由Root负责。Host binary/Node/bundle的持有期应覆盖该Host整棵Job树与统一deadline。

这些是尚待证明的集成条件，本模块自身不创建Job、不证明provider预算或资格验收，也不证明实际Windows句柄已经关闭。本次未修改Source或其他既有成果。

