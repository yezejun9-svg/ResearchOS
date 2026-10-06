//go:build windows

// cancel_run_windows.go is W05-02 step 4 at the CLI edge. Two verbs:
//
//	worker  - a child that really appends a tick to a file on a timer, so survival is measurable
//	          rather than asserted by a log line;
//	run     - starts that child inside the package's existing job object, admits queued work, waits
//	          for a timer or a real Ctrl+C, and then runs clear_queue -> abort -> settled ->
//	          child_confirmed through adapters/runtime, reporting each step.
//
// The order is not this file's invention: adapters/runtime.Child.Cancel refuses to run before the
// queue has been cleared, so a caller that skips a step gets an error instead of a confident report.

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	rosruntime "researchos.local/research-os/adapters/runtime"
)

func init() {
	commandHandlers["worker"] = runWorkerLoop
	commandHandlers["run"] = runCancelCascade
}

func runWorkerLoop(args []string) {
	fs := flag.NewFlagSet("worker", flag.ContinueOnError)
	path := fs.String("file", "", "file the worker appends ticks to")
	every := fs.Duration("every", 40*time.Millisecond, "tick interval")
	if e := fs.Parse(args); e != nil {
		os.Exit(2)
	}
	if *path == "" || *every <= 0 {
		fmt.Println("worker: INVALID_REQUEST (-file and a positive -every are required)")
		os.Exit(2)
	}
	f, e := os.OpenFile(*path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o600)
	if e != nil {
		fmt.Println("worker: OPEN_FAILED " + e.Error())
		os.Exit(1)
	}
	defer f.Close()
	for n := 1; ; n++ {
		if _, e = f.WriteString(fmt.Sprintf("tick %d pid %d\n", n, os.Getpid())); e != nil {
			fmt.Println("worker: WRITE_FAILED " + e.Error())
			os.Exit(1)
		}
		_ = f.Sync()
		time.Sleep(*every)
	}
}

type cancelEnvelope struct {
	rosruntime.CancelReport
	TicksAtCancel int    `json:"ticks_at_cancel"`
	TicksLater    int    `json:"ticks_after_settle"`
	WritesAfter   int    `json:"writes_after_cancel"`
	WorkerExe     string `json:"worker_exe"`
	TickFile      string `json:"tick_file"`
}

func runCancelCascade(args []string) {
	fs := flag.NewFlagSet("run", flag.ContinueOnError)
	job := fs.String("job", "ros-w0502-cancel", "job object name")
	dir := fs.String("dir", ".", "directory the worker writes in")
	tickName := fs.String("tick-file", "worker-ticks.log", "file the worker appends to")
	queue := fs.Int("queue", 3, "queued items admitted before the cancel")
	after := fs.Duration("cancel-after", 400*time.Millisecond, "start the cascade after this long; 0 waits for a signal")
	settle := fs.Duration("settle", 8*time.Second, "how long to wait for the job to become empty")
	gap := fs.Duration("observe-after", 600*time.Millisecond, "extra time watched for any post-cancel write")
	exe := fs.String("exe", "", "worker executable; defaults to this binary")
	if e := fs.Parse(args); e != nil {
		os.Exit(2)
	}
	if *settle <= 0 || *gap < 0 {
		fmt.Println("run: INVALID_REQUEST (-settle must be positive and -observe-after non-negative)")
		os.Exit(2)
	}
	bin := *exe
	if bin == "" {
		b, e := os.Executable()
		if e != nil {
			fmt.Println("run: EXE_LOOKUP_FAILED " + e.Error())
			os.Exit(1)
		}
		bin = b
	}
	tickFile := filepath.Join(*dir, *tickName)
	// stdin is the null device, and stdout and stderr are separate handles: the pinned launcher hands
	// the child an explicit inheritable-handle list, and passing one handle twice was enough to make
	// CreateProcess reject the launch with ERROR_INVALID_PARAMETER.
	in, e := os.Open(os.DevNull)
	if e != nil {
		fmt.Println("run: DEVNULL_OPEN_FAILED " + e.Error())
		os.Exit(1)
	}
	stdout, e := os.OpenFile(filepath.Join(*dir, "worker-stdout.log"), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o600)
	if e != nil {
		in.Close()
		fmt.Println("run: LOG_OPEN_FAILED " + e.Error())
		os.Exit(1)
	}
	stderr, e := os.OpenFile(filepath.Join(*dir, "worker-stderr.log"), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o600)
	if e != nil {
		in.Close()
		stdout.Close()
		fmt.Println("run: LOG_OPEN_FAILED " + e.Error())
		os.Exit(1)
	}
	child, e := rosruntime.StartChild(*job, rosruntime.Command{
		Executable: bin,
		Args:       []string{"worker", "-file", tickFile, "-every", "40ms"},
		Directory:  *dir,
	}, os.Environ(), stdout, stderr, in)
	if e != nil {
		in.Close()
		stdout.Close()
		stderr.Close()
		fmt.Println("run: " + e.Error())
		os.Exit(1)
	}
	defer child.Close()

	admitted, refused := 0, 0
	for i := 0; i < *queue; i++ {
		if e = child.Admit(fmt.Sprintf("item-%d", i)); e != nil {
			refused++
		} else {
			admitted++
		}
	}

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	if *after > 0 {
		select {
		case <-time.After(*after):
		case <-sig:
		}
	} else {
		<-sig
	}

	before := countLines(tickFile)
	dropped := child.ClearQueue()
	rep, cancelErr := child.Cancel(*settle)
	rep.Order = append(rep.Order, fmt.Sprintf("clear_queue_returned=%d", dropped))
	after1 := countLines(tickFile)
	if *gap > 0 {
		time.Sleep(*gap)
	}
	after2 := countLines(tickFile)

	env := cancelEnvelope{CancelReport: rep, TicksAtCancel: before, TicksLater: after2,
		WritesAfter: after1 - before, WorkerExe: bin, TickFile: tickFile}
	env.Order = append(env.Order, fmt.Sprintf("admitted=%d", admitted), fmt.Sprintf("refused=%d", refused))
	out, _ := json.Marshal(env)
	fmt.Println(string(out))
	if cancelErr != nil {
		fmt.Println("run: CANCEL_INCOMPLETE: " + cancelErr.Error())
		os.Exit(5)
	}
	os.Exit(0)
}

func countLines(p string) int {
	b, e := os.ReadFile(p)
	if e != nil {
		return 0
	}
	n := 0
	for _, c := range b {
		if c == '\n' {
			n++
		}
	}
	return n
}
