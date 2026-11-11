# D03: Native platform policy in the first Harness adapter

ResearchOS owns outer tasks, dispatch, process supervision, event persistence and result presentation. The installed Harness owns model authentication and its native inner tool policies. V1 respects trusted machine/account requirements and never bypasses them.

The earlier `DISABLED` intent could imply that every managed hook/MCP source had been eliminated. That is not established by `--ignore-user-config` or an ordinary MCP-list probe. Revision 2 therefore reports `PLATFORM_POLICY`, independently of execution, filesystem and cancellation verification.

The driver uses fixed safe arguments, a Host-owned per-Run working directory and project-root marker, with the authorized source root separately readonly. It requests optional extensions disabled and does not copy user configuration or credentials. Known policy incompatibility or uncontrolled project inheritance blocks that Run. It does not silently request full access.

This is an architecture decision, not a runtime qualification. Real readonly-boundary, event, cancellation and Windows UI evidence remain required by the V1 acceptance records. Source/unit/build success cannot mark those journeys accepted.
