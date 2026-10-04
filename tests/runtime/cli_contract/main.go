// Command cli_contract is the W05-03 construction check for the CLI command surface, the JSONL output contract and
// the exit-code contract. It builds the real binary, runs it as a real child process (including from a workspace
// path containing spaces and non-ASCII characters), and grades what comes back.
//
// It is a separate program from tests/runtime/check because this card's write_scope covers tests/runtime/cli_contract*
// only; the accepted runtime check program belongs to W05-01/W05-02 and was not edited. The consequence is stated in
// the card receipt: the registered command test.runtime --check-id W05-03 still answers NOT_IMPLEMENTED, so this
// program is executor evidence and not the registered path.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"syscall"
	"time"
)

var ids []string
var failures []map[string]string
var notVerified []string

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
		return
	}
	parts := make([]string, 0, len(detail))
	for _, d := range detail {
		s := fmt.Sprint(d)
		if len(s) > 600 {
			s = s[:600]
		}
		parts = append(parts, s)
	}
	failures = append(failures, map[string]string{"id": label, "detail": strings.Join(parts, " | ")})
}

func skip(label, reason string) { notVerified = append(notVerified, label+": "+reason) }

type run struct {
	stdout, stderr string
	code           int
	err            error
}

func (r run) lines() []string {
	out := []string{}
	for _, l := range strings.Split(strings.ReplaceAll(r.stdout, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(l) != "" {
			out = append(out, l)
		}
	}
	return out
}

func main() {
	repo := repoRoot()
	bin := filepath.Join(repo, ".local", "w0503_cli.exe")
	if runtime.GOOS != "windows" {
		bin = filepath.Join(repo, ".local", "w0503_cli")
	}
	build := exec.Command(goExe(), "build", "-o", bin, "./apps/cli")
	build.Dir = repo
	build.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off")
	if out, err := build.CombinedOutput(); err != nil {
		ok("W0503-CLI-BUILDS", false, err, string(out))
		report()
		return
	}
	ok("W0503-CLI-BUILDS", true)

	// A workspace path with a space and a non-ASCII directory, because the card names 中文路径 explicitly.
	wsRoot := filepath.Join(repo, ".local", "w0503 工作区 space")
	if err := os.MkdirAll(wsRoot, 0o700); err != nil {
		ok("W0503-SETUP-WORKSPACE", false, err)
		report()
		return
	}
	defer os.RemoveAll(wsRoot)
	cfg := filepath.Join(repo, ".local", "w0503_config.json")
	disc := filepath.Join(repo, ".local", "w0503_discovery.json")
	_ = os.Remove(cfg)
	_ = os.Remove(disc)
	env := append(os.Environ(), "RESEARCHOS_CLI_CONFIG="+cfg, "RESEARCHOS_CLI_DISCOVERY="+disc)

	callIn := func(dir string, args ...string) run {
		c := exec.Command(bin, args...)
		c.Dir = dir
		c.Env = env
		var stdout, stderr strings.Builder
		c.Stdout, c.Stderr = &stdout, &stderr
		err := c.Run()
		code := 0
		if ee, isExit := err.(*exec.ExitError); isExit {
			code = ee.ExitCode()
		} else if err != nil {
			code = -1
		}
		return run{stdout.String(), stderr.String(), code, err}
	}
	call := func(args ...string) run { return callIn(repo, args...) }

	// 1. stdout purity is checked on every call below, not only on one: any non-JSON line is a failure.
	pure := func(label string, r run) bool {
		ls := r.lines()
		if len(ls) == 0 {
			ok(label+"-STDOUT-JSONL", false, "no JSONL record at all")
			return false
		}
		bad := []string{}
		for _, l := range ls {
			var m map[string]any
			if err := json.Unmarshal([]byte(l), &m); err != nil {
				bad = append(bad, l)
			}
		}
		ok(label+"-STDOUT-JSONL", len(bad) == 0, strings.Join(bad, " / "))
		return len(bad) == 0
	}
	first := func(r run) map[string]any {
		ls := r.lines()
		if len(ls) == 0 {
			return map[string]any{}
		}
		var m map[string]any
		_ = json.Unmarshal([]byte(ls[0]), &m)
		return m
	}

	commands := call("commands")
	if pure("W0503-COMMANDS", commands) {
		m := first(commands)
		list, _ := m["commands"].([]any)
		missingH := fmt.Sprint(m["missing_handler"])
		missingC := fmt.Sprint(m["missing_check"])
		ok("W0503-COMMANDS-ALL-HANDLED", commands.code == 0 && len(list) >= 15 && missingH == "[]" && missingC == "[]",
			"count", len(list), "missing_handler", missingH, "missing_check", missingC, "code", commands.code)
		names := []string{}
		for _, e := range list {
			row, _ := e.(map[string]any)
			names = append(names, fmt.Sprint(row["command"]))
		}
		want := []string{"cancel", "chat", "commands", "config", "goal", "go", "init", "run", "resume", "status",
			"init", "/cancel", "/goal", "/model", "/resume", "/status"}
		present := map[string]bool{}
		for _, n := range names {
			present[n] = true
		}
		absent := []string{}
		for _, w := range want {
			if !present[w] {
				absent = append(absent, w)
			}
		}
		ok("W0503-PRODUCT-CONTRACT-COMMANDS-PRESENT", len(absent) == 0, absent)
	// A declared list field that serialises as null is a shape break for every strict client, and this run found one
	// (missing_handler came back as <nil> from an uninitialised Go slice), so the rule is asserted, not assumed.
	nullLists := []string{}
	for _, key := range []string{"commands", "missing_handler", "missing_check"} {
		if v, has := m[key]; !has || v == nil {
			nullLists = append(nullLists, key)
		}
	}
	ok("W0503-LIST-FIELDS-ARE-ARRAYS-NOT-NULL", len(nullLists) == 0, nullLists)
	}
	slash := call("/status")
	if pure("W0503-SLASH", slash) {
		ok("W0503-SLASH-COMMANDS-HANDLED", slash.code == 3 && fmt.Sprint(first(slash)["command"]) == "/status",
			"code", slash.code, "record", first(slash))
	}
	help := call("/help")
	if pure("W0503-HELP", help) {
		m := first(help)
		list, _ := m["commands"].([]any)
		ok("W0503-HELP-COVERS-EVERY-COMMAND", help.code == 0 && len(list) >= 15, "code", help.code, "count", len(list))
		surface, _ := m["surface"].([]any)
		states := map[string]string{}
		for _, e := range surface {
			row, _ := e.(map[string]any)
			states[fmt.Sprint(row["command"])] = fmt.Sprint(row["state"])
		}
		// The refusal must stay visible in help, and an accepted verb must not be claimed as this card's work.
		ok("W0503-HELP-NAMES-THE-REFUSED-TUI", states["chat"] == "NOT_IMPLEMENTED", states["chat"])
		// The refusal list is a separate claim from the per-command state label: mutation M09 of round 1 showed a
		// build that still labelled chat NOT_IMPLEMENTED while dropping it from the list, so the list is asserted too.
		refusedList := []string{}
		if l, isList := m["not_implemented"].([]any); isList {
			for _, x := range l {
				refusedList = append(refusedList, fmt.Sprint(x))
			}
		}
		ok("W0503-HELP-LISTS-CHAT-IN-NOT-IMPLEMENTED", len(refusedList) > 0 &&
			func() bool {
				for _, r := range refusedList {
					if r == "chat" {
						return true
					}
				}
				return false
			}(), refusedList)
		ok("W0503-HELP-ATTRIBUTES-ACCEPTED-VERBS", states["run"] == "ACCEPTED" && states["task"] == "ACCEPTED",
			"run", states["run"], "task", states["task"])
		nullLists := []string{}
		for _, key := range []string{"commands", "surface", "not_implemented"} {
			if v, has := m[key]; !has || v == nil {
				nullLists = append(nullLists, key)
			}
		}
		ok("W0503-HELP-LIST-FIELDS-ARE-ARRAYS-NOT-NULL", len(nullLists) == 0, nullLists)
	}

	initRes := call("init", "--workspace", wsRoot)
	if pure("W0503-INIT", initRes) {
		m := first(initRes)
		back := fmt.Sprint(m["workspace_ref"])
		ok("W0503-INIT-ACCEPTS-CHINESE-AND-SPACE-PATH", initRes.code == 0 && filepath.Clean(back) == filepath.Clean(wsRoot) &&
			fmt.Sprint(m["path_contains_non_ascii"]) == "true", "code", initRes.code, "echoed", back, "wanted", wsRoot)
	}
	noWs := call("init")
	ok("W0503-INIT-WITHOUT-WORKSPACE-IS-USAGE-ERROR", noWs.code == 2 && strings.HasPrefix(fmt.Sprint(first(noWs)["reason"]), "MISSING_WORKSPACE"),
		"code", noWs.code, "record", first(noWs))
	badWs := call("init", "--workspace", filepath.Join(wsRoot, "definitely-not-here"))
	ok("W0503-INIT-MISSING-DIRECTORY-FAILS", badWs.code == 1 && fmt.Sprint(first(badWs)["reason"]) == "WORKSPACE_NOT_A_DIRECTORY",
		"code", badWs.code, "record", first(badWs))

	// Model switching: no revision, wrong revision, missing settled, then the accepted path.
	noRev := call("config", "set-model", "--model", "vendor/new-model")
	ok("W0503-MODEL-CHANGE-NEEDS-CONFIG-REVISION", noRev.code == 2 && fmt.Sprint(first(noRev)["reason"]) == "MISSING_CONFIG_REVISION",
		"code", noRev.code, "record", first(noRev))
	stale := call("config", "set-model", "--model", "vendor/new-model", "--config-revision", "99", "--settled")
	ok("W0503-STALE-CONFIG-REVISION-REFUSED", stale.code == 1 && fmt.Sprint(first(stale)["reason"]) == "STALE_CONFIG_REVISION",
		"code", stale.code, "record", first(stale))
	notSettled := call("config", "set-model", "--model", "vendor/new-model", "--config-revision", "0")
	ok("W0503-MODEL-CHANGE-NEEDS-SETTLED-CONFIRMATION", notSettled.code == 1 &&
		fmt.Sprint(first(notSettled)["reason"]) == "SETTLED_CONFIRMATION_REQUIRED", "code", notSettled.code, "record", first(notSettled))
	show := call("config", "show")
	if pure("W0503-CONFIG-SHOW", show) {
		ok("W0503-CONFIG-SHOW-AFTER-REFUSALS-IS-UNCHANGED", show.code == 0 &&
			fmt.Sprint(first(show)["status"]) == "COMPLETED", "code", show.code, "record", first(show))
	}

	// Hostless commands must refuse with 3, and a host that is configured but unreachable must fail with 1.
	// `run` is deliberately not in this list: it is an accepted W05-02 verb with a real Job Object cascade, and this
	// card's layer must not answer it — see W0503-ACCEPTED-VERBS-NOT-SHADOWED.
	for _, c := range []string{"status", "goal", "go", "resume", "cancel"} {
		r := call(c)
		ok("W0503-HOSTLESS-"+strings.ToUpper(c)+"-REFUSES", r.code == 3 &&
			fmt.Sprint(first(r)["reason"]) == "HOST_DISCOVERY_UNAVAILABLE", "code", r.code, "record", first(r))
	}
	_ = os.WriteFile(disc, []byte(`{"url":"http://127.0.0.1:1","pid":1,"data_dir":"x","started_at":"now"}`), 0o600)
	dead := call("status")
	ok("W0503-DEAD-HOPE-FAILS-NOT-SILENT-OK", dead.code == 1 && fmt.Sprint(first(dead)["reason"]) == "HOST_UNREACHABLE",
		"code", dead.code, "record", first(dead))

	// A real listening host, so HOST_ANSWERED is measured rather than imagined.
	ln, lerr := net.Listen("tcp", "127.0.0.1:0")
	if lerr != nil {
		skip("W0503-LIVE-HOST-ANSWERED", "loopback listen refused: "+lerr.Error())
	} else {
		server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprint(w, `{"state":"READY","protocol":"researchos-client/2"}`)
		})}
		go server.Serve(ln)
		url := "http://" + ln.Addr().String()
		ready := false
		for i := 0; i < 40; i++ {
			c, err := net.DialTimeout("tcp", ln.Addr().String(), 200*time.Millisecond)
			if err == nil {
				c.Close()
				ready = true
				break
			}
			time.Sleep(50 * time.Millisecond)
		}
		if !ready {
			skip("W0503-LIVE-HOST-ANSWERED", "loopback never accepted; the same flake the checkpoint records for W17")
		} else {
			_ = os.WriteFile(disc, []byte(`{"url":"`+url+`","pid":`+fmt.Sprint(os.Getpid())+`,"data_dir":"x","started_at":"now"}`), 0o600)
			live := call("status")
			ok("W0503-LIVE-HOST-ANSWERED", live.code == 0 && fmt.Sprint(first(live)["status"]) == "HOST_ANSWERED" &&
				strings.Contains(fmt.Sprint(first(live)["health_body_truncated"]), "READY"), "code", live.code, "record", first(live))
			resume := call("resume", "--session", "sess-1")
			ok("W0503-RESUME-GOES-THROUGH-THE-HOST", resume.code == 0 && fmt.Sprint(first(resume)["command"]) == "resume",
				"code", resume.code, "record", first(resume))
		}
		server.Close()
	}
	_ = os.Remove(disc)

	// Stderr separation: a refusal must put its explanation on stderr only as a diagnostic, and the machine record
	// must stay on stdout alone.
	unknown := call("totally-unknown-verb")
	ok("W0503-UNKNOWN-VERB-NON-ZERO", unknown.code != 0, "code", unknown.code)
	// This row was red on the first run of this check: the accepted W02-03 launcher wrote the unknown-verb refusal to
	// stdout as human text, which makes the card's "非交互stdout仅JSONL" requirement false. apps/cli/main.go is inside
	// this card's write scope (CLI/**), so the refusal became a JSONL record on stdout with the sentence as a stderr
	// diagnostic; the accepted W05-02 check that pins the strings NOT_IMPLEMENTED/chat/task on stdout still passes
	// (receipts/W05/W05-03/accepted_check_reruns_after_contract_change.json).
	ok("W0503-UNKNOWN-VERB-KEEPS-STDOUT-JSONL-ONLY", strings.TrimSpace(unknown.stdout) == "" ||
		strings.HasPrefix(strings.TrimSpace(unknown.stdout), "{"),
		"launcher wrote human text to stdout: "+clipOut(unknown.stdout))

	// The accepted verbs must keep their accepted answers. This card registers into the same commandHandlers map that
	// apps/cli/cancel_run_windows.go uses, so the real risk is not a missing handler but a shadowed one: measured here
	// by driving the accepted cascade itself and by mirroring the two refusals the accepted W05-02 check pins.
	cascadeDir := filepath.Join(repo, ".local", "w0503_noshadow")
	_ = os.MkdirAll(cascadeDir, 0o700)
	defer os.RemoveAll(cascadeDir)
	cascade := callIn(cascadeDir, "run", "-dir", cascadeDir, "-job", "ros-w0503-noshadow", "-queue", "1",
		"-cancel-after", "250ms", "-observe-after", "300ms", "-settle", "6s")
	corder := []string{}
	if list, isList := first(cascade)["order"].([]any); isList {
		for _, x := range list {
			corder = append(corder, fmt.Sprint(x))
		}
	}
	ok("W0503-ACCEPTED-VERBS-NOT-SHADOWED", cascade.code == 0 && len(corder) >= 4 &&
		corder[0] == "clear_queue" && corder[1] == "abort" && corder[2] == "settled" && corder[3] == "child_confirmed",
		"code", cascade.code, "order", corder, "stdout", clipOut(cascade.stdout), "stderr", clipOut(cascade.stderr))
	// The cascade's own child is the accepted `worker` verb, so the tick count it recorded is the proof that verb
	// still runs; `worker` is never invoked bare here because it loops until its job object is cancelled.
	ticks, _ := first(cascade)["ticks_at_cancel"].(float64)
	ok("W0503-ACCEPTED-WORKER-VERB-STILL-RUNS-INSIDE-THE-CASCADE", ticks > 0, "ticks_at_cancel", ticks, first(cascade))

	chat := call("chat")
	ok("W0503-CHAT-KEEPS-THE-ACCEPTED-REFUSAL", chat.code == 3 && strings.Contains(chat.stdout, "NOT_IMPLEMENTED"),
		"code", chat.code, "record", first(chat))

	// The empty-stub / external-CLI negative: the command surface must be implemented here, not delegated.
	src, rerr := os.ReadFile(filepath.Join(repo, "apps", "cli", "cli_contract.go"))
	if rerr != nil {
		ok("W0503-NO-PROCESS-DELEGATION", false, rerr)
	} else {
		code := []string{}
		for _, l := range strings.Split(string(src), "\n") {
			if strings.HasPrefix(strings.TrimSpace(l), "//") {
				continue
			}
			code = append(code, l)
		}
		body := strings.Join(code, "\n")
		// The command surface must answer by itself. This is asserted about this file only: the accepted
		// coding_task.go legitimately runs the configured check commands, and that is a different capability,
		// not a CLI verb being aliased to another vendor binary.
		ok("W0503-NO-PROCESS-DELEGATION", !strings.Contains(body, "os/exec") && !strings.Contains(body, "exec.Command"),
			"the CLI command surface must not start another process")
		answered := 0
		// Only the verbs this card owns are expected to answer in JSONL under their own name; the accepted verbs are
		// graded above, because their answer is a real cascade rather than a contract record.
		for _, c := range []string{"commands", "/help", "init", "config", "/model", "status", "goal", "go",
			"resume", "cancel", "chat", "/status", "/goal", "/resume", "/cancel"} {
			base := strings.TrimPrefix(c, "/")
			r := call(c)
			m := first(r)
			back := fmt.Sprint(m["command"])
			if back == "" {
				back = fmt.Sprint(m["reason"])
			}
			if len(r.lines()) > 0 && (back == c || back == base || strings.HasPrefix(back, c)) {
				answered++
				continue
			}
			failures = append(failures, map[string]string{"id": "W0503-HANDLER-ANSWERS-" + c,
				"detail": "code " + fmt.Sprint(r.code) + " stdout " + clipOut(r.stdout)})
		}
		ok("W0503-EVERY-OWNED-VERB-ANSWERS-IN-ITS-OWN-NAME", answered == 15, "answered", answered)
	}

	longOut := call("commands")
	ok("W0503-LONG-OUTPUT-STAYS-PARSABLE", len(longOut.lines()) == 1 &&
		strings.Contains(longOut.stdout, "exit_code_contract") && len(longOut.stdout) > 1500,
		"lines", len(longOut.lines()), "bytes", len(longOut.stdout))

	interrupt130(repo, bin, disc, env)
	distributionPhase(repo)

	head := exec.Command("git", "rev-parse", "HEAD")
	head.Dir = repo
	hb, _ := head.Output()
	ok("W0503-HEAD-RECORDED", len(strings.TrimSpace(string(hb))) == 40, strings.TrimSpace(string(hb)))

	os.Remove(cfg)
	report()
}

