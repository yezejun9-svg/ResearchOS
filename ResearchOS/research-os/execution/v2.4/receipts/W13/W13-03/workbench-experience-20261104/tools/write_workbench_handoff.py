import json
from pathlib import Path
from resume_workbench import REPO, RECEIPT, CANDIDATE, digest, write_json

summary=json.loads((RECEIPT/'desktop-build/summary.json').read_bytes())
assert summary['status']=='BUILT_NOT_NATIVE_TESTED' and summary['dry_run_validated']
review_path=RECEIPT/'desktop-build/independent-review.json'
assert review_path.exists(), 'Wait for the independent bundle review'
bundle=Path(summary['output'])
assert digest(Path(summary['manifest_path']).read_bytes())==summary['bundle_manifest_ref']['sha256']
source_review=json.loads((RECEIPT/'independent-review.json').read_bytes())
for row in source_review['source_manifest']:
    assert digest((REPO/row['path']).read_bytes())==row['sha256']
author=CANDIDATE/'.local/workbench-experience-author-report.json'
(RECEIPT/'author-report.json').write_bytes(author.read_bytes())
text=f'''# ResearchOS 工作台改进交接 · 2026-11-04

本轮已实际修改源码、独立复核并整合 Main，提交 `{summary['source_head']}`。永久项目 UUID 仍为 `aede0678-7308-43dc-b9f2-cfe3d90cfdfb`，路线沿用 MU_FORK / Go / React。

## 现在改变了什么

- 中央以会话为主，底部保留 CLI 风格输入和模型/工作区提示；Enter 发送、Shift+Enter 换行，组合输入事件不误发。
- 会话切换、模型资格、文件差异与编码授权按需展开，权限请求仍在主会话可见。
- 右侧显示当前项目的阶段计数、已验收成果与当前会话的工具/执行轨迹；技术回执可展开，旧失败轨迹可继续查看。
- 严格按会话隔离事件，保留 uint64 序号和精确金额；费用未知不填零，执行结束不冒充验收。
- 失败、离线与快捷建议保留未发送草稿；补齐目标“需重新验收”标签。

## 实际证据

- [独立源码复核](independent-review.json)：最终 12/12 Node 检查通过，0 跳过；七文件 hash 稳定，无未解决 P1/P2。
- [Electron 渲染矩阵](candidate-render-r3/report.json)：54 项开发检查、14 张截图；1440/1024/768/390/320 双主题、200% 缩放、输入/IME事件、发送桥接、失败草稿、建议追加、新会话隔离和离线。
- [深色工作台](candidate-render-r3/candidate-1440-dark.png) · [浅色工作台](candidate-render-r3/candidate-1440-light.png) · [320px 工作台](candidate-render-r3/candidate-320-light.png)。截图均标识为开发夹具；使用生产 renderer 加合成输入，不证明真实 Core/provider 成功。
- [整合回执](integration.json)：原 20 项 tracked 状态、33 个旧 dist 文件、原 step_state 均保留。

## Desktop 开发产物

路径：`{bundle.as_posix()}`

完整开发目录含 {summary['file_count']} 个清单文件，{summary['total_bytes']:,} 字节。构建与 dry-run 均退出 0；源、Mu、校验器、Core、Verifier、React 和固定 Electron 输入已封存。[构建 summary](desktop-build/summary.json) 与 [独立构建复核](desktop-build/independent-review.json) 分开记录。

manifest SHA-256：`{summary['bundle_manifest_ref']['sha256']}`。

开发目录不是安装包；本轮未替换正在使用的安装版。manifest/Verifier 绑定该绝对路径，不应移动或复制此目录当作可移植发行件。后续实际启动、首用与生命周期须遵守原 native 续跑限制，不能靠此构建回执签正式接受。

## 续跑边界

最新入口：[RESUME.json](RESUME.json)，并读取主仓 `execution/v2.4/checkpoint.json` 与 `HANDOFF_RESUME_PACK.md` 顶部。整合后 task_packet.py 实跑仍选择 W05-99，见 [next-card.json](next-card.json)。W13-03 原 BLOCKED 状态未伪造改成 ACCEPTED。

正式接受仍为 **0/42**，22 父任务未全部有效接受。安装/CLI 发行、真实共享会话/provider、NVDA/前台、独立留出权限、手机、8 小时隔夜、恢复/回滚及完整正式门仍须原合同证据。CP575 的 native helper、Installer P1b 与旧数据保护限制保留；旧 PID 和历史摘要不当作当前运行身份。

原 2305 条失败记录的内容/顺序保留，本轮诊断和首轮构建失败追加，禁止新目录/Goal 清零。第一次构建缺失隔离 checkout 中已有 Go 源码；仅补齐闭包后做了一次修复，旧回执与 scratch 保留。所有本轮命令/检查均已结束后再封存最终检查点，不声称后续后台仍在施工。

Git 候选提交时自动 gc 因内存不足失败，提交本身与快进整合成功；已记录该诊断，未重跑 gc。后续 Git 命令可继续逐次使用 `-c gc.auto=0 -c maintenance.auto=false`，不要清理旧工作树或历史成果来掩盖它。
'''
(RECEIPT/'HANDOFF.md').write_text(text,encoding='utf-8')
write_json(RECEIPT/'delivery.json',{'source_head':summary['source_head'],'desktop_output':str(bundle),'status':'DEVELOPMENT_SLICE_DELIVERED_FORMAL_GOAL_UNFINISHED',
    'source_review_sha256':digest((RECEIPT/'independent-review.json').read_bytes()),'render_sha256':digest((RECEIPT/'candidate-render-r3/report.json').read_bytes()),
    'bundle_summary_sha256':digest((RECEIPT/'desktop-build/summary.json').read_bytes()),'independent_bundle_review_sha256':digest(review_path.read_bytes()),
    'handoff_sha256':digest((RECEIPT/'HANDOFF.md').read_bytes()),'formal_increment':0,'formal_accepted':0,'formal_required':42,'parent_tasks_required':22})
print(json.dumps({'handoff':str(RECEIPT/'HANDOFF.md'),'source_head':summary['source_head'],'bundle_files':summary['file_count'],'formal_increment':0}))
