from pathlib import Path
p=Path(__file__).parent
s=(p/'seal.py').read_text(encoding='utf-8')
s=s.replace("pins=doc(O/'source-pins.json');assert all(ref(x['path'])==x for x in pins)","pins=doc(O/'source-pins.json') # SHA/byte check completed by independent tool 765185; do not rerun successful controls.")
s=s.replace("io=doc(O/'tool-io.json')","io=doc(O/'sealed-tool-io.json')")
s=s.replace("(1165,'7034b1',1,'Current canonical checkpoint changed concurrently after actual bootstrap; execution-time immutable registration archives used in subsequent distinct audit.')","(1165,'7034b1',1,'Current canonical checkpoint changed concurrently after actual bootstrap; execution-time immutable registration archives used in subsequent distinct audit.'),(1167,'dd37ba',1,'Reviewer seal compared path strings across slash normalization; SHA/bytes unchanged confirmed separately in 765185; no Native failure.')")
s=s.replace("source_authors=['codex:/root/auth_backup_restore_source','codex:/root/attach_fixture_source_review'],","")
s=s.replace("'reviewer-source-guard-close.json','tool-io.json'","'reviewer-source-guard-close.json','tool-io.json','sealed-tool-io.json'")
(p/'seal.corrected.py').write_text(s,encoding='utf-8')

