package installation

import "testing"

func TestSelectPlanRoutes(t *testing.T) {
	p := PayloadIdentity{"a", "commit", "protocol", 24}
	f := InstallFacts{Incoming:p, CanonicalRoots:true, SupportedSchema:true, SupportedProtocol:true}
	if got := SelectPlan(f).Route; got != RouteFresh { t.Fatal(got) }
	f.RetainedData = true
	if got := SelectPlan(f).Route; got != RouteUpgrade { t.Fatal(got) }
	f.RetainedData = false; f.ProgramExists = true; f.OwnedProgram = true; f.Installed = &p
	if got := SelectPlan(f).Route; got != RouteExact { t.Fatal(got) }
	changed := p; changed.ManifestSHA256 = "b"; f.Incoming = changed
	if got := SelectPlan(f).Route; got != RouteUpgrade { t.Fatal(got) }
	f.HistoricalVerifierRegistration = true
	if got := SelectPlan(f).Route; got != RouteRefuse { t.Fatal(got) }
	f.HistoricalVerifierRegistration = false; f.SupportedSchema = false
	if got := SelectPlan(f).Route; got != RouteRefuse { t.Fatal(got) }
	f.SupportedSchema = true; f.UnfinishedJournal = true
	if got := SelectPlan(f).Route; got != RouteRefuse { t.Fatal(got) }
}
