from pathlib import Path
p=Path(__file__).resolve().parent/'register_product_v1_layout_visual04.py';assert not p.exists();b=p.with_name('register_product_v1_layout_visual03.py').read_bytes()
for x,y in [(b'build-10',b'build-11'),(b'build10',b'build11'),(b'visual-03',b'visual-04'),(b'visual03',b'visual04'),(b'prepare-09',b'prepare-10'),(b'run-03',b'run-04'),(b'>=661',b'>=668')]:
 assert x in b,x;b=b.replace(x,y)
# The original native selector proof is immutable run03, not the new visual run04.
b=b.replace('product-v1-native-path-entry-中文-run-04'.encode(), 'product-v1-native-path-entry-中文-run-03'.encode())
x=b"pins={row['path']:row['sha256'] for row in scope['source']['pins']};pins.update(reg['source_sha256'])";assert x in b
y=b"pins={row['path']:row['sha256'] for row in scope['source']['pins']}\nresolved_partial_pins={}\nfor ref,digest in list(pins.items()):\n observed=sha(WT/ref)\n if digest is None:resolved_partial_pins[ref]=observed;pins[ref]=observed\n else:assert observed==digest,ref\npins.update(reg['source_sha256'])\nfor ref,digest in scope['selector_binding']['source_sha256'].items():\n observed=sha(WT/ref)\n if digest is None:scope['selector_binding']['source_sha256'][ref]=observed\n else:assert observed==digest,ref\nscope['product_acceptance']='NOT_RUN_BUILD11_VISUAL04_ROOT_REGISTERED_PENDING_ACTUAL'\nscope['root_partial_pin_resolution']=dict(source_head=cp['current_Main_HEAD'],basis='CLEAN_COMMITTED_SOURCE_HEAD_AND_COMPLETE_REVIEWED_INTEGRATED_PINS_WITH_VALIDATED_BUNDLE',resolved_source_pins=resolved_partial_pins,template_old_build10_label_corrected=True)";b=b.replace(x,y)
p.write_bytes(b);compile(b,str(p),'exec');print(p)
