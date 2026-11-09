from pathlib import Path
import ast
T=Path('C:/Users/yqyyds/AppData/Local/Temp');old=T/'w0599_attach_seal.py';new=T/'w0599_attach_seal_revision.py'
raw=old.read_text(encoding='utf-8')
bad="ordinary active non-restored renewal must still succeed.'))]"
good="ordinary active non-restored renewal must still succeed.')]"
assert raw.count(bad)==1
raw=raw.replace(bad,good)
raw=raw.replace("'w0599_attach_audit.py','w0599_attach_seal.py'):","'w0599_attach_audit.py','w0599_attach_seal.py','w0599_attach_recover.py','w0599_attach_seal_revision.py'):")
raw=raw.replace('唯一新增 mechanical 829 为读取不存在的 report.md','新增 mechanical 829 为读取不存在的 report.md')
raw=raw.replace('旧候选与 827 原封。','旧候选与 827 原封。封包首版脚本随后产生 Python SyntaxError 831，未生成任何封包输出；原脚本和 exact IO 已保存，独立 seal_revision 仅修正多余括号并补齐失败记账。')
raw=raw.replace("mechanical_failure_ordinals=[829]","mechanical_failure_ordinals=[829,831]")
raw=raw.replace("diagnostic829_ref=pin(O/'diagnostic-829.json'),","diagnostic829_ref=pin(O/'diagnostic-829.json'),diagnostic831_ref=pin(O/'diagnostic-831.json'),")
ast.parse(raw)
with new.open('x',encoding='utf-8',newline='') as f:f.write(raw)
print('Distinct seal_revision source written; original failed source preserved; static ast.parse passed.')
