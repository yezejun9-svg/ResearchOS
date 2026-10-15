//go:build !windows

package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Fprintln(os.Stderr, "STOP_UNAVAILABLE: exact retained Windows handles required")
	os.Exit(3)
}
