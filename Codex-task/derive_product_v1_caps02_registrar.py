from pathlib import Path
s=Path('register_product_v1_same_host_caps.py').read_text(encoding='utf8')
s=s.replace("scope.update(status='ROOT_APPROVED_SINGLE_CAPS',scope_nonce=secrets.token_hex(24));assert not Path(scope['run_root']).exists()", "scope.update(status='ROOT_APPROVED_SINGLE_CAPS',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-cli-same-host-caps-run-02'));assert not Path(scope['run_root']).exists()")
s=s.replace('product-v1-cli-same-host-caps-01','product-v1-cli-same-host-caps-02').replace('single-harness-20261104/cli-same-host-caps-01','single-harness-20261104/cli-same-host-caps-02')
p=Path('register_product_v1_same_host_caps02.py');assert not p.exists();p.write_bytes(s.encode('utf8'))
print('New scope02 registrar uses canonical Windows path; prior consumed01 is untouched')
