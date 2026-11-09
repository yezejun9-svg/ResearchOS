from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE/'prepare_product_v1_clean_build.py').read_text(encoding='utf8')
changes={
 "product-v1-build-20261104';OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build-scope'":"product-v1-build-03-20261104';OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build03-scope'",
 "cp['revision']>=609":"cp['revision']>=615",
 "assert len(integrated)==3":"assert len(integrated)>=5",
 " for ref,digest in item['source_sha256'].items():assert ref not in pins and sha(ROOT/ref)==digest;pins[ref]=digest":" for ref,digest in item['source_sha256'].items():pins[ref]=digest",
 "assert len(pins)==30":"assert len(pins)>=39\nfor ref,digest in pins.items():assert sha(ROOT/ref)==digest",
 "codex/product-v1-build-20261104":"codex/product-v1-build-03-20261104",
 "desktop-v1-build-01":"desktop-v1-build-03",
 "producer-01":"producer-03",
 "product-v1-build-01.json":"product-v1-build-03.json",
 "scope_id='product-v1-build-01'":"scope_id='product-v1-build-03'",
 "prepare_product_v1_clean_build.py').write_bytes":"prepare_product_v1_desktop_build03.py').write_bytes",
}
for old,new in changes.items():
 assert source.count(old)>=1,old
 source=source.replace(old,new)
dest=HERE/'prepare_product_v1_desktop_build03.py';assert not dest.exists();dest.write_bytes(source.encode('utf8'))
compile(source,str(dest),'exec')
print('Prepared inert Desktop build03 registrar; requires independently reviewed assistant-home integration.')
