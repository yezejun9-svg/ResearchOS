The earlier status document listed the two origins known before sealing.
Two later metadata-only origins are now additionally preserved: 3d077c
(Python1/outer1, locator incorrectly required `func ` and missed the existing
`func(v ...) evaluate` spelling) and 86f70b (Python1/outer1, unmatched parenthesis
in a read-only inspection command). Thus this new revision preparation has four
new metadata origins. These are separate from the previous four author origins
and the peer's eade2d; none are product failures or recounted historical events.

062f8f outer0 independently displayed the actual evaluate declaration at line
1515. The original seal.py remains untouched. The new seal.v2.py only corrects
metadata line matching and retains the new failure references; no proposed Go
source, test source, patch or selector changed. prepare-seal-v2.py produced the
new script under actual Python0/outer0 (284e8b), using AST checks, without
executing the candidate, Go, SQL or any product. The final seal invocation's
actual tool result is reported separately after the manifest is immutable.
