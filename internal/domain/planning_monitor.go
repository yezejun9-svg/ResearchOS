package domain

import (
	"fmt"
	"regexp"
)

// This bounded language authorizes reuse of the current project configuration,
// not a model-selected topic, provider, experiment or success threshold.
var monitorInstruction = regexp.MustCompile(`^请(?:持续|长期)监控当前项目(?:，|,)(?:按|沿用)现有配置定期生成研究报告(?:，(并运行已预注册实验))?(?:，|,)直到我暂停或取消[。！!]?$`)

type MonitorPlan struct {
	Schema                 string          `json:"schema"`
	ProfileRef             Object          `json:"profile_ref"`
	RunPolicyRef           Object          `json:"run_policy_ref"`
	ContextTarget          string          `json:"context_target"`
	Sources                []MonitorSource `json:"sources"`
	PeriodSeconds          int64           `json:"period_seconds"`
	FirstLookbackSeconds   int64           `json:"first_lookback_seconds"`
	PagesPerSource         int             `json:"pages_per_source"`
	ItemsPerPage           int             `json:"items_per_page"`
	MaxTasks               int             `json:"max_tasks"`
	WallTimeSeconds        int             `json:"wall_time_seconds"`
	RequiredExperimentRefs []Object        `json:"required_experiment_refs"`
	Exit                   string          `json:"exit"`
}

type MonitorSource struct {
	SourceID   string `json:"source_id"`
	ConfigHash string `json:"config_hash"`
}

func monitorAuthorization(meta Object) (authorized, experiments bool) {
	req, _ := meta["requirement"].(map[string]any)
	if req == nil || req["status"] != "ACCEPTED" || req["basis"] != "USER_STATED" {
		return false, false
	}
	m := monitorInstruction.FindStringSubmatch(Str(req, "text"))
	return m != nil, m != nil && m[1] != ""
}

func verifyMonitorPlan(plan *MonitorPlan, meta Object) error {
	authorized, experiments := monitorAuthorization(meta)
	if !authorized || plan == nil || plan.Schema != "MonitorPlan/v1" {
		return fmt.Errorf("current explicit Owner monitoring instruction and typed MonitorPlan/v1 required")
	}
	profile, _ := meta["profile"].(map[string]any)
	policy, _ := meta["run_policy"].(map[string]any)
	if profile == nil || policy == nil || Hash(plan.ProfileRef) != Hash(Ref(profile, "ProjectProfile")) || Hash(plan.RunPolicyRef) != Hash(Ref(policy, "RunPolicy")) || plan.ContextTarget != Str(profile, "intent") {
		return fmt.Errorf("monitor scope and policy must match the exact current project")
	}
	period, _ := Num(policy, "monitor_period_seconds")
	lookback, _ := Num(policy, "first_lookback_seconds")
	if plan.PeriodSeconds != period || period < 60 || plan.FirstLookbackSeconds != lookback || lookback < 1 || plan.Exit != "OWNER_PAUSE_OR_CANCEL" {
		return fmt.Errorf("monitor period, lookback and exit must preserve current authorization")
	}
	if plan.PagesPerSource < 1 || plan.PagesPerSource > 4 || plan.ItemsPerPage < 1 || plan.ItemsPerPage > 100 || plan.MaxTasks < 1 || plan.MaxTasks > 32 || plan.WallTimeSeconds < 1 || plan.WallTimeSeconds > 300 {
		return fmt.Errorf("monitor work must remain within finite page, item, task and wall-time bounds")
	}
	configs := Arr(profile, "source_configs")
	if plan.Sources == nil || len(plan.Sources) != len(configs) {
		return fmt.Errorf("monitor must preserve every configured source including required gaps")
	}
	seen := map[string]bool{}
	for _, source := range plan.Sources {
		if seen[source.SourceID] {
			return fmt.Errorf("duplicate monitor source")
		}
		seen[source.SourceID] = true
		matched := false
		for _, raw := range configs {
			config := raw.(map[string]any)
			matched = matched || source.SourceID == Str(config, "source_id") && source.ConfigHash == Hash(config)
		}
		if !matched {
			return fmt.Errorf("monitor cannot invent or modify source configuration")
		}
	}
	if plan.RequiredExperimentRefs == nil || !experiments && len(plan.RequiredExperimentRefs) != 0 {
		return fmt.Errorf("experiments require explicit Owner authorization")
	}
	seen = map[string]bool{}
	for _, ref := range plan.RequiredExperimentRefs {
		if ref["entity_type"] != "Experiment" || seen[Hash(ref)] {
			return fmt.Errorf("unique preregistered experiment references required")
		}
		seen[Hash(ref)] = true
		found := false
		for _, raw := range Arr(meta, "registered_experiments") {
			x := raw.(map[string]any)
			found = found || x["status"] == "REGISTERED" && Hash(Ref(x, "Experiment")) == Hash(ref)
		}
		if !found {
			return fmt.Errorf("monitor experiment is not a current preregistered input")
		}
	}
	if experiments && len(plan.RequiredExperimentRefs) == 0 {
		return fmt.Errorf("Owner requested experiments but no preregistered experiment is available")
	}
	return nil
}

func monitorNodeSupported(n PlanningNode, b *GoalBrief) bool {
	if n.ID != "monitor" || n.Action != "research_monitor" || n.Title == "" || n.Dependencies == nil || len(n.Dependencies) != 0 || n.Inputs == nil || len(n.Outputs) != 1 || n.Outputs[0] != "cycle-report.json" || len(n.Checks) != 1 || n.Checks[0].ID != "cycle-report" || n.Checks[0].Command != "research.cycle-report-v1" || n.Checks[0].Expected != "current required stage evidence and explicit gaps" || n.WallTime != b.Monitor.WallTimeSeconds || n.MaxAttempts < 1 || n.MaxAttempts > 2 {
		return false
	}
	allowed := map[string]bool{}
	for _, ref := range b.VersionVector {
		allowed[Hash(ref)] = true
	}
	for _, ref := range n.Inputs {
		if !allowed[Hash(ref)] {
			return false
		}
	}
	return true
}

func monitorPlanningPrompt(profile, policy Object) string {
	return "\nMonitoring catalog: only an explicit positive request to keep monitoring the current project with existing settings is supported: 请持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。 (长期/沿用 also supported; optionally ，并运行已预注册实验 before the final exit clause). Never turn a mention, negation, other topic or changed budget into authorization. For that exact bounded intent attach monitor {schema:MonitorPlan/v1,profile_ref,run_policy_ref,context_target:exact current project intent,sources:[{source_id,config_hash:sha256 canonical config}],period_seconds,first_lookback_seconds,pages_per_source:1..4,items_per_page:1..100,max_tasks:1..32,wall_time_seconds:1..300,required_experiment_refs:[],exit:OWNER_PAUSE_OR_CANCEL}. Copy ALL source configs including disabled/required sources and exact current policy values. Current profile=" + string(Bytes(profile)) + "; run_policy=" + string(Bytes(policy)) + ". Use exactly one node logical_id=monitor, action=research_monitor, depends_on=[], outputs=[cycle-report.json], checks=[{check_id:cycle-report,command_key:research.cycle-report-v1,expected:current required stage evidence and explicit gaps}], wall_time_seconds matching monitor, max_attempts<=2. Stage state is decided by the trusted cycle driver, not by this proposal. If experiments were requested and no approved preregistration is available, omit monitor and return NEEDS_INPUT with a blocking question. Source/runtime gaps become visible requests during bounded execution; no configuration is silently enabled. The monitor remains ACTIVE until an Owner lifecycle action; a completed cycle never completes long-term monitoring."
}
