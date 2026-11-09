package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"time"
)

func main() {
	child := flag.String("child", "", "task-owned child executable")
	pidFile := flag.String("pid-file", "", "task-owned child PID marker")
	cleanup := flag.String("cleanup", "", "task-owned cleanup marker")
	flag.Parse()
	if *child == "" || *pidFile == "" || *cleanup == "" {
		fmt.Fprintln(os.Stderr, "all fixture paths required")
		os.Exit(2)
	}
	cmd := exec.Command(*child, flag.Args()...)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	if err := cmd.Start(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	if err := os.WriteFile(*pidFile, []byte(strconv.Itoa(cmd.Process.Pid)), 0600); err != nil {
		_ = cmd.Process.Kill()
		_ = cmd.Wait()
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	finished := make(chan error, 1)
	go func() { finished <- cmd.Wait() }()
	tick := time.NewTicker(25 * time.Millisecond)
	defer tick.Stop()
	for {
		select {
		case err := <-finished:
			if err != nil {
				fmt.Fprintln(os.Stderr, "fixture child exited:", err)
			}
			return
		case <-tick.C:
			if _, err := os.Stat(*cleanup); err == nil {
				_ = cmd.Process.Kill()
				<-finished
				return
			}
		}
	}
}
