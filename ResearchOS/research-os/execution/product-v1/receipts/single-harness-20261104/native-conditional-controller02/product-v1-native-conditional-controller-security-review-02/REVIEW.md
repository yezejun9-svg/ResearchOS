# Conditional controller prep02

**APPROVED_SOURCE_FIXTURE_ONLY**. Formal/product increment **0**; no remaining source blockers.

CTRL-F1 is fixed by canonicalizing the fixed Windows source once. CTRL-F2 is fixed by checking both exact B3 addition hashes before launch and reusing the frozen values for final effects checking. Helper and template bytes are unchanged; the template remains blocked.

Root's recorded pure02 run passed all **5 cases**, with no failures or skips. All **11 input rows / 10 unique paths** matched. The original Job stopped with exit 0, **3 cumulative processes**, active zero, no force, timeout or drift. Imports do not activate the runner entrypoint or launch App/helper/Native.

Review itself executed no tests or candidate. Fresh Source3/build/runtime bindings and separate post-stop verification remain required. Exact hashes, case names and limitations are in REVIEW.json. Prior blocked reviews remain unchanged.
