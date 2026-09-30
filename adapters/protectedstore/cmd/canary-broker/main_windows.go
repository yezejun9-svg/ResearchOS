//go:build windows

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"researchos.local/research-os/adapters/protectedstore"
)

func main() {
	service := flag.Bool("service", false, "run installed synthetic service")
	probe := flag.Bool("probe", false, "read fixed synthetic service aggregate")
	configure := flag.Bool("configure-from-stdin", false, "elevated one-time project credential handoff; does not start calls")
	start := flag.Bool("start-frozen-run", false, "start the one frozen protected evaluation once")
	status := flag.Bool("status", false, "read state without partial metrics")
	aggregate := flag.Bool("aggregate", false, "read only a terminal frozen aggregate")
	reader := flag.String("reader-sid", "", "single local developer SID permitted to request aggregate")
	flag.Parse()
	count := 0
	for _, enabled := range []bool{*service, *probe, *configure, *start, *status, *aggregate} {
		if enabled {
			count++
		}
	}
	if flag.NArg() != 0 || count != 1 {
		fmt.Fprintln(os.Stderr, "exactly one fixed broker operation required")
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
	if *configure {
		raw, e := io.ReadAll(io.LimitReader(os.Stdin, 4097))
		if e != nil {
			os.Exit(1)
		}
		e = protectedstore.ConfigureServiceCredential(raw)
		for i := range raw {
			raw[i] = 0
		}
		if e != nil {
			fmt.Fprintln(os.Stderr, "CONFIGURATION_REFUSED")
			os.Exit(1)
		}
		json.NewEncoder(os.Stdout).Encode(map[string]bool{"configured": true, "started": false})
		return
	}
	var result protectedstore.SafeSummary
	var e error
	if *probe {
		result, e = protectedstore.ProbeCanaryService()
	} else {
		command := "status"
		if *start {
			command = "start-frozen-run"
		}
		if *aggregate {
			command = "aggregate"
		}
		result, e = protectedstore.QueryFrozenService(command)
	}
	if e != nil {
		fmt.Fprintln(os.Stderr, "CANARY_BROKER_UNAVAILABLE")
		os.Exit(1)
	}
	json.NewEncoder(os.Stdout).Encode(result)
}
