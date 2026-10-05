// Deterministic child for the fixed skill-up CLI probe. This is not Qoder.
package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	if strings.Contains(strings.Join(os.Args[1:], " "), "--version") {
		fmt.Println("mock-qodercli 1")
		return
	}
	fmt.Println("null bug found")
}
