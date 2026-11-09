from pathlib import Path
p=Path(__file__).resolve().parent/'register_product_v1_layout_visual02.py';assert not p.exists()
b=p.with_name('register_product_v1_layout_visual01.py').read_bytes()
for x,y in [(b'build-08',b'build-09'),(b'build08',b'build09'),(b'visual-01',b'visual-02'),(b'visual01',b'visual02'),(b'prepare-07',b'prepare-08'),(b'run-01',b'run-02')]:
 assert x in b,x;b=b.replace(x,y)
for x,y in [(b"assert cp['revision']==650 and cp['current_Main_HEAD']=='1b3a131320c09f553bd3c2c5e3bd39ee6ecb61f2'",b"assert cp['revision']>=655 and cp['current_Main_HEAD']==read(PREP/'scope.template.json')['source']['head']"),(b"assert sha(mf)=='7f18b5310a855039cef507ddd7093a568a53273a706d63e043ed6946fbc9dfbb'",b"assert sha(mf)==read(PREP/'scope.template.json')['bundle']['manifest_sha256']"),(b"==scope['bundle']['control_sha256']=='95da2a4eedd60a5e38f8a08dbe43e38ebb640ee36b826ae37902e21bb6b13b85'",b"==scope['bundle']['control_sha256']")]:
 assert x in b,x;b=b.replace(x,y)
p.write_bytes(b);print(p)
