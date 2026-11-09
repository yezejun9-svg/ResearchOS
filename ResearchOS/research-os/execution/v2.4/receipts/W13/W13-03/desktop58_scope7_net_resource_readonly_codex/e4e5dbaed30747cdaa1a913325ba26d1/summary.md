# Scope7 net.exe read-only resource candidate

Actual first rejection: `bb3e638c8b5b6ef80847e364aeef2796cad25d3539cf9b41d3820fa48943e777` / 81920 bytes, generation 806. `net1.exe` is a static potential child only; no actual loaded event was seen.

The System32 explicit-file import graph closed at 325 files and 12920 edges without its 2048-file cap. 243 explicit files are absent from the frozen 1303-file runtime list. The graph still has 6365 unresolved edge instances, mainly API-set names absent from this machine's static `.apiset` namespace; export forwarders and dynamic loads were not examined. Treat all discovered files as future resource candidates, not an authorized loader whitelist.

Frozen events show node.exe generation 803, cmd.exe 804, conhost.exe 805, then the rejected net.exe load at 806. They do not include parent PID edges or net.exe command line. The builder source's next call after the completed web-module-junction receipt is react-build; attribution to that call is an inference.

No native application, builder, Go, Git, or network command was run; this branch did not write Main, canonical metadata, or the old Scope7 receipts.
