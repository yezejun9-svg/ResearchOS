// Fixture-only challenger. Native exit 10 means same-root acquisition refused.
package main

import (
    "fmt"
    "os"
    "researchos.local/research-os/adapters/runtime"
)

func main() {
    if len(os.Args) != 2 { os.Exit(2) }
    lease, err := runtime.AcquireDataRootLease(os.Args[1])
    if err != nil { fmt.Println("SAME_ROOT_REFUSED"); os.Exit(10) }
    if !lease.Held() { fmt.Println("NOT_HELD"); os.Exit(3) }
    if err := lease.Close(); err != nil { fmt.Fprintln(os.Stderr,err); os.Exit(4) }
    fmt.Println("ACQUIRED_AND_RELEASED")
}
