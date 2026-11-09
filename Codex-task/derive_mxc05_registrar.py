from pathlib import Path
p=Path(__file__).resolve().parent/'register_product_v1_mxc_echo05.py';assert not p.exists()
b=p.with_name('register_product_v1_mxc_echo04.py').read_bytes()
for x,y in [(b'rev04-20261105-e91c',b'rev05-20261105-f602'),(b'registration04',b'registration05'),(b'mxc_availability_20261105_e91c',b'mxc_availability_20261105_f602'),(b'preparation-04/product-v1-mxc-availability-security-review-rev04',b'preparation-05/product-v1-mxc-availability-security-review-rev05'),(b'650d24d091a86aa52b6c9779e3f7aff9fcf24dc58ded095af5b012aabd999025',b'ROOT_FILL_REVIEW05_SHA'),(b'8055e053377ed5f837abbe8ee870a5b46f5a214b3360da34ea07b591d93c9fcd',b'f104973eb1ccd5f4009bb6424553f2ec683df2bb0022e8254ca36fbadd15285e'),(b'registered-04',b'registered-05'),(b'register_product_v1_mxc_echo04.py',b'register_product_v1_mxc_echo05.py'),(b"'C:/Windows/System32/cmd.exe','/d'",b"'C:\\\\Windows\\\\System32\\\\cmd.exe','/d'")]:
 assert x in b,x;b=b.replace(x,y)
x=b"assert inner['argv']==";assert b.count(x)==1
b=b.replace(x,b"assert inner['diagnostic_origin']=='mxc_availability_20261105_e91c:local-command-syntax-error' and inner['diagnostic_attempt']==2\nassert inner['argv']==")
p.write_bytes(b);print(p)
