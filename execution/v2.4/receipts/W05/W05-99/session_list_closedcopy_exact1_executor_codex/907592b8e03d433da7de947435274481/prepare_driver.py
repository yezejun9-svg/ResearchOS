from pathlib import Path
import ast, hashlib, json
R=Path(r'D:/作品集/ResearchOS/research-os'); W=R/'.local/worktrees/codex-w0599-session-list-proof-r312'; P=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex/907592b8e03d433da7de947435274481'
rootrunner=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310/list_replay.v2.py'; raw=rootrunner.read_bytes();assert hashlib.sha256(raw).hexdigest()=='85e35100bd7ed509883a0ae4729f68aab283032002f8eb8784d28900e97c54ea';src=raw.decode(); tree=ast.parse(src);lines=src.splitlines(keepends=True)
names={'typed_cells','canonical_saved_cells','check_closed','check_wire'}
parts=[''.join(lines[n.lineno-1:n.end_lineno]) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(parts)==4
(P/'root_assertions.original.py').write_text('\n\n'.join(parts)+'\n',encoding='utf-8',newline='\n')
(P/'root_assertions.origin.json').write_text(json.dumps({'root_path':str(rootrunner),'root_sha256':hashlib.sha256(raw).hexdigest(),'functions':sorted(names),'copied_function_bytes_unchanged':True},indent=2)+'\n',encoding='utf-8')
print('Extracted four unchanged Root assertion functions; no target execution.')
