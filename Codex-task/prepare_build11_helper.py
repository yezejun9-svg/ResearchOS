from pathlib import Path
p=Path(__file__).resolve().parent/'prepare_product_v1_desktop_build11.py';assert not p.exists();b=p.with_name('prepare_product_v1_desktop_build10.py').read_bytes()
for x,y in [(b'build-10',b'build-11'),(b'build10',b'build11'),(b'producer-10',b'producer-11'),(b'>=660',b'>=667'),(b'>=12',b'>=14'),(b'>=43',b'>=48')]:
 assert x in b,x;b=b.replace(x,y)
p.write_bytes(b);compile(b,str(p),'exec');print(p)
