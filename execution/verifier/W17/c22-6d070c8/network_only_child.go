//go:build windows

package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"syscall"
	"time"
)

func main() {
	if len(os.Args) != 3 {
		os.Exit(90)
	}
	connection, e := net.DialTimeout("tcp", os.Args[1], 2*time.Second)
	connected := connection != nil
	if connection != nil {
		connection.Close()
	}
	var errno syscall.Errno
	errors.As(e, &errno)
	result := map[string]any{"pid": os.Getpid(), "network_connected": connected, "network_code": uint64(errno), "network_error": fmt.Sprint(e), "inherited_researchos_go": os.Getenv("RESEARCHOS_GO"), "inherited_c22_evidence": os.Getenv("RESEARCHOS_C22_EVIDENCE")}
	raw, e := json.Marshal(result)
	if e != nil {
		os.Exit(91)
	}
	if e = os.WriteFile(os.Args[2], raw, 0600); e != nil {
		os.Exit(92)
	}
	fmt.Println(string(raw))
}
