package main

import (
	"encoding/json"
	"fmt"
	"os"
	"researchos.local/research-os/adapters/evaluation"
)

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: native dataset.json program.json")
		os.Exit(2)
	}
	dataset, e := os.ReadFile(os.Args[1])
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(2)
	}
	program, e := os.ReadFile(os.Args[2])
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(2)
	}
	rows, e := evaluation.Execute(dataset, program)
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(2)
	}
	if e = json.NewEncoder(os.Stdout).Encode(rows); e != nil {
		os.Exit(2)
	}
}
