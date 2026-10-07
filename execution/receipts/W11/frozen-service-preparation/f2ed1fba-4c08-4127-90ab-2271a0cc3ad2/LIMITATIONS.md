# Preparation evidence limits

These are public-fixture/native same-user tests and read-only deployment Plan.
No UAC/service installation, real credential read, formal holdout generation/read
or live provider call occurred. They do not establish installed identity isolation
or formal W11-G04/A08 pass.

Earlier development loopback tests failed with reused HTTP connections on Windows;
increasing only the fixture timeout did not resolve it. The final service and
fixture transports both disable keep-alive connection reuse; the source-frozen
recorded suite passes in under three seconds. Real timeout remains 60 seconds.

Terminal fixture JSON is 2663 bytes under the fixed 4096-byte protocol cap.
All 24 frozen public assertions and six native broker assertions passed.
The existing 41 protected-domain assertions separately passed at the same source.

The deployment script parsed and its embedded C# compiled. The full elevated
installer, virtual-account DPAPI profile behavior and real endpoint reachability
remain to be verified only after explicit user authorization.
