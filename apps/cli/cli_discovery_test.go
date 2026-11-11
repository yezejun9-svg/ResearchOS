package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

type locatorFixture struct {
	Schema  string `json:"schema"`
	HostID  string `json:"host_id"`
	URL     string `json:"url"`
	Invalid []struct {
		Name   string `json:"name"`
		Target string `json:"target"`
		Field  string `json:"field"`
		Value  any    `json:"value"`
	} `json:"invalid"`
}

func sharedLocatorFixture(t *testing.T) locatorFixture {
	t.Helper()
	_, source, _, _ := runtime.Caller(0)
	raw, err := os.ReadFile(filepath.Join(filepath.Dir(source), "..", "..", "tests", "ui", "desktop", "fixtures", "shared-host-locator.json"))
	if err != nil {
		t.Fatal(err)
	}
	var f locatorFixture
	if err := json.Unmarshal(raw, &f); err != nil {
		t.Fatal(err)
	}
	return f
}

func locatorWriteJSON(t *testing.T, file string, value any) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, raw, 0600); err != nil {
		t.Fatal(err)
	}
}

func locatorEnvironment(t *testing.T) (string, string, string, map[string]any, map[string]any) {
	t.Helper()
	f := sharedLocatorFixture(t)
	root := t.TempDir()
	cwd, _ := os.Getwd()
	project := filepath.Join(root, "普通 项目")
	data := filepath.Join(root, "Desktop 数据")
	for _, dir := range []string{project, data} {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Chdir(project); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := os.Chdir(cwd); err != nil {
			t.Error(err)
		}
	})
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", "")
	t.Setenv("RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED", "")
	t.Setenv("RESEARCHOS_CLI_CREDENTIAL", "")
	t.Setenv("LOCALAPPDATA", filepath.Join(root, "AppData"))
	discoveryFile := filepath.Join(root, "desktop-discovery.json")
	locatorFile := filepath.Join(root, "AppData", "ResearchOS", "host-locator-v1.json")
	d := map[string]any{"url": f.URL, "pid": 123, "data_dir": data, "host_instance_id": f.HostID}
	l := map[string]any{"schema": f.Schema, "discovery_file": discoveryFile, "data_root": data, "host_instance_id": f.HostID}
	locatorWriteJSON(t, discoveryFile, d)
	locatorWriteJSON(t, locatorFile, l)
	return root, discoveryFile, locatorFile, d, l
}

func TestSharedHostLocatorCrossCWDAndNativeIdentity(t *testing.T) {
	_, file, _, _, _ := locatorEnvironment(t)
	d, resolved, err := hostDiscovery()
	if err != nil || resolved != file {
		t.Fatalf("resolve: %q %v", resolved, err)
	}
	if id, err := cliHostInstanceID(d); err != nil || id != sharedLocatorFixture(t).HostID {
		t.Fatalf("identity: %q %v", id, err)
	}
	if _, err := cliSessionCredential(d); err == nil {
		t.Fatal("locator manufactured a credential")
	}
	changed := d
	changed.PID++
	if _, err := cliHostInstanceID(changed); err == nil {
		t.Fatal("changed caller identity accepted")
	}
}

