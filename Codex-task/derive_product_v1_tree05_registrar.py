from pathlib import Path
s=Path('register_product_v1_tree_diagnostic04.py').read_text(encoding='utf8')
s=s.replace('product-v1-real-electron-tree-diagnostic-revision-02','product-v1-real-electron-tree-diagnostic-revision-03')
s=s.replace('product-v1-tree-diagnostic-04','product-v1-tree-diagnostic-05').replace('product-v1-tree-diagnostic-run-04','product-v1-tree-diagnostic-run-05').replace('tree-diagnostic-04','tree-diagnostic-05')
s=s.replace('32bbc82cebcc1d6693588639bfc3dd81eb685c7ed4c856f512dc42aa61c4c40a','def290342be6417bff524cac2e0a3c0779429851e3c87160381600c268ca3eb6')
s=s.replace('d3e37e333fa85fe57b6951292a458f73b08a2f801a2e9b997089599ec044ade4','029a96be3fecc0e4154acdeb402c90ccf1120783492ba1b9d08aa840ce5ab732')
p=Path('register_product_v1_tree_diagnostic05.py');assert not p.exists();p.write_bytes(s.encode('utf8'))
print('Prepared new direct-HWND diagnostic05 registration, not executed')
