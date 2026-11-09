# Qualification helper build: registration instructions

This directory contains an exact, minimal helper-only Go source tree and a draft original-f13 BUILD scope. It is preparation material, not authorization and not an executed build.

The selected files are the two independently reviewed B3 producer files (`internal/qualificationprobe/plan.go` and `cmd/researchos-qualification-helper/main_windows.go`) plus Main13e6 `go.mod` and `go.sum`. All four retain their module-relative paths and match the recorded SHA256 values. The selected helper files match the approved B3 manifest `522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2` and Main source HEAD `13e6b8f1da9f61d6c77982f2a368204652b475e4`.

The scope template proposes exactly:

`go build -trimpath -buildvcs=false -o C:\Users\yqyyds\Documents\Codex\2026-11-04\task\product-v1-native-helper-build01\buildout\qualification-helper.exe ./cmd/researchos-qualification-helper`

The scope pins all four source/module inputs, the public Go SDK binary, the original f13 controller, and the approved B3 preparation manifest. Its environment pins local Go only, disables network module resolution, and directs Go cache/temp writes to the new C candidate. Budgets are 600 seconds, 48 processes, 6144 MiB, and 8 MiB raw output.

Before any registration or execution, Root must independently review this exact command and scope, verify source/module/SDK/controller/manifest pins, and register a fresh unique BUILD scope with the original f13 controller. Do not edit the template in place after review; produce a new revision if pins or command change. No CONTROL entry or execution scope has been registered here.

This is helper-only source binding. It does not bind or certify the complete ResearchOS application. No Go command, build, test, helper, Native, CLI, model, or credential/private-config access occurred in this preparation.

