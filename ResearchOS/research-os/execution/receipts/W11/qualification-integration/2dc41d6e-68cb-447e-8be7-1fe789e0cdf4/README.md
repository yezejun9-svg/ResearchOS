# Qualification integration public test receipt

This test injects an unexported preparedQualification using a valid public
synthetic SafeSummary. LIVE object fields exercise the trusted admission branch;
no actual service query, credential read, formal dataset or provider call occurs.
The independent service/binary/OS boundary is outside this test's scope.

Real SQLite and production entity schemas verify acceptance followed by a stored
FAILED/ADVISORY qualification, even with requested BOUNDED_AUTO. The exact sealed
aggregate is checked and the synthetic private-body canary is absent from uploads.
Fourteen drift scenarios reject, with dataset bytes, protected descriptor and
sealed aggregate mutations rejected earlier by SQLite immutable-seal triggers.
Current grants/credential are reauthenticated between fixture transactions.
The existing HTTP fixture qualification-closed test also passes in this command.