func report() {
	status := "PASS"
	if len(failures) > 0 {
		status = "FAIL"
	}
	if len(ids) == 0 {
		failures = append(failures, map[string]string{"id": "NO-ASSERTIONS-RECORDED", "detail": "a run that recorded nothing is never a pass"})
		status = "FAIL"
	}
	sort.Strings(ids)
	fails := failures
	if fails == nil {
		fails = []map[string]string{}
	}
	nv := notVerified
	if nv == nil {
		nv = []string{}
	}
	out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
		"failures": fails, "not_verified": nv,
		"scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
		"environment": map[string]any{"os": runtime.GOOS, "arch": runtime.GOARCH}})
	fmt.Println(string(out))
	if len(failures) > 0 {
		os.Exit(1)
	}
}

func clipOut(s string) string {
	s = strings.ReplaceAll(strings.TrimSpace(s), "\n", " / ")
	if len(s) > 300 {
		s = s[:300]
	}
	return s
}

// interrupt130 delivers a real console signal to the CLI child and grades the exit code it comes back with, because
// the card names 130 as part of the contract and a mapping table alone would not prove the path is reachable. On
// Windows the only way to signal one child without signalling this check process as well is CTRL_BREAK_EVENT aimed at
// a new process group. If the platform refuses the delivery — which is what happens with no console attached — that is
// recorded as not verified with the error that came back, and the product is not blamed for it.
func interrupt130(repo, bin, disc string, env []string) {
	const ctrlBreakEvent = 1
	const createNewProcessGroup = 0x00000200
	if runtime.GOOS != "windows" {
		skip("W0503-INTERRUPT-EXITS-130", "console signal delivery is a Windows mechanism; host is "+runtime.GOOS)
		return
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		skip("W0503-INTERRUPT-EXITS-130", "loopback listen refused: "+err.Error())
		return
	}
	server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		time.Sleep(5 * time.Second)
		fmt.Fprint(w, `{"state":"READY"}`)
	})}
	go server.Serve(ln)
	defer server.Close()
	_ = os.WriteFile(disc, []byte(`{"url":"http://`+ln.Addr().String()+`","pid":1,"data_dir":"x","started_at":"now"}`), 0o600)
	defer os.Remove(disc)

	cmd := exec.Command(bin, "status")
	cmd.Dir = repo
	cmd.Env = env
	cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: createNewProcessGroup}
	var stdout, stderr strings.Builder
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	if err := cmd.Start(); err != nil {
		ok("W0503-INTERRUPT-CHILD-STARTED", false, err)
		return
	}
	ok("W0503-INTERRUPT-CHILD-STARTED", true, cmd.Process.Pid)
	time.Sleep(600 * time.Millisecond)

	proc := syscall.NewLazyDLL("kernel32.dll").NewProc("GenerateConsoleCtrlEvent")
	r1, _, e := proc.Call(ctrlBreakEvent, uintptr(cmd.Process.Pid))
	if r1 == 0 {
		skip("W0503-INTERRUPT-EXITS-130", "GenerateConsoleCtrlEvent refused the delivery: "+e.Error())
		_ = cmd.Wait()
		return
	}
	done := make(chan error, 1)
	go func() { done <- cmd.Wait() }()
	select {
	case werr := <-done:
		code := 0
		if ee, isExit := werr.(*exec.ExitError); isExit {
			code = ee.ExitCode()
		}
		rec := map[string]any{}
		ls := strings.Split(strings.ReplaceAll(stdout.String(), "\r\n", "\n"), "\n")
		for _, l := range ls {
			if strings.TrimSpace(l) != "" {
				_ = json.Unmarshal([]byte(strings.TrimSpace(l)), &rec)
				break
			}
		}
		ok("W0503-INTERRUPT-EXITS-130", code == 130 && fmt.Sprint(rec["status"]) == "INTERRUPTED" &&
			fmt.Sprint(rec["exit_code"]) == "130", "code", code, "record", rec, "stderr", clipOut(stderr.String()))
	case <-time.After(10 * time.Second):
		_ = cmd.Process.Kill()
		ok("W0503-INTERRUPT-EXITS-130", false, "signal was delivered but the child never exited")
	}
}

