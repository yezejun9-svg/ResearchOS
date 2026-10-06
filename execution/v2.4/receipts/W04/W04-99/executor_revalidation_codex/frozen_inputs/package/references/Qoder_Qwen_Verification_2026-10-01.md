# Qoder / Qwen 核实记录

版本：2.4.0。时间：2026-10-01（Asia/Shanghai）。范围：当前机器的 CLI 无推理探针与官方资料；没有模型任务、产品建设或凭据读取。

## 1. 本地直接证据

| 探针 | 结果 | 能证明什么 |
|---|---|---|
| `Get-Command qoder,qodercli,qodercli.exe` | qoder.cmd 位于 `C:/Users/yqyyds/.qoder/entry/`；qodercli.exe 位于 `C:/Users/yqyyds/.qoder/bin/qodercli/` | 当前命令解析路径 |
| 读取上述 qoder.cmd 与同目录 qoder-dispatcher.ps1 | wrapper 分派 CLI/IDE；现存路径首参数走 IDE，选项首参数走 CLI | 应用 `-w` 或明确 exe 选择 CLI |
| `qodercli.exe --version` | `1.1.64`；exit 0 | 当前安装版本 |
| `qodercli.exe --help` | exit 0；下表列出相关参数 | 当前二进制声明的语法 |
| `qodercli.exe --list-models` | exit 0；内置列表含 `Qwen3.8-Max`、`Qwen3.8-Flash` | 当前账号目录能看见指定模型 |

目录输出还含其他已配置模型；它们不属于本目标，不在本包复制账户自定义 ID。本记录没有读取 settings、API key、token 或认证文件。`--list-models` 是账号目录查询，不能被写成完全离线验证，也不能证明推理成功。

本地 help 的相关参数：

| 参数 | 已观察到的说明或用途 |
|---|---|
| `-m, --model <model>` | Default/New Models 使用 model name；Custom 使用 modelID |
| `-w, --cwd <dir>` | 启动前切换工作目录 |
| `--add-dir <dir>` | 为工作区加入其他目录 |
| `--permission-mode <mode>` | choices 为 default / accept_edits / bypass_permissions / dont_ask / auto |
| `--list-models` | 列当前用户模型目录 |
| `-p, --print` | 非交互输出后退出 |
| `--tools <tools...>` | 限制可用内置工具，可空值禁用全部 |
| `--strict-mcp-config` | 只使用显式 MCP 配置 |
| `--max-model-request-retries <count>` | 模型请求重试上限 |
| `--max-output-tokens <size>` | 模型输出上限 |
| `-o, --output-format <format>` | CLI 输出格式 |
| `--no-session-persistence` | 仅 print 模式，不保存可恢复会话 |
| `-c, --continue` | 恢复最近会话 |
| `-r, --resume [id]` | 按标识恢复，未给 ID 时选择 |
| `--session-id <id>` | 使用指定会话 ID |
| `--list-sessions` | 列历史会话后退出；本轮未运行，以免枚举无关会话 |
| `-n, --name <name>` | 会话显示名称 |

本地 help 没列 `--max-turns`、`--yolo`、`--goal`，也没列 `goal` shell 子命令。某些官方旧示例包含前两者，但本包不依赖这些未在本机 help 中确认的别名。Goal 轮次放在交互 `/goal ... --turns N` 中。

## 2. 官方资料与采用范围

