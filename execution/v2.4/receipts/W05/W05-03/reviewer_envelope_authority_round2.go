// envcheck.go replays the CLI's captured envelopes through the accepted protocol
// authority (internal/domain.DecodeEnvelope) so the CLI's local precondition mirrors can
// be compared with the real core's answer. Reviewer scratch tool; not project source.
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"researchos.local/research-os/internal/domain"
)

func main() {
	raw, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Println("READ_ERR", err)
		os.Exit(2)
	}
	var cases []struct {
		Case     string            `json:"case"`
		Envelopes []json.RawMessage `json:"envelopes"`
	}
	if e := json.Unmarshal(raw, &cases); e != nil {
		fmt.Println("PARSE_ERR", e)
		os.Exit(2)
	}
	out := []map[string]any{}
	for _, c := range cases {
		for _, env := range c.Envelopes {
			var m map[string]any
			_ = json.Unmarshal(env, &m)
			decoded, e := domain.DecodeEnvelope(env)
			row := map[string]any{"case": c.Case, "method": fmt.Sprint(m["method"]), "ok": e == nil}
			if e != nil {
				row["refusal"] = e.Error()
			} else {
				row["refusal"] = ""
				row["decoded_method"] = *decoded.Method
			}
			out = append(out, row)
			fmt.Printf("%-28s %-18s ok=%-5v %s\n", c.Case, fmt.Sprint(m["method"]), e == nil,
				func() string { if e != nil { return e.Error() }; return "ACCEPTED BY THE CORE" }())
		}
	}
	f, _ := os.Create(os.Args[2])
	json.NewEncoder(f).Encode(out)
	f.Close()
}
