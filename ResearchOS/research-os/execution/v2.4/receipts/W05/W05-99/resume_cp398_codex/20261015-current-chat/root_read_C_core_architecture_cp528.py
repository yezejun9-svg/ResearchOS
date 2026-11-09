from pathlib import Path
R=Path(r'D:\\作品集\\ResearchOS\\research-os');E=R/'execution/v2.4/receipts/W05/W05-99'
for d,n in [('qualification_failure_revision02_architecture_codex','C-ARCHITECTURE.md'),('qualification_failure_revision03_architecture_codex','C-lease-addendum.md')]:
 p=E/d/'20261015-current-chat'/n
 print('DOCUMENT',n,'BYTES',p.stat().st_size);print(p.read_text(encoding='utf-8-sig'))