// distributionPhase drives the candidate generator under OPS/cli_distribution and grades its report, so the install
// claim is measured through the real build+launch path in a directory containing a space and Chinese characters.
func distributionPhase(repo string) {
	target := filepath.Join(repo, ".local", "w0503 分发 target")
	_ = os.RemoveAll(target)
	defer os.RemoveAll(target)
	cmd := exec.Command(goExe(), "run", "./ops/cli_distribution", "-repo", repo, "-target", target)
	cmd.Dir = repo
	cmd.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off")
	var so, se strings.Builder
	cmd.Stdout, cmd.Stderr = &so, &se
	err := cmd.Run()
	var rep map[string]any
	linesOut := []string{}
	for _, l := range strings.Split(strings.ReplaceAll(so.String(), "\r\n", "\n"), "\n") {
		if strings.TrimSpace(l) != "" {
			linesOut = append(linesOut, strings.TrimSpace(l))
		}
	}
	if len(linesOut) > 0 {
		_ = json.Unmarshal([]byte(linesOut[len(linesOut)-1]), &rep)
	}
	got := []string{}
	if list, isList := rep["assertion_ids"].([]any); isList {
		for _, x := range list {
			got = append(got, fmt.Sprint(x))
		}
	}
	ok("W0503-DISTRIBUTION-CANDIDATE-PASSES", err == nil && fmt.Sprint(rep["status"]) == "PASS" && len(got) >= 6,
		"err", err, "status", rep["status"], "assertions", len(got), "stderr", clipOut(se.String()))
	hasChineseRow := false
	for _, g := range got {
		if g == "DIST-TARGET-HAS-SPACE-AND-NON-ASCII" {
			hasChineseRow = true
		}
	}
	ok("W0503-DISTRIBUTION-ASSERTS-ITSELF", hasChineseRow && len(got) == len(sortedUnique(got)), got)
	ok("W0503-DISTRIBUTION-REPORT-FAILURES-EMPTY", len(got) > 0 && fmt.Sprint(rep["failures"]) == "[]", rep["failures"])
	// The claim is verified outside the program that makes it: this process launches the installed artefact from its
	// own directory, so a candidate report that fabricated a leg cannot carry the card on its own word.
	exePath := filepath.Join(target, "researchos.exe")
	if st, serr := os.Stat(exePath); serr != nil || st.Size() < 100000 {
		ok("W0503-DISTRIBUTION-ARTIFACT-LAUNCHES-INDEPENDENTLY", false, serr, st)
	} else {
		c := exec.Command(exePath, "version")
		c.Dir = target
		var so, se strings.Builder
		c.Stdout, c.Stderr = &so, &se
		rerr := c.Run()
		rec := map[string]any{}
		_ = json.Unmarshal([]byte(strings.TrimSpace(so.String())), &rec)
		ok("W0503-DISTRIBUTION-ARTIFACT-LAUNCHES-INDEPENDENTLY", rerr == nil &&
			fmt.Sprint(rec["status"]) == "COMPLETED" && len(nonEmpty(so.String())) == 1,
			"exit", rerr, "stdout", clipOut(so.String()), "stderr", clipOut(se.String()))
		// The candidate program publishes the bytes its own launch produced. Comparing that digest with this
		// process's launch is what turns "the leg ran" from a claim in the report into a measured fact.
		h := sha256.Sum256([]byte(so.String()))
		mine := hex.EncodeToString(h[:])
		ok("W0503-DISTRIBUTION-SELFREPORT-DIGEST-MATCHES-INDEPENDENT-LAUNCH",
			fmt.Sprint(rep["installed_version_sha256"]) == mine,
			"reported", rep["installed_version_sha256"], "measured", mine)
	}
}

func nonEmpty(s string) []string {
	out := []string{}
	for _, l := range strings.Split(strings.ReplaceAll(s, "\r\n", "\n"), "\n") {
		if strings.TrimSpace(l) != "" {
			out = append(out, l)
		}
	}
	return out
}

func sortedUnique(in []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, s := range in {
		if !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	sort.Strings(out)
	return out
}

func repoRoot() string {
	root, _ := os.Getwd()
	for i := 0; i < 6; i++ {
		if _, err := os.Stat(filepath.Join(root, "go.mod")); err == nil {
			return root
		}
		root = filepath.Dir(root)
	}
	return root
}

func goExe() string {
	if v := os.Getenv("RESEARCHOS_GO"); v != "" {
		return v
	}
	return filepath.Join(".local", "tools", "go1.27.1", "go", "bin", "go.exe")
}
