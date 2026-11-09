// Fixture-only independent process holding the real DataRootLease until stdin newline.
package main

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"
    "researchos.local/research-os/adapters/runtime"
)

func main() {
    if len(os.Args) != 2 { fmt.Fprintln(os.Stderr,"usage: lease_holder <fixture-data-root>"); os.Exit(2) }
    lease, err := runtime.AcquireDataRootLease(os.Args[1])
    if err != nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }
    if err := json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"HELD","held":lease.Held(),"pid":os.Getpid()}); err != nil { os.Exit(1) }
    _, err = bufio.NewReader(os.Stdin).ReadString('\n')
    if err != nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }
    if err := lease.Close(); err != nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }
    fmt.Println(`{"status":"RELEASED"}`)
}
