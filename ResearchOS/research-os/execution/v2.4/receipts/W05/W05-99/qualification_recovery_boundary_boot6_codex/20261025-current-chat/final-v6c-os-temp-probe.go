package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Printf("os.TempDir=%q\n", os.TempDir())
	for _, key := range []string{"TEMP", "TMP", "TMPDIR", "GOTMPDIR", "GOCACHE"} {
		fmt.Printf("%s=%q\n", key, os.Getenv(key))
	}
}
