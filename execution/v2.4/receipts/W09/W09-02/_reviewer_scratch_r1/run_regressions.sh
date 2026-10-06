#!/bin/sh
cd "D:/作品集/ResearchOS/research-os" || exit 1
export PYTHONIOENCODING=utf-8 GOTOOLCHAIN=local
export RESEARCHOS_GO="D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe"
OUT="execution/v2.4/receipts/W09/W09-02/_reviewer_scratch_r1"
for spec in "test.retrieval|--task-id W09|--check-id W09-01" "test.domain|--task-id W03|--check-id W03-01" "test.research.fixture|--task-id W08|--check-id W08-01"; do
  key=$(echo "$spec" | cut -d'|' -f1)
  echo "### $key"
  python execution/command_dispatcher/dispatch.py $key $(echo "$spec" | cut -d'|' -f2-) 2>&1 | tail -1
done
