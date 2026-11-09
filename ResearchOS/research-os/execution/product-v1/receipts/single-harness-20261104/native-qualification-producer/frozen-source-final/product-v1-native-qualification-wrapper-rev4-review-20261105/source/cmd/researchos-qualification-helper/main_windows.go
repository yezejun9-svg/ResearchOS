//go:build windows

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"syscall"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/qualificationprobe"
)

func errorNumber(err error) int {
	var n syscall.Errno
	if errors.As(err, &n) {
		return int(n)
	}
	return -1
}
func emit(e qualificationprobe.Event) error {
	raw, err := json.Marshal(e)
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	n, err := os.Stdout.Write(raw)
	if err != nil {
		return err
	}
	if n != len(raw) {
		return io.ErrShortWrite
	}
	return nil
}
func fixedPath(root, name string) string { return filepath.Join(root, name) }
func readSource(path string) qualificationprobe.Event {
	e := qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "RESULT", Case: "source_read"}
	f, err := os.Open(path)
	if err != nil {
		e.Errno = errorNumber(err)
		return e
	}
	defer f.Close()
	e.Opened = true
	raw, err := io.ReadAll(io.LimitReader(f, 64<<10+1))
	if err != nil || len(raw) > 64<<10 {
		e.Errno = -1
		return e
	}
	sum := sha256.Sum256(raw)
	e.Digest = "sha256:" + hex.EncodeToString(sum[:])
	e.Bytes = len(raw)
	return e
}
func deniedRead(path string) qualificationprobe.Event {
	e := qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "RESULT", Case: "denied_read"}
	f, err := os.Open(path)
	if err != nil {
		e.Errno = errorNumber(err)
		return e
	}
	e.Opened = true
	f.Close()
	return e
}
func openWin(path string, create bool, name string) qualificationprobe.Event {
	e := qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "RESULT", Case: name}
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		e.Errno = -1
		return e
	}
	mode := uint32(windows.OPEN_EXISTING)
	if create {
		mode = windows.CREATE_NEW
	}
	h, err := windows.CreateFile(p, windows.GENERIC_WRITE, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, mode, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		e.Errno = errorNumber(err)
		return e
	}
	e.Opened = true
	windows.CloseHandle(h)
	return e
}
func connectLoopback(port uint16) qualificationprobe.Event {
	e := qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "RESULT", Case: "loopback_connect"}
	c, err := net.DialTimeout("tcp4", net.JoinHostPort("127.0.0.1", strconv.Itoa(int(port))), time.Second)
	if err != nil {
		e.Errno = errorNumber(err)
		return e
	}
	e.Opened = true
	c.Close()
	return e
}
func run(p qualificationprobe.Plan) error {
	paths := map[string]string{
		"source_read": fixedPath(p.Source, "allow.txt"), "denied_read": fixedPath(p.Denied, "denied.txt"),
		"source_write_open": fixedPath(p.Source, "write-existing.txt"), "working_write_open": fixedPath(p.Working, "write-existing.txt"),
		"source_create": fixedPath(p.Source, "create-denied.txt"), "working_create": fixedPath(p.Working, "create-denied.txt"),
	}
	for _, name := range qualificationprobe.Cases {
		if err := emit(qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "START", Case: name}); err != nil {
			return err
		}
		var result qualificationprobe.Event
		switch name {
		case "source_read":
			result = readSource(paths[name])
		case "denied_read":
			result = deniedRead(paths[name])
		case "source_write_open", "working_write_open":
			result = openWin(paths[name], false, name)
		case "source_create", "working_create":
			result = openWin(paths[name], true, name)
		case "loopback_connect":
			result = connectLoopback(p.Port)
		}
		if err := emit(result); err != nil {
			return err
		}
	}
	return emit(qualificationprobe.Event{Schema: qualificationprobe.EventSchema, Phase: "COMPLETE", Bitmap: qualificationprobe.CompleteBitmap})
}
func main() {
	if len(os.Args) != 3 || os.Args[1] != "--plan-v1" {
		os.Exit(64)
	}
	p, err := qualificationprobe.Decode(os.Args[2])
	if err != nil {
		os.Exit(64)
	}
	watchdog := time.AfterFunc(10*time.Second, func() { os.Exit(75) })
	defer watchdog.Stop()
	if run(p) != nil {
		os.Exit(74)
	}
}
