//go:build windows

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"researchos.local/research-os/adapters/protectedstore"
)

func main() {
	service := flag.Bool("service", false, "run installed synthetic service")
	probe := flag.Bool("probe", false, "read fixed synthetic service aggregate")
	reader := flag.String("reader-sid", "", "single local developer SID permitted to request aggregate")
	flag.Parse()
	if flag.NArg() != 0 || *service == *probe {
		fmt.Fprintln(os.Stderr, "exactly one --service or --probe required")
		os.Exit(2)
	}
	if *service {
		if protectedstore.RunCanaryService(*reader) != nil {
			os.Exit(1)
		}
		return
	}
	if *reader != "" {
		os.Exit(2)
	}
	result, e := protectedstore.ProbeCanaryService()
	if e != nil {
		fmt.Fprintln(os.Stderr, "CANARY_BROKER_UNAVAILABLE")
		os.Exit(1)
	}
	json.NewEncoder(os.Stdout).Encode(result)
}
