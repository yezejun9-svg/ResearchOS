# Native identity serialization repair

Verdict: **PASS_ASYNC_BOUNDARY_IDENTITY_FIX** at `a7608ad` (integrated `1524356`).

Both native creation-time fields now serialize as decimal strings while retaining Go int64 values. Independent tests passed 33 assertions through nested domain.Decode, canonical JSON and typed round trips, including 2^53+1 and MaxInt64. The original lossy numeric form still fails the unchanged strict decoder.

Root's W10 NativePair and W16 C20 consumer reruns passed; their raw file hashes, two string-valued native receipt identities and FIXTURE acceptance record were reconciled. Prior failure records remain preserved. This is a serialization/consumer compatibility repair, not full S2 or LIVE acceptance.
