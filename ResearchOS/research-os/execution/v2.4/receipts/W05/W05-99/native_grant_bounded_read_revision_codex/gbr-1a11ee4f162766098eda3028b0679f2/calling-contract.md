# Bounded helper calling contract

The CLI and exact request schema remain the old GPA contract. Invoke with the reviewed new helper Source path and explicit REQUEST_PATH REQUEST_SHA256 REQUEST_BYTES using Python -I -S -B -X utf8. All digests are prefixed lowercase sha256. This Source only fixes GPA-R01 bounded input reads; it does not authorize runtime execution or approve a grant.

Root may first invoke the separately reviewed root_build_grant_archive_request.py with a concrete existing Snapshot ref3 and --select-full-current-grant-public-pins. That inert builder only writes the request; Root still reviews it and separately invokes this helper. A successful helper prints GRANT_PUBLIC_ARCHIVE_OK plus manifest ref3. Guard closure, exact copies and full/partial closure fields remain unchanged. No signing, approval, grant TTL refresh or original Owner/nine-case/formal42 acceptance is inferred.

