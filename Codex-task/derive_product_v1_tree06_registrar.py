from pathlib import Path
s=Path('register_product_v1_tree_diagnostic05.py').read_text(encoding='utf8')
s=s.replace('product-v1-real-electron-tree-diagnostic-revision-04','product-v1-real-electron-tree-diagnostic-revision-05')
s=s.replace('product-v1-tree-diagnostic-05','product-v1-tree-diagnostic-06').replace('product-v1-tree-diagnostic-run-05','product-v1-tree-diagnostic-run-06').replace('tree-diagnostic-05','tree-diagnostic-06')
s=s.replace('88e4b33142d8e8274ec0edcc99314f4f867a749217f869298ae8e7fdc52d9d47','8d2811eb8e8c3fd93cbbf460b5562c899df88cb1458dc522fbadad5def284875')
p=Path('register_product_v1_tree_diagnostic06.py');assert not p.exists();p.write_bytes(s.encode('utf8'))
print('Prepared new optional-type diagnostic06 registrar, not executed')
