"""Prepare a fresh owner only from the new, unchanged genuine delivery."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'prepare_br8_owner_check.actual.root.py').read_bytes()
changes=[
 (b'capture-a7067db724ce4a34a71a01055c9e00c8/result.json',b'capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/result.json'),
 (b'8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f',b'04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8'),
 (b'prospective-owner.actual.root.json',b'prospective-owner.literal02.actual.root.json'),
 (b'check.actual.extras.root.json',b'check.literal02.actual.extras.root.json')]
fixed=raw
for old,new in changes:assert fixed.count(old)==1;fixed=fixed.replace(old,new)
inverse=fixed
for old,new in reversed(changes):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse==raw
exec(compile(fixed,str(S/'prepare_br8_owner_check.actual.root.py'),'exec'),dict(__name__='__main__',__file__=str(S/'prepare_br8_owner_check.actual.root.py')))
