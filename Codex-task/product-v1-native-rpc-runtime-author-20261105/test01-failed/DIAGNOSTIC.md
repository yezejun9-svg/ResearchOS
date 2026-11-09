Origin: native-rpc-b1:same-pipe-stderr-warning-order

Test01 ended CHILD_NONZERO_STOPPED, exit 1, stop proved, input drift false. It
executed only the Go test executable; Native and model were not invoked.

The failure was in the fixture assertion, not in capture ordering. The fake
child sends the initialize response on stdout before it emits the warning on
stderr, then sends the thread/start response on stdout. Captured raw bytes in
stdout.raw lines 75-78 show exactly that order: id 1, warning, id 2,
thread/started. The original test incorrectly asserted that the warning was
the first byte of the *entire* pipe, despite the preceding initialize response.

The runtime passes the same underlying os.Pipe write end to stdout and an
inheritable DuplicateHandle of that write end to stderr. It does not merge two
Go readers. The revised assertion verifies the known child write order and
the existing failure/zero-turn checks remain. The original test01 source and
raw receipt are preserved here; test02 requires a new registered scope.
