from pathlib import Path
root=Path(__file__).resolve().parents[7]
source=(root/'internal/domain/runtime_model_windows_test.go').read_text(encoding='utf-8')
helper=source[source.index('func muBrokerFixtureProgram('):source.index('func TestRuntimeMuQualificationBroker(')]
helper=helper.replace('func muBrokerFixtureProgram(', 'func providerBrokerFixture(').replace('t.Skip("requires explicitly built immutable Mu bundle")','t.Fatal("requires explicitly built immutable Mu bundle")')
helper=helper.replace('"fixture-model"','"deepseek-v4.1-flash"').replace('modelFixtureConfig(server.URL + "/v1/chat/completions")','providerFixtureConfig(server.URL + "/zen/go/v1/chat/completions")')
helper=helper.replace('if r.Header.Get("Authorization")', 'if r.Header.Get("User-Agent") != "ResearchOS/2.4" || !strings.HasPrefix(r.Header.Get("x-opencode-session"), "ros-v1-") || r.URL.Path != "/zen/go/v1/chat/completions" { t.Error("provider original transport headers/path missing"); w.WriteHeader(400); return }; if r.Header.Get("Authorization")')
source=(root/'internal/domain/runtime_tool_integration_windows_test.go').read_text(encoding='utf-8')
cycle=source[source.index('func runtimeMuToolCycle('):source.index('func checkMuReceiptRecovery(')]
cycle=cycle.replace('func runtimeMuToolCycle(t *testing.T, refuse bool) {','func TestProviderBindingActualSameRunToolHistory(t *testing.T) {\n refuse := false')
cycle=cycle.replace('muBrokerFixtureProgram(', 'providerBrokerFixture(')
cycle=cycle.replace('"fixture-model"','"deepseek-v4.1-flash"')
cycle=cycle.replace('delta = Object{"role": "assistant", "tool_calls":', 'delta = Object{"role": "assistant", "reasoning": "  original thought\\n", "reasoning_text": "not selected", "tool_calls":')
cycle=cycle.replace('delta["content"] = "已读取工作区文件。"','delta["content"] = "已读取工作区文件。"\n delta["reasoning_content"] = "final thought"\n var prior Object; for _,v:=range Arr(body,"messages") { m,_:=v.(map[string]any); if m["role"]=="assistant" {prior=m} }; if prior["reasoning_content"]!="  original thought\\n" {t.Errorf("actual SDK omitted original thinking: %s",Bytes(prior))}')
cycle=cycle.replace('checkMuReceiptRecovery(t, c, r)','checkMuReceiptRecovery(t, c, r)\n sourceTx(t,f.db,func(tx *sql.Tx)error{ transports,e:=validateProviderInventory(tx,f.project,Str(r.run,"id"));if e!=nil{return e};if len(transports)!=2{t.Fatalf("original MODEL inventory=%d",len(transports))};return nil })')
header='''//go:build windows

package domain

import (
 "bytes"
 "context"
 "database/sql"
 "encoding/json"
 "fmt"
 "io"
 "net/http"
 "os"
 "os/exec"
 "path/filepath"
 "strings"
 "sync/atomic"
 "testing"
 "time"
)

'''
(root/'internal/domain/runtime_provider_binding_windows_test.go').write_text(header+helper+cycle,encoding='utf-8')
