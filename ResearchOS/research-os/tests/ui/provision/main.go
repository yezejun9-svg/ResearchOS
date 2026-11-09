package main

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// This process is only used against the temporary W13 browser fixture database.
func main() {
	if len(os.Args) < 2 || os.Getenv("RESEARCHOS_TASK_ID") != "W13" || !strings.HasPrefix(filepath.Base(filepath.Dir(os.Getenv("RESEARCHOS_DATA_DIR"))), "researchos-w13-ui-") {
		log.Fatal("W13 project id required")
	}
	db, err := store.Open(filepath.Join(os.Getenv("RESEARCHOS_DATA_DIR"), "researchos.sqlite"))
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	service, err := domain.New(db, filepath.Join("spec", "v2.0", "contracts"), filepath.Join("migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		log.Fatal(err)
	}
	if len(os.Args) >= 3 {
		switch os.Args[2] {
		case "runtime":
			if len(os.Args) != 4 {
				log.Fatal("runtime id required")
			}
			err = service.RegisterOrchestrationFixture(context.Background(), os.Args[1], os.Args[3])
		case "artifact-metadata":
			var artifacts []domain.Object
			if err = json.NewDecoder(os.Stdin).Decode(&artifacts); err != nil {
				log.Fatal(err)
			}
			tx, beginErr := db.Begin()
			if beginErr != nil {
				log.Fatal(beginErr)
			}
			defer tx.Rollback()
			for _, artifact := range artifacts {
				if artifact["project_id"] != os.Args[1] || (artifact["validity"] != "STALE" && !(artifact["access_class"] == "VERIFIER_ONLY" && strings.HasPrefix(domain.Str(artifact, "storage_key"), "unbound-w13-"))) {
					log.Fatal("classification fixture only")
				}
				if err = service.Contracts.Validate("Artifact", artifact); err != nil {
					log.Fatal(err)
				}
				body := string(domain.Bytes(artifact))
				if _, err = tx.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,?,?,?) ON CONFLICT(project,kind,id) DO UPDATE SET revision=excluded.revision,body=excluded.body", os.Args[1], artifact["id"], artifact["revision"], body, artifact["content_hash"]); err != nil {
					log.Fatal(err)
				}
				if _, err = tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,?,?,?)", os.Args[1], artifact["id"], artifact["revision"], body, artifact["content_hash"]); err != nil {
					log.Fatal(err)
				}
			}
			err = tx.Commit()
		case "verifying":
			// C18 transient-state fixture only: real reported Tasks and Runs
			// remain intact; no acceptance or product authority is fabricated.
			var ids []string
			if err = json.NewDecoder(os.Stdin).Decode(&ids); err != nil {
				log.Fatal(err)
			}
			tx, beginErr := db.Begin()
			if beginErr != nil {
				log.Fatal(beginErr)
			}
			defer tx.Rollback()
			for _, id := range ids {
				var raw string
				if err = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND id=?", os.Args[1], id).Scan(&raw); err != nil {
					log.Fatal(err)
				}
				task, decodeErr := domain.Decode([]byte(raw))
				if decodeErr != nil {
					log.Fatal(decodeErr)
				}
				if task["status"] != "EXECUTION_REPORTED" {
					log.Fatal("only real reported task may enter transient fixture")
				}
				revision, revErr := domain.Num(task, "revision")
				if revErr != nil {
					log.Fatal(revErr)
				}
				task["status"] = "VERIFYING"
				task["revision"] = revision + 1
				task["updated_at"] = domain.Now()
				if err = service.Contracts.Validate("Task", task); err != nil {
					log.Fatal(err)
				}
				body := string(domain.Bytes(task))
				if _, err = tx.Exec("UPDATE domain_objects SET revision=?,body=? WHERE project=? AND kind='Task' AND id=?", revision+1, body, os.Args[1], id); err != nil {
					log.Fatal(err)
				}
				if _, err = tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body) VALUES(?,'Task',?,?,?)", os.Args[1], id, revision+1, body); err != nil {
					log.Fatal(err)
				}
			}
			err = tx.Commit()
		case "observe":
			raw, readErr := io.ReadAll(os.Stdin)
			if readErr != nil {
				log.Fatal(readErr)
			}
			observation, decodeErr := domain.Decode(raw)
			if decodeErr != nil {
				log.Fatal(decodeErr)
			}
			spec := observation["spec"].(map[string]any)
			epoch, numberErr := domain.Num(spec, "epoch")
			if numberErr != nil {
				log.Fatal(numberErr)
			}
			err = service.ObserveRuntime(context.Background(), os.Args[1], domain.Str(spec, "run_id"), epoch, observation)
		default:
			log.Fatal("unknown fixture operation")
		}
		if err != nil {
			log.Fatal(err)
		}
		os.Stdout.WriteString("{}\n")
		return
	}
	principal := domain.Principal{ID: domain.ID(), Roles: []string{"SOURCE_ADAPTER"}, Grants: []domain.Grant{{ProjectID: os.Args[1]}}}
	if err = service.ProvisionPrincipal(context.Background(), principal); err != nil {
		log.Fatal(err)
	}
	token, err := service.IssueCredential(context.Background(), principal.ID, 15*time.Minute)
	if err != nil {
		log.Fatal(err)
	}
	result := map[string]string{"principal_id": principal.ID, "token": token}
	for name, roles := range map[string][]string{"editor": {"PLANNER", "EXECUTOR"}, "verifier": {"VERIFIER"}, "scheduler": {"SCHEDULER"}} {
		actor := domain.Principal{ID: domain.ID(), Roles: roles, Grants: []domain.Grant{{ProjectID: os.Args[1]}}}
		if err = service.ProvisionPrincipal(context.Background(), actor); err != nil {
			log.Fatal(err)
		}
		credential, issueErr := service.IssueCredential(context.Background(), actor.ID, 15*time.Minute)
		if issueErr != nil {
			log.Fatal(issueErr)
		}
		result[name+"_id"] = actor.ID
		result[name+"_token"] = credential
	}
	if err = json.NewEncoder(os.Stdout).Encode(result); err != nil {
		log.Fatal(err)
	}
}
