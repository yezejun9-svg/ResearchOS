# r2mutants2.py - round-2 reviewer matrix part 2: re-runs R2-M4 after an environmental
# flake, and adds four mutants around stdout purity, the run delegation, and the two
# unexercised local-precondition mirrors in apps/cli/cli_v2.go.
import importlib.util, os

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("r2base", os.path.join(here, "r2mutants.py"))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

base.MUTANTS = [
 {"id": "R2-M4-table-claims-a-method-the-code-never-sends", "file": "apps/cli/cli_contract.go",
  "old": '"session.attach + session.control", []string{"W0503-RESUME-SENDS-SESSION-ATTACH"',
  "new": '"session.attach + session.control + session.handoff", []string{"W0503-RESUME-SENDS-SESSION-ATTACH"',
  "expected": ["W0503-TABLE-ROWS-ALL-PROVEN", "W0503-COMMANDS-ALL-HANDLED"],
  "claim": "the command table's method column is checked against what the CLI actually sent"},
 {"id": "R2-M10-doctor-puts-a-human-line-on-stdout", "file": "apps/cli/main.go",
  "old": "\t\tline, _ := json.Marshal(out)\n\t\tfmt.Println(string(line))",
  "new": "\t\tfmt.Println(\"doctor: human-readable diagnostic on stdout\")\n\t\tline, _ := json.Marshal(out)\n\t\tfmt.Println(string(line))",
  "expected": ["W0503-DOCTOR-UP-COMPLETES", "W0503-DOCTOR-DOWN-EXIT-1", "W0503-DOCTOR-NOT-FOUND-REFUSES"],
  "claim": "non-interactive stdout is JSONL only for every command (card negative: mixed logs on stdout must fail)"},
 {"id": "R2-M11-accepted-run-shape-always-matched", "file": "apps/cli/cli_run_contract.go",
  "old": "\t_, has := firstPositional(args)\n\treturn !has",
  "new": "\t_, has := firstPositional(args)\n\t_ = has\n\treturn true",
  "expected": ["W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS"],
  "claim": "the contract's run syntax reaches the protocol client rather than only the accepted cascade"},
 {"id": "R2-M12-command-id-pattern-mirror-removed", "file": "apps/cli/cli_v2.go",
  "old": "\tif !commandIDPattern.MatchString(ctx.commandID) {\n\t\treturn nil, \"MISSING_FIELD:command_id\"\n\t}",
  "new": "\t_ = commandIDPattern",
  "expected": ["W0503-MALFORMED-HOST-REPLY-FAILS", "W0503-STATUS-SENDS-HOST-STATUS"],
  "claim": "the client refuses locally what the core would refuse (command_id shape)"},
 {"id": "R2-M13-empty-payload-mirror-removed", "file": "apps/cli/cli_v2.go",
  "old": "\tif c.payload == \"EmptyPayload\" && len(keys) > 0 {\n\t\treturn nil, \"UNEXPECTED_PAYLOAD_KEYS:\" + strings.Join(sortedKeys(keys), \",\")\n\t}",
  "new": "\t_ = sortedKeys",
  "expected": ["W0503-STATUS-SENDS-HOST-STATUS"],
  "claim": "the client mirrors the schema's EmptyPayload rule for host.status and session.get"},
]
base.main()
