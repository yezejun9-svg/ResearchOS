package domain

import (
	"database/sql"
	"fmt"
	"strings"
	"unicode/utf8"
)

// muTurnSnapshot adds immutable broker history to BOTH acceptance snapshots.
// Worker counters and SDK placeholder costs are never independent evidence.
func (s *Service) muTurnSnapshot(tx *sql.Tx, project string, task, run, contract, observation Object) (Object, error) {
	needed := false
	for _, v := range Arr(contract, "checks") {
		check, _ := v.(map[string]any)
		needed = needed || check["command_key"] == "mu.turn-output-v1"
	}
	if !needed {
		return nil, nil
	}
	if task["task_type"] != "mu_turn" && task["task_type"] != "runtime_qualification" {
		return nil, Fail(422, "GATE_FAILED", "Mu verifier requires a finite Mu turn or runtime qualification")
	}
	dispatch, err := nativeDispatchProof(tx, project, run, observation)
	if err != nil {
		return nil, err
	}
	admission, err := s.currentDispatchAdmission(tx, project, task, run, dispatch, "accept")
	if err != nil {
		return nil, err
	}
	profile, _ := admission["profile"].(map[string]any)
	if profile["backend"] != runtimeMuBackend {
		return nil, Fail(422, "GATE_FAILED", "Mu native dispatch profile required")
	}
	if err = validateRuntimeModelConfig(profile); err != nil {
		return nil, err
	}
	bundle, err := load(tx, project, "ContextBundle", Str(run, "context_bundle_id"))
	if err != nil {
		return nil, err
	}
	goal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, err
	}
	request := Object{"run_id": run["id"], "task_id": task["id"], "task_type": task["task_type"], "task_title": task["title"], "task_description": goal["original_intent"], "epoch": run["lease_epoch"], "context": bundle, "input_refs": run["input_refs"], "checkpoint_artifact_id": run["checkpoint_artifact_id"], "artifact_inputs": Empty()}
	attachments := Empty()
	for _, v := range Arr(run, "input_refs") {
		ref, _ := v.(map[string]any)
		if ref["entity_type"] != "Artifact" {
			continue
		}
		a, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		var raw []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); err != nil {
			return nil, err
		}
		if Digest(raw) != a["content_hash"] || !utf8.Valid(raw) {
			return nil, Fail(422, "GATE_FAILED", "Mu input artifact seal or UTF-8 mismatch")
		}
		request["artifact_inputs"] = append(Arr(request, "artifact_inputs"), Object{"id": a["id"], "content_hash": a["content_hash"], "media_type": a["media_type"], "path": "artifacts/" + Str(a, "id")})
		attachments = append(attachments, Object{"id": a["id"], "content_hash": a["content_hash"], "media_type": a["media_type"], "text": string(raw)})
	}
	prompt := Merge(request, Object{"attachments": attachments})
	history, ledger := Empty(), Empty()
	rows, err := tx.Query("SELECT rowid,body FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence", project, run["id"])
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var raw string
		var position int64
		if err = rows.Scan(&position, &raw); err != nil {
			rows.Close()
			return nil, err
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		// Local append order is read from SQLite, never accepted from a worker.
		// It proves MODEL -> TOOL -> MODEL ordering without trusting wall time.
		o["_journal_position"] = position
		history = append(history, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	rows, err = tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? ORDER BY id", project, run["id"])
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		ledger = append(ledger, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	return Object{"dispatch": dispatch, "profile": profile, "request": request, "prompt": prompt, "effects": history, "ledger": ledger}, nil
}

type muAssistant struct {
	Text, Thinking, Stop string
	Calls                []Object
}

// Parse the broker's bounded original SSE, independently of the SDK artifact.
func muResponse(raw string) (muAssistant, error) {
	result := muAssistant{Calls: []Object{}}
	if !completeRuntimeModelSSE([]byte(raw)) {
		return result, fmt.Errorf("incomplete model SSE")
	}
	calls := map[int64]Object{}
	for _, event := range strings.Split(strings.ReplaceAll(raw, "\r\n", "\n"), "\n\n") {
		data := []string{}
		for _, line := range strings.Split(event, "\n") {
			if strings.HasPrefix(line, "data:") {
				data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
			}
		}
		payload := strings.Join(data, "\n")
		if payload == "" || payload == "[DONE]" {
			continue
		}
		chunk, err := Decode([]byte(payload))
		if err != nil || chunk["error"] != nil {
			return result, fmt.Errorf("model error or malformed SSE")
		}
		choices := Arr(chunk, "choices")
		if len(choices) == 0 {
			continue
		}
		if len(choices) != 1 {
			return result, fmt.Errorf("multiple model choices")
		}
		choice, ok := choices[0].(map[string]any)
		if !ok {
			return result, fmt.Errorf("malformed choice")
		}
		index, err := Num(choice, "index")
		if err != nil || index != 0 {
			return result, fmt.Errorf("unexpected model choice")
		}
		delta, _ := choice["delta"].(map[string]any)
		if result.Stop != "" && (len(delta) > 0 || choice["finish_reason"] != nil) {
			return result, fmt.Errorf("data after model finish")
		}
		if delta["role"] != nil && delta["role"] != "assistant" {
			return result, fmt.Errorf("invalid response role")
		}
		for _, key := range []string{"content", "reasoning_content", "reasoning", "reasoning_text"} {
			if delta[key] != nil {
				if _, ok := delta[key].(string); !ok {
					return result, fmt.Errorf("nontext model delta")
				}
			}
		}
		result.Text += Str(delta, "content")
		for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
			result.Thinking += Str(delta, key)
		}
		if delta["refusal"] != nil || delta["function_call"] != nil {
			return result, fmt.Errorf("unsupported refusal or legacy call")
		}
		for _, v := range Arr(delta, "tool_calls") {
			part, ok := v.(map[string]any)
			if !ok {
				return result, fmt.Errorf("malformed tool delta")
			}
			n, err := Num(part, "index")
			if err != nil || n < 0 || n > 31 {
				return result, fmt.Errorf("invalid tool index")
			}
			call := calls[n]
			if call == nil {
				call = Object{"id": "", "name": "", "arguments": ""}
				calls[n] = call
			}
			if part["type"] != nil && part["type"] != "function" {
				return result, fmt.Errorf("unsupported tool type")
			}
			if id := Str(part, "id"); id != "" {
				if Str(call, "id") != "" && call["id"] != id {
					return result, fmt.Errorf("tool ID changed")
				}
				call["id"] = id
			}
			fn, _ := part["function"].(map[string]any)
			call["name"] = Str(call, "name") + Str(fn, "name")
			call["arguments"] = Str(call, "arguments") + Str(fn, "arguments")
		}
		if stop := Str(choice, "finish_reason"); stop != "" {
			result.Stop = stop
		}
	}
	if result.Stop != "stop" && result.Stop != "tool_calls" {
		return result, fmt.Errorf("model did not finish successfully")
	}
	for n := int64(0); n < int64(len(calls)); n++ {
		call := calls[n]
		if call == nil || Str(call, "id") == "" || Str(call, "name") == "" {
			return result, fmt.Errorf("incomplete tool call")
		}
		args, err := Decode([]byte(Str(call, "arguments")))
		if err != nil {
			return result, err
		}
		call["arguments"] = args
		result.Calls = append(result.Calls, call)
	}
	if (result.Stop == "tool_calls") != (len(result.Calls) > 0) {
		return result, fmt.Errorf("tool finish mismatch")
	}
	return result, nil
}

func muSDKAssistant(message Object) (muAssistant, error) {
	r := muAssistant{Calls: []Object{}, Stop: Str(message, "stopReason")}
	if r.Stop == "toolUse" {
		r.Stop = "tool_calls"
	}
	for _, v := range Arr(message, "content") {
		part, ok := v.(map[string]any)
		if !ok {
			return r, fmt.Errorf("malformed SDK content")
		}
		switch part["type"] {
		case "text":
			r.Text += Str(part, "text")
		case "thinking":
			r.Thinking += Str(part, "thinking")
		case "toolCall":
			r.Calls = append(r.Calls, Object{"id": part["id"], "name": part["name"], "arguments": part["arguments"]})
		default:
			return r, fmt.Errorf("unsupported SDK content")
		}
	}
	return r, nil
}

func muText(content any) (string, bool) {
	if s, ok := content.(string); ok {
		return s, true
	}
	parts, ok := content.([]any)
	if !ok {
		return "", false
	}
	text := ""
	for _, v := range parts {
		p, ok := v.(map[string]any)
		if !ok || p["type"] != "text" {
			return "", false
		}
		s, ok := p["text"].(string)
		if !ok {
			return "", false
		}
		text += s
	}
	return text, true
}

// Compare semantic request history without depending on SDK timestamps, usage
// placeholders or provider-specific optional serialization fields.
func muRequestHistory(messages []any, sdk bool) ([]any, error) {
	result := Empty()
	for _, v := range messages {
		m, ok := v.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("malformed message")
		}
		role := Str(m, "role")
		if role == "system" {
			continue
		}
		switch role {
		case "user":
			text, ok := muText(m["content"])
			if !ok {
				return nil, fmt.Errorf("nontext user input")
			}
			result = append(result, Object{"role": "user", "text": text})
		case "assistant":
			text := ""
			calls := []Object{}
			if sdk {
				a, err := muSDKAssistant(m)
				if err != nil {
					return nil, err
				}
				text = a.Text
				calls = a.Calls
			} else {
				if m["content"] != nil {
					var ok bool
					text, ok = muText(m["content"])
					if !ok {
						return nil, fmt.Errorf("nontext assistant")
					}
				}
				for _, v := range Arr(m, "tool_calls") {
					c, ok := v.(map[string]any)
					if !ok || c["type"] != "function" {
						return nil, fmt.Errorf("invalid wire tool call")
					}
					fn, _ := c["function"].(map[string]any)
					args, err := Decode([]byte(Str(fn, "arguments")))
					if err != nil {
						return nil, err
					}
					calls = append(calls, Object{"id": c["id"], "name": fn["name"], "arguments": args})
				}
			}
			result = append(result, Object{"role": "assistant", "text": text, "calls": calls})
		case "tool", "toolResult":
			text, ok := muText(m["content"])
			if !ok {
				return nil, fmt.Errorf("nontext tool result")
			}
			id := m["tool_call_id"]
			if sdk {
				id = m["toolCallId"]
				parts := []string{}
				for _, v := range Arr(m, "content") {
					p, _ := v.(map[string]any)
					parts = append(parts, Str(p, "text"))
				}
				text = strings.Join(parts, "\n")
				if text == "" {
					text = "(no tool output)"
				}
			}
			result = append(result, Object{"role": "tool", "id": id, "text": text})
		default:
			return nil, fmt.Errorf("unsupported role")
		}
	}
	return result, nil
}

