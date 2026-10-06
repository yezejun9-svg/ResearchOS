# W13 targeted review-fix execution evidence

Application source: a366288. Replay test: ab52b4c.
Latest complete receipt: 20260930T124023Z (DEVELOPMENT_ONLY_BROWSER).

The real temporary SQLite/control server and browser exercise 12 URL/selection
steps: A to B, browser back/forward, reload and reauthentication, server search
selection, preservation of other query parameters and filter state, query removal,
and return to the prior selection. The measured ordinary request timeout is
30.21 seconds; loading ends with an explanatory error and actual service retry
succeeds. Navigation cancellation does not leak an error into the next screen.

Measured desktop, 320 CSS px, mobile stage drawer, and native Chromium 200 percent
zoom (outerWidth 640, innerWidth 320, DPR 2, visualViewport.scale 1) have no whole
page horizontal overflow. Important tags and stage counts use 14 CSS px, auxiliary
text and mobile navigation use at least 12 CSS px. Text horizontal bounds were
also checked. Chromium-native zoom was used, not CSS zoom. No physical phone was
used and no formal AcceptanceReceipt was created.

The application produced zero pageerror events. Playwright itself emitted
CancelledError callbacks when disposing deliberately intercepted pending requests;
runner.stderr.log retains them. These are test transport cleanup warnings, not
application exceptions, and are not hidden from the evidence.

20260930T123757Z is the earlier development pass. Its drawer screenshots were
captured at animation start, and its test source was not yet committed. It is
retained for provenance and superseded by the latest replay, which waits for the
drawer right edge to reach the viewport before capture and checks text bounds.
The native 200 percent screenshot renderer shows extra blank space after scrolling;
viewport/DPR/overflow and computed-font evidence are recorded separately in JSON.

All test-created server/browser processes were closed and the new task-specific
temporary directory removed. No prior or policy-rejected directory was touched.
