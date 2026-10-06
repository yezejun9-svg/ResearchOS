package domain

import "testing"

func TestMonitorPlanCurrentAuthorityAndBounds(t *testing.T) {
	profile := Merge(Base("monitor-project"), Object{"intent": "当前项目范围", "source_configs": []any{Object{"source_id": "papers", "required": true, "enabled": false, "query": "current topic"}}})
	policy := Merge(Base("monitor-project"), Object{"monitor_period_seconds": 21600, "first_lookback_seconds": 604800})
	meta := Object{"requirement": Object{"status": "ACCEPTED", "basis": "USER_STATED", "text": "请持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。"}, "profile": profile, "run_policy": policy}
	valid := MonitorPlan{Schema: "MonitorPlan/v1", ProfileRef: Ref(profile, "ProjectProfile"), RunPolicyRef: Ref(policy, "RunPolicy"), ContextTarget: Str(profile, "intent"), Sources: []MonitorSource{{"papers", Hash(Arr(profile, "source_configs")[0])}}, PeriodSeconds: 21600, FirstLookbackSeconds: 604800, PagesPerSource: 2, ItemsPerPage: 25, MaxTasks: 16, WallTimeSeconds: 120, RequiredExperimentRefs: []Object{}, Exit: "OWNER_PAUSE_OR_CANCEL"}
	if err := verifyMonitorPlan(&valid, meta); err != nil {
		t.Fatal(err)
	}
	for _, test := range []struct {
		name string
		edit func(*MonitorPlan)
	}{
		{"expanded-period", func(p *MonitorPlan) { p.PeriodSeconds = 60 }},
		{"changed-topic", func(p *MonitorPlan) { p.ContextTarget = "model invented topic" }},
		{"missing-required-source", func(p *MonitorPlan) { p.Sources = []MonitorSource{} }},
		{"model-source-config", func(p *MonitorPlan) { p.Sources = []MonitorSource{{"papers", Hash("changed")}} }},
		{"unbounded-pages", func(p *MonitorPlan) { p.PagesPerSource = 999 }},
		{"unbounded-tasks", func(p *MonitorPlan) { p.MaxTasks = 999 }},
		{"invented-experiment", func(p *MonitorPlan) {
			p.RequiredExperimentRefs = []Object{{"entity_type": "Experiment", "id": "invented"}}
		}},
		{"changed-exit", func(p *MonitorPlan) { p.Exit = "UNTIL_IMPROVED" }},
	} {
		t.Run(test.name, func(t *testing.T) {
			plan := valid
			test.edit(&plan)
			if err := verifyMonitorPlan(&plan, meta); err == nil {
				t.Fatal("untrusted monitor expansion accepted")
			}
		})
	}
	for _, statement := range []string{"不要持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。", "请解释：请持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。", "请持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。但不要执行。"} {
		meta["requirement"].(map[string]any)["text"] = statement
		if err := verifyMonitorPlan(&valid, meta); err == nil {
			t.Fatalf("non-authorizing statement accepted: %s", statement)
		}
	}
}
