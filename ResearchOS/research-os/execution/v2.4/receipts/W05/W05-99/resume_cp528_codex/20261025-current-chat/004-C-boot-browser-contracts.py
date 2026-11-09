from pathlib import Path
R=Path(r'D:\作品集\ResearchOS\research-os');E=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'
for n in ['BOOT-C-ARCHITECTURE.md','B-API-compatibility.md']:
 p=E/n;print('CONTRACT',n);print(p.read_text(encoding='utf-8-sig'))
p=Path(r'C:\Users\yqyyds\.codex\skills\playwright\SKILL.md');print('BROWSER_SKILL',p.read_text(encoding='utf-8-sig'))
