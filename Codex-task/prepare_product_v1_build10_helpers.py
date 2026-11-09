from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'prepare_product_v1_integration.py';b=p.read_bytes()
for x,y in [(b"'mobile-conversation-layout'],required",b"'mobile-conversation-layout','mobile-scroll-region'],required"),(b"'mobile-conversation-layout':'fix(desktop): keep narrow conversation composer in normal document flow'",b"'mobile-conversation-layout':'fix(desktop): keep narrow conversation composer in normal document flow','mobile-scroll-region':'fix(desktop): bound mobile workbench scrolling above navigation'"),(b"if a.kind=='mobile-conversation-layout':",b"if a.kind in ('mobile-conversation-layout','mobile-scroll-region'):")]:
 assert b.count(x)==1,x;b=b.replace(x,y)
x=b"out.parent.mkdir(parents=True,exist_ok=True);";assert b.count(x)==1
b=b.replace(x,b"if a.kind=='mobile-scroll-region':plan['next']='Build10 from complete reviewed mobile viewport source, then new main-scroll-aware real visual03 controller/scope. Preserve original visual01/02 failures; actual main/document/transcript initial0 and all original overlap/overflow/control hit checks required. MXC fixed local echo diagnosis finished2/2, startup only; split-read profile/model/cancel/resume remain unverified. No extra echo, model task replay or permission/config/OS changes.'\n"+x);p.write_bytes(b)
p=HERE/'prepare_product_v1_desktop_build10.py';assert not p.exists();b=p.with_name('prepare_product_v1_desktop_build09.py').read_bytes()
for x,y in [(b'build-09',b'build-10'),(b'build09',b'build10'),(b'producer-09',b'producer-10'),(b'>=654',b'>=660'),(b'>=11',b'>=12')]:
 assert x in b,x;b=b.replace(x,y)
p.write_bytes(b)
p=HERE/'register_product_v1_layout_visual03.py';assert not p.exists();b=p.with_name('register_product_v1_layout_visual02.py').read_bytes()
for x,y in [(b'build-09',b'build-10'),(b'build09',b'build10'),(b'visual-02',b'visual-03'),(b'visual02',b'visual03'),(b'prepare-08',b'prepare-09'),(b'run-02',b'run-03'),(b'>=655',b'>=661')]:
 assert x in b,x;b=b.replace(x,y)
p.write_bytes(b);print('C helpers prepared; no D write, source integration or process launch')
