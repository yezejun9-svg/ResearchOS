# UI repair v2 independent review

Decision: **REQUEST_CHANGES** for candidate `9602f61c05325fc9bd1b523398a8f9721eded72e` over Main `292ad860f9e76cf2795d5a3010da1d114d01ff56`.

The original whitespace-refusal and already-ACKNOWLEDGED remount paths are repaired in independent tests. One P1 remains: if the original HTTP response completes after the component has unmounted and a replacement component has captured its pending payload, the old component deletes the shared Map entry without updating the replacement component. That component remains locked and offers “continue the same configuration”; clicking it constructs a new command at the next revision. Raw evidence shows `review-3-host.configure` at revision 1 followed by `review-6-host.configure` at revision 2.

`independent-review.json` contains the exact trigger, current code lines, evidence references and repair requirement. `reviewer-dom-results.json` and the matching raw HTTP directory prove the result with actual Chromium DOM, candidate IPC, the current source-bound Go validator and synthetic loopback HTTP. Three positive DOM flows also pass. The 15 selected source-bound boundary checks have 14 passes and one retained stale test expectation; remote server `NOT_SENT` cannot release the barrier. The inherited host namespace weakness is separately recorded with a synthetic reproduction and is not attributed to this repair.

7432 input bindings were independently verified, including the 972-file author manifest, validator inputs, binary/module inventory and candidate Git content. There were zero model/external calls and no normal Electron/Core, product, parent or formal acceptance. All writes are confined to this review receipt directory. Existing blocked caches were not deleted.
