//go:build windows

// Independent fixture-only child. All supplied resources are newly created canaries.
//
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"strconv"
	"syscall"
	"time"
	"unsafe"
)

func code(e error) uint64 {
	var n syscall.Errno
	if errors.As(e, &n) {
		return uint64(n)
	}
	return 0
}
func main() {
	if len(os.Args) != 4 {
		os.Exit(90)
	}
	handle, e := strconv.ParseUint(os.Args[1], 10, 64)
	if e != nil {
		os.Exit(91)
	}
	var count uint32
	buffer := make([]byte, 4096)
	var flags uint32
	valid, _, handleErr := syscall.NewLazyDLL("kernel32.dll").NewProc("GetHandleInformation").Call(uintptr(handle), uintptr(unsafe.Pointer(&flags)))
	var readErr error
	if valid == 0 {
		readErr = handleErr
	} else {
		readErr = syscall.ReadFile(syscall.Handle(handle), buffer, &count, nil)
	}
	connection, networkErr := net.DialTimeout("tcp", os.Args[2], 2*time.Second)
	connected := connection != nil
	if connection != nil {
		connection.Close()
	}
	result := map[string]any{"pid": os.Getpid(), "handle_valid": valid != 0, "handle_read_attempted": valid != 0, "handle_read_code": code(readErr), "handle_read_error": fmt.Sprint(readErr), "handle_read_bytes": count, "handle_read_body": string(buffer[:count]), "network_connected": connected, "network_code": code(networkErr), "network_error": fmt.Sprint(networkErr), "inherited_researchos_go": os.Getenv("RESEARCHOS_GO"), "inherited_c22_evidence": os.Getenv("RESEARCHOS_C22_EVIDENCE")}
	raw, e := json.Marshal(result)
	if e != nil {
		os.Exit(92)
	}
	if e = os.WriteFile(os.Args[3], raw, 0600); e != nil {
		os.Exit(93)
	}
	fmt.Println(string(raw))
}
