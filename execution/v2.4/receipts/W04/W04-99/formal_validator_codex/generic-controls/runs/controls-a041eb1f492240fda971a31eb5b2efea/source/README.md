# Public formal aggregation synthetic controls

Scope: `SYNTHETIC_GENERIC_CONTROLS_NOT_PRODUCT_EVIDENCE`. These tests create isolated fake root authority, byte-bound receipts, independent actor strings, and inert tool files. They exercise the public `execution/v2.4/formal_case_index.py` reader and CAS dependency check. A synthetic result of three accepted cases never contributes real formal acceptance.

The frozen sibling `test_validate.Fixture` is reused only as a fake-data builder; its scratch location is redirected into this directory at runtime. The old validator and four frozen sibling source files are not changed. No product driver, Go command, dispatcher, provider, registry mutation, or real state mutation is executed.

`python -B -X utf8 run_generic.py` retains each actual attempt, exact argv, stdout, stderr, source archive, SHA256 pins, and source-stability result under `runs`. Unchanged failed input is not retried. Temporary fixture trees are removed after each test. The runner separately reads current main state through the public aggregator and retains the result without editing main inputs.

Controls cover the 42-case/22-owner catalog, empty and nonaccepted owners, canonical registration, no candidate glob discovery, valid W04 contribution, source change/add/remove, history preservation, raw hash tampering, modes, final ownership, assertion IDs, verifier identity, observed issuance, conflicting review, global corruption, unsupported owner isolation, CAS file/inventory changes, and retained-registry compatibility.
