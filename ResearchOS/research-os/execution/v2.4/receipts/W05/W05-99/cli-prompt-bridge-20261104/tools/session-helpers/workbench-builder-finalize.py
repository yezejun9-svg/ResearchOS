from pathlib import Path
import difflib
import subprocess

root=Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\workbench-experience-20261104')
css=root/'apps/web/src/workbench.css'
css.write_text(css.read_text(encoding='utf-8').replace('font:14px/1.65 inherit;', 'font-size:14px;line-height:1.65;font-family:inherit;'),encoding='utf-8',newline='\n')
name='apps/web/src/workbench.jsx'
original=subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=root).decode('utf-8')
current=(root/name).read_text(encoding='utf-8')
original_lines=original.splitlines(keepends=True)
old=[line.rstrip('\r\n') for line in original_lines]
new=current.splitlines()
result=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
    if tag=='equal': result.extend(original_lines[a:b])
    else: result.extend(line+'\r\n' for line in new[c:d])
(root/name).write_bytes(''.join(result).encode('utf-8'))
print('Preserved original line endings for unchanged source lines.')
