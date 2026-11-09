package ledgers

import (
	"testing"
	"time"
)

func TestObjectivePublicCorpus(t *testing.T) {
	cases := Cases()
	if len(cases) != 60 {
		t.Fatal(len(cases))
	}
	counts := map[string]int{}
	for _, c := range cases {
		if e := Validate(c.State, c.Expected, c.Critical); e != nil {
			t.Fatalf("%s: %v", c.ID, e)
		}
		counts[c.Scope.Language+":"+c.Expected]++
	}
	for _, key := range []string{"zh:ACCEPT", "zh:REJECT", "zh-en:ACCEPT", "zh-en:REJECT"} {
		if counts[key] != 15 {
			t.Fatalf("%s: %d", key, counts[key])
		}
	}
	s := Cases()[0].State
	end, _ := time.Parse(time.RFC3339, s.Rules.WindowEnd)
	s.Documents[0].ObservedAt = end.Format(time.RFC3339)
	s.Documents[0].Text = documentText(s.Documents[0])
	s.Citations[0].Quote = s.Documents[0].Text
	if label, e := Grade(s); e != nil || label != "ACCEPT" {
		t.Fatalf("inclusive timestamp boundary: %s %v", label, e)
	}
	s.Documents[0].ObservedAt = end.Add(time.Second).Format(time.RFC3339)
	if label, _ := Grade(s); label != "REJECT" {
		t.Fatal("date outside window accepted")
	}
	s = Cases()[0].State
	s.Citations[0].Quote = "invented quote"
	if label, _ := Grade(s); label != "REJECT" {
		t.Fatal("fabricated quote accepted")
	}
}
