# driver-v3 revision01：待独立复审

保留上版 `driver-v3` 全部文件。此目录只改 `run-owned.py`；`lifecycle.mjs` 与两份 PowerShell 脚本仍逐字节相同。源码 SHA256 与检查见 `PREPARATION.json`。

修正两处审查发现：只读扫描现在按安装包 `.exe` 名称 **或已知 PID** 取进程；已知 PID 即使复用为 `notepad.exe` 也会进入身份判断并阻止 release。控制器非零退出后，wrapper 在持久循环中写或核对 `exit.json`，再建立等待记录；写入、状态输出或等待建立出错时继续持有自身进程并重试。已有等待记录会核对后复用，避免重生成 nonce。

Root 的唯一 release 契约沿用 v3：绑定 scope SHA、outer PID、controller PID、exit SHA、nonce、wrapper 派生的身份清单。两次只读扫描间隔两秒，已知 PID、安装包镜像或未知身份仍在时继续等待。wrapper 不执行产品关闭或强制终止。写入介质长期故障可能使等待记录或 release 永远无法完成，外部工具宿主的进程回收机制仍未验证。

已通过 Python 静态编译、Node 语法检查、内联 PowerShell 解析；纯模拟证明非安装包名称的 PID 复用会阻断，以及退出证据、等待记录和日志写入出错后 wrapper 继续重试。没有运行 native／GUI／Core／CLI，正式验收增量为 0。