func TestSharedHostLocatorPriorityAndNoSilentFallback(t *testing.T) {
	root, _, _, _, _ := locatorEnvironment(t)
	legacy := discoveryPath
	locatorWriteJSON(t, legacy, map[string]any{"url": "http://127.0.0.1:55001", "pid": 1})
	d, file, err := hostDiscovery()
	if err != nil || file != legacy || !strings.Contains(d.URL, "55001") {
		t.Fatalf("legacy precedence: %v %s", err, file)
	}
	explicit := filepath.Join(root, "explicit.json")
	locatorWriteJSON(t, explicit, map[string]any{"url": "http://127.0.0.1:55002", "pid": 2})
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", explicit)
	if _, file, err = hostDiscovery(); err != nil || file != explicit {
		t.Fatalf("explicit precedence: %v %s", err, file)
	}
	if err := os.WriteFile(explicit, []byte("{"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, file, err = hostDiscovery(); err == nil || file != explicit {
		t.Fatal("bad explicit fell back")
	}
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", "")
	if err := os.WriteFile(legacy, []byte("{"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, file, err = hostDiscovery(); err == nil || file != legacy {
		t.Fatal("bad legacy fell back")
	}
	if err := os.Remove(legacy); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(legacy, 0700); err != nil {
		t.Fatal(err)
	}
	if _, _, err = hostDiscovery(); err == nil {
		t.Fatal("legacy directory fell back")
	}
}

func TestSharedHostLocatorSharedNegativeVectors(t *testing.T) {
	f := sharedLocatorFixture(t)
	for _, vector := range f.Invalid {
		t.Run(vector.Name, func(t *testing.T) {
			_, discoveryFile, locatorFile, d, l := locatorEnvironment(t)
			if vector.Target == "discovery" {
				d[vector.Field] = vector.Value
			} else {
				l[vector.Field] = vector.Value
			}
			locatorWriteJSON(t, discoveryFile, d)
			locatorWriteJSON(t, locatorFile, l)
			if _, _, err := hostDiscovery(); err == nil {
				t.Fatal("tampered shared hint accepted")
			}
		})
	}
}

func TestSharedHostLocatorDisabledAndDoctorUsesResolver(t *testing.T) {
	_, file, locatorFile, d, _ := locatorEnvironment(t)
	t.Setenv("RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED", "1")
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("disabled locator consulted")
	}
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", file)
	if _, _, err := hostDiscovery(); err != nil {
		t.Fatal("disable blocked explicit discovery:", err)
	}
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", "")
	t.Setenv("RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED", "")
	d["url"] = "http://example.com:80"
	locatorWriteJSON(t, file, d)
	out, code := doctorReport()
	if code != 2 || out["reason"] != "INVALID_LOCAL_URL" || out["health"] != "NOT_CHECKED" {
		t.Fatalf("doctor did not use resolver: %v", out)
	}
	if err := os.WriteFile(locatorFile, []byte("{"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("broken locator accepted")
	}
}

func TestSharedHostLocatorRejectsDuplicateFieldsAndRootMismatch(t *testing.T) {
	root, file, locator, original, record := locatorEnvironment(t)
	raw, _ := json.Marshal(record)
	duplicate := append([]byte(`{"schema":"foreign/1",`), raw[1:]...)
	if err := os.WriteFile(locator, duplicate, 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("duplicate locator field accepted")
	}
	locatorWriteJSON(t, locator, record)
	if err := os.WriteFile(file, []byte(`{"url":"http://127.0.0.1:54321/","url":"http://example.com"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("duplicate discovery field accepted")
	}
	locatorWriteJSON(t, file, original)
	otherRoot := filepath.Join(root, "other-data-root")
	if err := os.Mkdir(otherRoot, 0700); err != nil {
		t.Fatal(err)
	}
	record["data_root"] = otherRoot
	locatorWriteJSON(t, locator, record)
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("different existing data root accepted")
	}
}

func TestSharedHostLocatorStableHostRestart(t *testing.T) {
	_, file, locator, d, _ := locatorEnvironment(t)
	before, err := os.ReadFile(locator)
	if err != nil {
		t.Fatal(err)
	}
	d["pid"] = 456
	d["url"] = "http://127.0.0.1:54322/"
	locatorWriteJSON(t, file, d)
	current, _, err := hostDiscovery()
	if err != nil || current.PID != 456 || current.URL != d["url"] {
		t.Fatalf("restart discovery: %v %v", current, err)
	}
	if _, err := cliHostInstanceID(current); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(locator)
	if err != nil || string(after) != string(before) {
		t.Fatal("locator bytes changed")
	}
}

func TestSharedHostLocatorExactFieldNamesMatchDesktop(t *testing.T) {
	_, file, _, d, _ := locatorEnvironment(t)
	d["URL"] = "http://example.com/"
	d["PID"] = 999
	locatorWriteJSON(t, file, d)
	if _, _, err := hostDiscovery(); err == nil {
		t.Fatal("case aliases accepted in closed shared protocol")
	}
}
