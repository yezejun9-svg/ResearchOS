from pathlib import Path
root=Path(__file__).resolve().parent;s=(root/'prepare_rpc_combined_overlay01.py').read_text(encoding='utf8')
s=s.replace('combined-overlay01','combined-overlay02').replace('wiring-rev3-tests','wiring-rev4-tests').replace('4f9087adf2ce2262c3b3183d3c2f0a4afef8bc9ba47ccbbabcf9f2fb0b377ef8','9e7196a771ffb76b977608e5972a05a2757780cdfb0eecb2f62d4736f9ec5487').replace('14cf67c5f5de30a06e77269df40cd6d1e1daa9ffd7d67d19964c57cc15a8f08d','9c66ab9a8922f8e59b4a9fc54dba01bf6622dc4c0cdb4470a417ff97394a682f')
p=root/'prepare_rpc_combined_overlay02_actual.py';assert not p.exists();p.write_text(s,encoding='utf8')
exec(compile(s,str(p),'exec'))
