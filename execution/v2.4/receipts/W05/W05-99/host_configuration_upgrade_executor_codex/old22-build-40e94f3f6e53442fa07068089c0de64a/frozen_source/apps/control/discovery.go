package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

func writeHostDiscovery(path, address, dataRoot, instanceID string) error {
	raw, e := json.Marshal(map[string]any{"url": "http://" + address, "pid": os.Getpid(), "data_dir": dataRoot, "host_instance_id": instanceID})
	if e != nil {
		return e
	}
	if e = os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return e
	}
	f, e := os.CreateTemp(filepath.Dir(path), "discovery-*.tmp")
	if e != nil {
		return e
	}
	defer os.Remove(f.Name())
	if _, e = f.Write(raw); e == nil {
		e = f.Sync()
	}
	if closeErr := f.Close(); e == nil {
		e = closeErr
	}
	if e != nil {
		return e
	}
	return os.Rename(f.Name(), path)
}
