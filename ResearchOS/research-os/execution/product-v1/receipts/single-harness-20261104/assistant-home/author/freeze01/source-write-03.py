from pathlib import Path
import hashlib, json
base=Path(__file__).resolve().parent
target=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104/apps/web/src/workbench.jsx')
before=target.read_bytes()
prefixes=[b"import { workspaceProjectPath }",b'      if (!workspaceProjectPath(value))',b'  return <section className="local-project-entry"',b'    <div className="local-project-main"',b'    <details className="project-name-option"',b'    <div className="local-project-note"',b'    <Failure error={hostError}',b'    {result && <div className="project-open-result"',b'  </section>']
lines=before.splitlines(keepends=True)
count=0
for i,line in enumerate(lines):
    if any(line.startswith(prefix) for prefix in prefixes) and line.endswith(b'\r\n'):
        lines[i]=line[:-2]+b'\n'; count+=1
assert count==9,count
after=b''.join(lines)
assert before.replace(b'\r\n',b'\n')==after.replace(b'\r\n',b'\n')
directory=base/'source-write-03';directory.mkdir(exist_ok=False)
(directory/'workbench.before.jsx').write_bytes(before)
(directory/'workbench.after.jsx').write_bytes(after)
target.write_bytes(after)
print(json.dumps({'converted_only_changed_lines':count,'source_sha256':hashlib.sha256(after).hexdigest(),'semantic_bytes_after_newline_normalization_equal':True}))
