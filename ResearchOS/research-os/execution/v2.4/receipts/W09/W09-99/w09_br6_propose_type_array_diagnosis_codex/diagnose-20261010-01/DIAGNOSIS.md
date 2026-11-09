Root original1208 is a Main internal tuple/list contract mismatch.

Actual Root BR6 propose called the sealed bridge __main__ and failed at Main _native line 642. The original call/output three-line capture and source byte ranges were verified. This diagnosis does not replace that real failure with a simulated Root run.

ops/ci/w09_formal_router.py stores every NATIVE, FORMAL and SELECTED value as a tuple. Main _router_contract uses ast.literal_eval and returns these tuples unchanged. Main _native gives FORMAL[route] directly to exact_ids; formal_case_index.sequence requires type(value) is list. Every one of the six valid routes therefore fails TYPE_ARRAY before Native/Mode validation.

NF6's accepted component review does not contradict this. prepare_review.py lines 40-48 extracts router literals and explicitly converts IDs/tests to lists for its review records. Its reused review_group calls closure.verify_native/verify_owned directly; publication lines 67-76 calls closure.verify_mode with a route tuple and prepared ctx/native records. These component checks do not call formal_profile_w09._native and do not claim formal parent acceptance.

The candidate patch belongs in Main _native: accept only an exact tuple/list from the trusted router, then pass list(value) into the existing exact_ids. Do not broaden sequence globally. Do not patch only BR6: verify_owner reconstructs the router and reaches the same defect through _dispatches. Do not rewrite router literals as the minimal fix: router.py belongs to producer Source21, while formal_profile_w09.py does not.

The static patch and candidate file are stored only in this diagnosis directory. Six pure boundary examples show original TYPE_ARRAY and candidate PASS. Nine counterexamples verify list compatibility and rejection of duplicate/missing/extra/non-text/empty IDs and dict/set/string containers. A dictionary with expected keys demonstrates why unguarded list conversion is insufficient. These are pure helper checks; no Main module, _native, Root stage, Native, SQL, model, dispatcher or TP was executed. Prior successful controls were not replayed.

After separate authorization/adoption and independent review, refresh the context's Main source pin and all dependent Root authority/snapshot references, then exercise the actual Main _native path with the sealed NF6 and Mode inputs. Original1208 remains failed. Existing Native evidence can remain reusable only while its exact Source21 pins remain unchanged. Six consumers and actual final acceptance gates remain outstanding.
