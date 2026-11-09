import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'ResearchOS_Implementation_Package_v2.4'
def load(name):return json.loads((P/name).read_text(encoding='utf8'))
def put(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def blob(x):return '```json\n'+json.dumps(x,ensure_ascii=False,indent=2)+'\n```\n'
plan=load('contracts/execution.plan.json');ph=hashlib.sha256((P/'contracts/execution.plan.json').read_bytes()).hexdigest()
for name in ['step_state.template.json','checkpoint.template.json','step_receipt.template.json']:
    p='examples/'+name;x=load(p)
    if 'plan_sha256' in x:x['plan_sha256']=ph
    if 'input' in x:x['input']['plan_sha256']=ph
    put(p,x)
f=P/'05_WBS.md';s=f.read_text(encoding='utf8');s=s[:s.index('### W00｜')]
for t in load('contracts/tasks.json')['tasks']:
    s+=f"### {t['task_id']}｜{t['title']}\n\n**依赖**：{'、'.join(t['depends_on']) or '无'}。\n\n"+'追踪：'+'、'.join(t['requirement_ids'])+'；'+'、'.join(t['acceptance_ids'])+'。\n\n'
    s+='任务卡：'+', '.join(f"[{x}](tasks/steps/{x}.md)" for x in t['execution_steps'])+'。\n\n'+blob(t)+'\n'
f.write_text(s,encoding='utf8')
f=P/'06_ACCEPTANCE_TESTS.md';s=f.read_text(encoding='utf8');s=s[:re.search(r'^### [CA]\d\d ·',s,re.M).start()]
for c in load('contracts/acceptance.json')['cases']:
    s+=f"### {c['id']} · {c['title']}\n\n模式：{c['mode']}；唯一最终负责人：{c['final_owner_task']}；状态：NOT_RUN。\n\n固定输入：\n\n"+blob(c['input'])+'\n完整合同：\n\n'+blob(c)+'\n'
f.write_text(s,encoding='utf8')
f=P/'21_EXECUTION_CARDS.md';s=f.read_text(encoding='utf8')
index=['| 父任务 | 实施卡（从左到右；仍须按依赖选择） | 正式终验 |','|---|---|---|']
for i in range(22):
    tid=f'W{i:02d}';ss=[x for x in plan['steps'] if x['parent_task']==tid and x['phase']=='IMPLEMENTATION_SLICE']
    index.append('| '+tid+' | '+'；'.join(f"[{x['id']}](tasks/steps/{x['id']}.md) {x['title']}" for x in ss)+f' | [{tid}-99](tasks/steps/{tid}-99.md) |')
s=re.sub(r'\| 父任务 \|.*?(?=\n## 3\.)','\n'.join(index)+'\n',s,flags=re.S)
s=s.replace('W04-01项目 → W13-01桌面首用 → W04-02上下文/W12-01费用 → W05 CLI','W04-01项目/W04-02上下文/W12-01费用 → W05-01模型工具 → W13-01桌面首用/W05完整CLI')
s=s.replace('复制[step_state.template.json]','W00-01即初始化不存在的新版状态；W00-02只接续到候选worktree，不能覆盖。复制[step_state.template.json]')
s+='\n施工元数据的通用写入规则：每卡只写自身receipt目录；step_state/checkpoint只由唯一施工整合者在独立复核后更新。父allowed_paths包含子卡范围，具体产品文件仍服从W02已登记owner；共享文件不能因总范围允许就并发写。\n'
f.write_text(s,encoding='utf8')
f=P/'20_QODER_QWEN_EXECUTION.md';s=f.read_text(encoding='utf8');goal=(P/'GOAL_START.txt').read_text(encoding='utf8').strip()
s=re.sub(r'```text\n/goal .*?\n```','```text\n'+goal+'\n```',s,count=1,flags=re.S);f.write_text(s,encoding='utf8')
print('Refreshed current plan templates and reading projections.')
