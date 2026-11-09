from pathlib import Path
p=Path(__file__).resolve().parent/'register_product_v1_native_policy_test02.py';assert not p.exists();b=p.with_name('register_product_v1_native_policy_test01.py').read_bytes()
for x,y in [(b'tests-01',b'tests-02'),(b'registration01',b'registration02'),(b'development-test01',b'development-test02'),(b'TestHarnessCoordinatorFakeChain$|TestHarnessHostPrincipalActualBinding$',b'TestHarnessCoordinatorFakeChain$|TestHarnessSourceRebindBeforeResume$|TestHarnessHostPrincipalActualBinding$')]:
 assert x in b,x;b=b.replace(x,y)
x=b"cp['revision']==664";assert x in b;b=b.replace(x,b"cp['revision']>=664")
p.write_bytes(b);compile(b,str(p),'exec');print(p)
