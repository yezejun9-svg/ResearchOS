from pathlib import Path
s=Path('register_product_v1_tree_diagnostic.py').read_text(encoding='utf8')
s=s.replace('product-v1-real-electron-tree-diagnostic-01','product-v1-real-electron-tree-diagnostic-revision-02')
s=s.replace('product-v1-tree-diagnostic-03','product-v1-tree-diagnostic-04').replace('product-v1-tree-diagnostic-run-03','product-v1-tree-diagnostic-run-04')
s=s.replace('build-05','build-06').replace('build05-scope','build06-scope').replace('tree-diagnostic-03','tree-diagnostic-04')
s=s.replace('a7e38ceecd654e63b6689556c18ec57346b8ae4390068bcd3e80d28a4ede692d','32bbc82cebcc1d6693588639bfc3dd81eb685c7ed4c856f512dc42aa61c4c40a')
p=Path('register_product_v1_tree_diagnostic04.py');assert not p.exists();p.write_bytes(s.encode('utf8'))
print('Prepared new diagnostic04 registrar, not executed')