// verifyMuTurn proves only execution of this finite turn, not correctness of
// business claims or repairs described by an assistant.
func verifyMuTurn(snapshot Object) (string, string) {
	fail := func(reason string) (string, string) { return "FAIL", reason }
	mu, _ := snapshot["mu_turn"].(map[string]any)
	if mu == nil {
		return fail("Mu native evidence snapshot missing.")
	}
	task, _ := snapshot["task"].(map[string]any)
	run, _ := snapshot["run"].(map[string]any)
	profile, _ := mu["profile"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	artifacts := Arr(snapshot, "artifacts")
	if len(artifacts) != 1 {
		return fail("One sealed SDK result required.")
	}
	entry, _ := artifacts[0].(map[string]any)
	raw, ok := entry["bytes"].([]byte)
	if !ok {
		return fail("SDK result bytes missing.")
	}
	result, err := Decode(raw)
	if err != nil || result["task_id"] != task["id"] || result["run_id"] != run["id"] || Hash(result["epoch"]) != Hash(run["lease_epoch"]) || result["model_ref"] != config["ref"] || result["model"] != config["model"] || result["actual_cost"] != nil || result["sdk_cost_is_placeholder"] != true {
		return fail("SDK result identity, model or cost binding mismatch.")
	}
	histories := map[string][]Object{}
	for _, v := range Arr(mu, "effects") {
		e, ok := v.(map[string]any)
		if !ok {
			return fail("Malformed effect history.")
		}
		histories[Str(e, "key")] = append(histories[Str(e, "key")], e)
	}
	models, tools := map[int64]Object{}, map[int64]Object{}
	for key, history := range histories {
		if len(history) < 3 || history[0]["state"] != "PREPARED" || history[1]["state"] != "STARTED" {
			return fail("Effect lacks prepared and started broker facts.")
		}
		e := history[len(history)-1]
		receipt, _ := e["receipt"].(map[string]any)
		request, _ := e["payload"].(map[string]any)
		if e["state"] != "CONFIRMED" || receipt["state"] != "CONFIRMED" || e["project_id"] != task["project_id"] || e["task_id"] != task["id"] || e["run_id"] != run["id"] || Hash(e["epoch"]) != Hash(run["lease_epoch"]) || e["context_bundle_id"] != run["context_bundle_id"] || receipt["run_id"] != run["id"] || receipt["key"] != key || Hash(receipt["epoch"]) != Hash(run["lease_epoch"]) {
			return fail("Every effect must be confirmed for this exact run and epoch.")
		}
		for i, h := range history {
			n, _ := Num(h, "sequence")
			if n != int64(i+1) || h["request_hash"] != e["request_hash"] || Hash(h["payload"]) != Hash(request) || h["reservation_id"] != e["reservation_id"] || h["epoch"] == nil || Hash(h["epoch"]) != Hash(e["epoch"]) {
				return fail("Effect history binding changed.")
			}
		}
		capability := Str(request, "capability")
		prefix := fmt.Sprintf("%s:%s:%v:%s:", task["id"], run["id"], run["lease_epoch"], strings.ToLower(capability))
		var ordinal int64
		if !strings.HasPrefix(key, prefix) {
			return fail("Effect logical key mismatch.")
		}
		if _, err = fmt.Sscan(strings.TrimPrefix(key, prefix), &ordinal); err != nil || ordinal < 1 || key != prefix+fmt.Sprint(ordinal) {
			return fail("Invalid effect ordinal.")
		}
		bound := false
		var routeBound any
		for _, v := range Arr(profile, "effect_routes") {
			route, _ := v.(map[string]any)
			if route["id"] == request["route"] && route["capability"] == capability && route["credential_revision"] == request["credential_revision"] {
				bound = true
				routeBound = route["upper_bound"]
			}
		}
		if !bound || request["route"] != config["route"] {
			return fail("Effect route differs from frozen profile.")
		}
		var reservation Object
		for _, v := range Arr(mu, "ledger") {
			l, _ := v.(map[string]any)
			if l["id"] == e["reservation_id"] {
				reservation = l
			}
			if capability == "MODEL" && receipt["actual_cost"] == nil && l["provider_request_id"] == key && (l["cost_basis"] == "ACTUAL" || l["operation"] == "RELEASE" || l["operation"] == "RECONCILE") {
				return fail("Unknown model money was settled or released.")
			}
		}
		if reservation == nil || reservation["run_id"] != run["id"] || reservation["provider_request_id"] != key || reservation["operation"] != "RESERVE" || reservation["cost_basis"] != "UPPER_BOUND" {
			return fail("Bounded durable effect reservation missing.")
		}
		cost := Object{"policy_id": reservation["policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": reservation["money"], "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": run["created_at"]}
		if Hash(reservation["money"]) != Hash(routeBound) || e["request_hash"] != Hash([]any{request, cost}) {
			return fail("Effect request or reserved bound differs from immutable admission.")
		}
		switch capability {
		case "MODEL":
			if receipt["model_transport"] != true || receipt["actual_cost"] != nil {
				return fail("Model transport must retain unknown monetary cost.")
			}
			models[ordinal] = e
		case "TOOL":
			if task["task_type"] == "runtime_qualification" {
				return fail("Qualification cannot execute tools.")
			}
			money, ok := receipt["actual_cost"].(map[string]any)
			amount, moneyErr := moneyAmount(money)
			if !ok || moneyErr != nil || amount.Sign() != 0 || Hash(receipt["actual_cost"]) != Hash(routeBound) {
				return fail("Host tool monetary receipt differs from its zero bound.")
			}
			tools[ordinal] = e
		default:
			return fail("Unrecognized effect capability.")
		}
	}
	max, _ := Num(config, "max_calls")
	if task["task_type"] == "runtime_qualification" {
		q, _ := profile["model_qualification"].(map[string]any)
		max, _ = Num(q, "max_calls")
	}
	if len(models) < 1 || int64(len(models)) > max {
		return fail("Model call count violates frozen bounds.")
	}
	mc, mcErr := Num(result, "model_calls")
	tc, tcErr := Num(result, "tool_calls")
	if mcErr != nil || tcErr != nil || mc != int64(len(models)) || tc != int64(len(tools)) {
		return fail("Worker counts differ from broker facts.")
	}
	messages := Arr(result, "messages")
	cursor := 0
	for cursor < len(messages) {
		m, _ := messages[cursor].(map[string]any)
		if m["role"] != "system" {
			break
		}
		cursor++
	}
	if cursor >= len(messages) {
		return fail("SDK user input missing.")
	}
	user, _ := messages[cursor].(map[string]any)
	text, valid := muText(user["content"])
	prompt, e := Decode([]byte(text))
	if !valid || e != nil || user["role"] != "user" || Hash(prompt) != Hash(mu["prompt"]) {
		return fail("SDK prompt differs from frozen task inputs.")
	}
	cursor++
	toolOrdinal := int64(0)
	usedIDs := map[string]bool{}
	lastPosition := int64(0)
	ordered := func(effect Object, after int64) (int64, bool) {
		history := histories[Str(effect, "key")]
		if len(history) == 0 {
			return 0, false
		}
		for _, fact := range history {
			pos, err := Num(fact, "_journal_position")
			if err != nil || pos <= after {
				return 0, false
			}
			after = pos
		}
		return after, true
	}
	for n := int64(1); n <= int64(len(models)); n++ {
		e := models[n]
		modelEnd, orderedModel := ordered(e, lastPosition)
		if e == nil || !orderedModel {
			return fail("Missing model call.")
		}
		lastPosition = modelEnd
		request, _ := e["payload"].(map[string]any)
		payload, _ := request["payload"].(map[string]any)
		body, err := validateRuntimeModelRequest(config, payload)
		if err != nil {
			return fail("Broker model request differs from frozen configuration.")
		}
		providerMessages := Arr(body, "messages")
		wireHistory, wireErr := muRequestHistory(providerMessages, false)
		sdkHistory, sdkErr := muRequestHistory(messages[:cursor], true)
		if wireErr != nil || sdkErr != nil || Hash(wireHistory) != Hash(sdkHistory) {
			return fail("Broker request history differs from preceding confirmed SDK messages.")
		}
		found := false
		for _, v := range providerMessages {
			m, _ := v.(map[string]any)
			if m["role"] == "user" {
				input, ok := muText(m["content"])
				p, err := Decode([]byte(input))
				if !ok || err != nil || Hash(p) != Hash(prompt) || found {
					return fail("Broker user input changed.")
				}
				found = true
			}
		}
		if !found {
			return fail("Broker request omitted task inputs.")
		}
		receipt, _ := e["receipt"].(map[string]any)
		response, _ := receipt["payload"].(map[string]any)
		status, _ := Num(response, "status")
		responseRaw := Str(response, "body")
		if status != 200 || response["content_type"] != "text/event-stream" || receipt["receipt_id"] != Digest([]byte(responseRaw)) {
			return fail("Broker model response seal mismatch.")
		}
		expected, err := muResponse(responseRaw)
		if err != nil {
			return fail("Broker model response: " + err.Error())
		}
		if cursor >= len(messages) {
			return fail("SDK omitted model response.")
		}
		message, _ := messages[cursor].(map[string]any)
		actual, err := muSDKAssistant(message)
		if err != nil || message["role"] != "assistant" || message["model"] != config["model"] || message["provider"] != config["provider"] || message["api"] != config["api"] || Hash(actual) != Hash(expected) {
			return fail("SDK assistant differs from broker response.")
		}
		if message["errorMessage"] != nil || (message["rawStopReason"] != nil && message["rawStopReason"] != expected.Stop) {
			return fail("SDK assistant reports an inconsistent stop or error.")
		}
		cursor++
		for _, call := range expected.Calls {
			declared := false
			for _, v := range Arr(config, "tools") {
				definition, _ := v.(map[string]any)
				fn, _ := definition["function"].(map[string]any)
				declared = declared || fn["name"] == call["name"]
			}
			if !declared {
				return fail("Provider called an undeclared tool.")
			}
			id := Str(call, "id")
			if usedIDs[id] {
				return fail("Duplicate provider tool call ID.")
			}
			usedIDs[id] = true
			toolOrdinal++
			effect := tools[toolOrdinal]
			toolEnd, orderedTool := ordered(effect, modelEnd)
			if effect == nil || !orderedTool {
				return fail("Provider tool call lacks a confirmed host effect.")
			}
			if toolEnd > lastPosition {
				lastPosition = toolEnd
			}
			req, _ := effect["payload"].(map[string]any)
			args, _ := req["payload"].(map[string]any)
			rec, _ := effect["receipt"].(map[string]any)
			output, _ := rec["payload"].(map[string]any)
			if args["name"] != call["name"] || Hash(args["arguments"]) != Hash(call["arguments"]) || rec["host_tool"] != call["name"] || rec["receipt_id"] != Digest(Bytes(output)) {
				return fail("Host tool request or result differs from provider call.")
			}
			if cursor >= len(messages) {
				return fail("SDK tool result missing.")
			}
			m, _ := messages[cursor].(map[string]any)
			if m["role"] != "toolResult" || m["toolCallId"] != id || m["toolName"] != call["name"] || m["isError"] != false || Hash(m["content"]) != Hash(output["content"]) || Hash(m["details"]) != Hash(output["details"]) {
				return fail("SDK tool result differs from confirmed host result.")
			}
			cursor++
		}
		if (n == int64(len(models))) != (expected.Stop == "stop") {
			return fail("Model call chain did not finish exactly once with stop.")
		}
	}
	if cursor != len(messages) || toolOrdinal != int64(len(tools)) {
		return fail("Unaccounted SDK messages or host effects.")
	}
	return "PASS", fmt.Sprintf("Verified finite Mu turn against native dispatch, sealed inputs/output and %d MODEL / %d TOOL broker receipts; model money remains unknown and reserved. No claim about semantic repair correctness.", len(models), len(tools))
}
