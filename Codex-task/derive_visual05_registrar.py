from pathlib import Path
p=Path(__file__).resolve().parent;src=(p/'register_product_v1_layout_visual04.py').read_text(encoding='utf8');dest=p/'register_product_v1_layout_visual05.py';assert not dest.exists()
src=src.replace('layout-visual-04','layout-visual-05').replace('layout-visual-中文-run-04','layout-visual-中文-run-05').replace('VISUAL04','VISUAL05').replace("register_product_v1_layout_visual04.py","register_product_v1_layout_visual05.py")
needle="scope['product_acceptance']='NOT_RUN_BUILD11_VISUAL05_ROOT_REGISTERED_PENDING_ACTUAL'"
assert needle in src
src=src.replace(needle,"scope['native_picker']['validation_warning']['source_sha256']=pins['internal/host/native_folder_windows.go']\n"+needle)
dest.write_text(src,encoding='utf8');print(dest)
