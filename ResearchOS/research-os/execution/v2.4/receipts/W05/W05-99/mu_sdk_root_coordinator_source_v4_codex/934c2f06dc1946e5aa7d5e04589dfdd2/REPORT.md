# Root coordinator v4 Source review candidate

Status: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW. This packet is not execution authority, an accepted bootstrap, runtime qualification, or formal acceptance.

The caller consumes actual staged prepare-runtime and finalize-prepare receipts. It never invokes legacy prepare. The pre-draft seed must have an empty draft_goal_id; the PREPARED receipt must identify the actual ordinary CLI Goal. Bootstrap validates one qualification DRAFT Task, zero ordinary Goal Tasks, zero Runs, BudgetLedgerEntry and resource effects. MODEL_TRIAL rechecks those facts through read-only database queries before admission; these queries have not been executed by this Source work.

Initial init/workspace evidence is the exact prior independent component review and its original partial snapshot. The new continuation requires exactly normal-host and cli-goal Jobs. Preparation has two separately pinned invocations and two separately pinned closure records, bound to their original before-resume identities, original fresh observation timing, Job idle state, and producer/watchdog duplicate closure. These records remain inputs: no actual IDs or successful execution fixtures were generated.

Only fixed role trusted_host_binary changes; the remaining 23 roles are reused. Historical trusted_host source/review roles remain historical. The current helper review, compile receipt, source-members list and eight members are separate guarded inputs. That helper review permits zero-provider preparation only; it does not itself authorize a MODEL trial. Independent review of this complete caller and Root execution authority remain mandatory.

Preparation stays outside the one 300-second window. start_trial, issue_go, execute_c7, finalize, run, retained-parent code and R01/R02 behavior retain v3 AST. Limits remain qualification 1 plus ordinary 2, total requested output tokens 8192, one resident parent, no retry. Host profile_hash retains its content digest; C7 uses Hash(ArtifactRef).

Validation: two pure control groups pass, including staged-chain and live-DB-contract positive fixtures, 11 staged-chain negatives, 7 database negatives, and 7 original cleanup negatives. Fixtures are synthetic and run only AST-extracted functions with fake database objects; the candidate module was not imported, and no native, WinAPI, actual SQL, or provider call occurred. Prior 40 + 1 + 2 controls are reused, not rerun. Both constructors succeeded first attempt. Constructor 1 outputs are retained verbatim in constructor1-snapshot for provenance.

One new actual tool failure is recorded as Root 739: a mistaken P05 path expansion during context recovery. Root 740 is an rg no-match observation, not an actual failure. Full observed failure output and both constructor results are retained. No Main or canonical files were changed; earlier Source packages and other agents' files are untouched.

