# Scope interpretation before DDL

This C-only prototype has not opened a database or executed a migration yet. It must not connect to D: or an old database, change the frozen pure-scalar package, or implement Native/Host/LIVE authorization.

The construction brief at `../contract-design/CONSTRUCTION_BRIEF.md:58` currently combines two statements: the stable intent key includes the Owner authority root; a new root must not reset a continuing failure lineage. A changed root changes that key, so a unique `(project, intent_key)` alone cannot enforce the second statement. Root has been asked to resolve this before the uniqueness schema is frozen.

Other required explicit choices are the scope of approval/intent uniqueness (project or global issuer-qualified identity), and a precisely named prototype DTO. A schema check does not establish that a client-supplied stable key, Owner/root/Host identity or approval is genuine.

The implementation will also need an insert-conflict guard in addition to immutable UPDATE/DELETE triggers: SQLite `INSERT OR REPLACE` can otherwise cause implicit deletion when `recursive_triggers=OFF`. Missing JSON values must not pass CHECK through SQL NULL. Exact body hashing, duplicate/unknown JSON keys, canonical refs and restore schema fingerprints require a separate fixture consumer.