| 官方来源 | 本包采用的事实 |
|---|---|
| [Qoder Goal Command Reference](https://docs.qoder.com/cli/goal-reference) | `/goal <description> [--turns <N>]`；status/pause/resume/take/clear；持久化、ownership、轮次上限与恢复 |
| [Continuously Achieve Goals](https://docs.qoder.com/cli/goal) | Goal 是清楚完成条件下的持续施工模式；在 TUI 中设置 |
| [CLI Commands and Parameters](https://docs.qoder.com/cli/cli-reference) | CLI 启动、模型、会话及工具参数；落地时再用本机 help 交叉核对 |
| [Slash Commands](https://docs.qoder.com/cli/slash-reference) | `/goal` 与 `/quest` 分别存在；命令会受版本和 feature gate 影响 |
| [Commands](https://docs.qoder.com/cli/commands) | `/quest` 属于工作流提示命令；TUI 操作不能一概移到 headless |
| [Model Selection](https://docs.qoder.com/cli/model) | 目录与参数可能由服务端改变；以 `/model` 和 `--list-models` 为准 |
| [CLI Custom Models](https://docs.qoder.com/cli/custom-models) | BYOK 经 `/model` Custom 向导；不要手工猜测 settings.json 配置 |
| [Qoder IDE Custom Models](https://docs.qoder.com/qoder/custom-models) | IDE 另有自定义 Base URL；不能据此宣称 CLI 同等支持 |
| [Permissions](https://docs.qoder.com/cli/permissions) | auto 自动判断授权；dont_ask 拒绝需要询问的动作；Goal 不代替权限配置 |
| [Qwen3.8-Flash model info](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-flash) | 官方模型 API ID 为 qwen3.8-flash |
| [Qwen3.8-Flash release](https://www.alibabacloud.com/en/news/product/qwen38-flash-released-noi?_p_lc=1) | 该模型是已公开的官方产品；不是把用户文字猜成一个不存在的型号 |

资料之间存在版本化措辞差异：Goal guide 对完成后清理、暂停时权限恢复的描述与 Reference 的权限独立说明不完全一致。本包使用 Reference 的明确命令语法，在实际版本中通过 `/status`、`/goal status` 检查行为；不依赖“Goal 自动给满权限”或“状态清空即产品完成”的推论。

## 3. 证据等级与未验证部分

| 项目 | 当前判定 |
|---|---|
| CLI 安装与基础语法 | 已用当前二进制验证 |
| 当前账号显示 Qwen3.8-Flash | 已用目录查询验证 |
| Qwen 模型官方身份/API ID | 已查官方资料 |
| Qoder `/goal` 语法与语义 | 官方文档已证；本轮未在 TUI 实跑 |
| 指定模型推理、Read/Write/tool-call | NOT_RUN |
| 额度、持续可用性、长时间运行、真实费用 | NOT_RUN / UNKNOWN |
| Goal 暂停/恢复/接管的本机运行行为 | NOT_RUN |
| 后台运行、退出后继续、跨进程工具取消 | NOT_RUN；没有后台服务证据 |
| ResearchOS 自有 CLI、Desktop、双端接续 | 本记录不提供产品验收结论 |
| 第三方模型实际内部路由 | 不由模型自述或目录结果证明；只记录可获得的真实元数据 |

## 4. 可运行的单次附件探针（模型调用尚未执行）

程序见 [tools/probe_qoder.py](../tools/probe_qoder.py)。依据本地 help 支持的 `--attachment`，只提供 `00_START_HERE.md`、`08_AGENT_EXECUTION_GOAL.md`、`tasks/steps/W00-01.md` 三份附件。使用 `--tools=` 禁用全部 Agent 工具、`--strict-mcp-config` 禁用非显式 MCP、`dont_ask`、零自动模型重试及不保存会话。

这项选择替代最初的 `Read` 工具方案：`--tools=Read` 只能限制工具种类，不能独自证明文件级隔离。现在检验的是给定规格内容的理解，不检验 Read tool-call，也不声称宿主进程处在操作系统文件沙箱内。

```powershell
python tools/probe_qoder.py --print-only
python tools/probe_qoder.py --output '..\research-os\execution\v2.4\probes'
```

没有 `--output` 且没有 `--print-only` 时，脚本拒绝执行。真实运行的输出目录必须在规格包之外；每次使用独立报告文件名，不覆盖既有证据。可以用 `--qoder-cli <真实exe路径>` 指定已有安装，用 `--timeout 1..120` 收紧期限；不能换模型。实际输出记录请求型号、输入哈希、参数、期限、退出码、脱敏文本与 NOT_RUN 产品状态；常见凭据形态会遮蔽，对外分享前仍检查脱敏文本。

Python 标准库通过 Windows API 实现专属匿名 Job Object。进程以 suspended 状态创建，成功加入 job 后才恢复，避免加入前启动子孙的窗口；异常/超时关闭只属于本次运行的 job，连同正常 CreateProcess 派生子孙回收。无法建立 job 则在启动推理前失败，不降级成不受控后台运行。该机制不负责回收外部服务自行发起的工作；本探针未开放能发起此类工作的 Agent 工具。[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) · [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)

成功退出时报告状态为 `RESPONSE_REQUIRES_REVIEW`，不是 PASS。必须将返回的版本、首任务 ID/标题/依赖/必读合同和完成门逐项对照附件。超时、非零、缺字段、内容错位、附件不受支持或输出截断分别留证；不能以模型回复“读完了”替代检查。即使对照通过，也不能据此判定真实 Goal 长时间实跑、Read/Write 工具、产品能力或内部 provider 路由通过。

## 5. 已运行的工具自检

2026-10-01 本机执行 `python -B tools/test_qoder_tools.py`：4 项通过。测试使用本地临时模拟程序，没有模型调用。

| 检查 | 证据边界 |
|---|---|
| 探针只传三份附件、指定Qwen、禁用全部工具、缺文件拒绝 | 程序参数与输入检查 |
| 有界运行器捕获输出与退出码 | 本地 Python 子进程 fixture |
| 期限耗尽后子孙没有继续写入，无关进程仍活着 | 本机 Windows Job Object 行为 |
| PrintOnly不执行程序；CheckOnly匹配trim后的精确型号；错误型号非零退出 | 临时 fake Qoder + fake package validator |

启动器见 [tools/start_qoder.ps1](../tools/start_qoder.ps1)，模型探针语法与命令见 [20_QODER_QWEN_EXECUTION.md](../20_QODER_QWEN_EXECUTION.md)。没有真实模型读取结果，不把上述 fixture 检查写成 Qwen 或 ResearchOS 已完成。
