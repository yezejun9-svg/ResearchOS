//go:build windows

package domain

import (
 "context"
 "encoding/json"
 "flag"
 "os"
 "os/exec"
 "path/filepath"
 "testing"
)

var reviewStageInput = flag.String("review-stage-input", "", "isolated reviewer staging fixture input")
var reviewStageHash = flag.String("review-stage-input-hash", "", "reviewer fixture options hash")
var reviewStageOutput = flag.String("review-stage-output", "", "reviewer fixture child observation")

func TestIndependentMinimalEnvironmentStage(t *testing.T) {
 opt:=pauseMigrationStageTestOptions(t)
 opt.Upgrade.TargetRoot=pauseMigrationTestRelease(t)
 raw,e:=json.Marshal(opt);if e!=nil {t.Fatal(e)}
 input:=filepath.Join(t.TempDir(),"bound-options.json")
 if e=os.WriteFile(input,raw,0600);e!=nil {t.Fatal(e)}
 executable,e:=os.Executable();if e!=nil {t.Fatal(e)}
 output:=os.Getenv("REVIEW_STAGE_OBSERVATION")
 if output=="" {t.Fatal("explicit reviewer output required")}
 command:=exec.Command(executable,"-test.run=^TestIndependentMinimalEnvironmentStageChild$","-test.v","-review-stage-input="+input,"-review-stage-input-hash="+Digest(raw),"-review-stage-output="+output)
 command.Env=[]string{"SystemRoot="+os.Getenv("SystemRoot"),"WINDIR="+os.Getenv("WINDIR")}
 childOutput,e:=command.CombinedOutput()
 if writeErr:=os.WriteFile(output+".stdout.raw",childOutput,0600);writeErr!=nil {t.Fatal(writeErr)}
 t.Logf("NATIVE_LIKE_MINIMAL_ENV_FIXTURE child exit=%v output=%s",e,childOutput)
 if e!=nil {t.Fatal(e)}
}

func TestIndependentMinimalEnvironmentStageChild(t *testing.T) {
 if *reviewStageInput=="" {t.Skip("only parent subprocess invokes this helper")}
 for _,key:=range []string{"TEMP","TMP","TMPDIR","USERPROFILE","HOME","GOROOT","GOCACHE"} {if _,exists:=os.LookupEnv(key);exists {t.Fatal("unexpected inherited environment",key)}}
 raw,e:=os.ReadFile(*reviewStageInput);if e!=nil || Digest(raw)!=*reviewStageHash {t.Fatal("fixture binding hash",e)}
 var opt PauseSchemaUpgradeOptions;if e=json.Unmarshal(raw,&opt);e!=nil {t.Fatal(e)}
 _,sqls,e:=pauseMigrationRelease(opt.Upgrade.TargetRoot,25);if e!=nil {t.Fatal(e)}
 contracts,e:=LoadContracts(filepath.Join(opt.Upgrade.TargetRoot,"spec/v2.0/contracts"));if e!=nil {t.Fatal(e)}
 parent:=filepath.Dir(opt.Upgrade.Destination)
 runs:=[]Object{}
 for _,existing:=range []bool{false,true} {
  if existing {if e=os.Mkdir(opt.Upgrade.Destination,0700);e!=nil {t.Fatal(e)}}
  schemas,e:=pauseMigrationTemplate(context.Background(),opt,parent,sqls,contracts)
  if e!=nil || schemas.Source24=="" || schemas.Original25=="" || schemas.Restored24=="" || schemas.Restored25=="" {t.Fatal("full template failed",schemas,e)}
  stages,e:=filepath.Glob(filepath.Join(parent,".researchos-backup-stage-*"));if e!=nil || len(stages)!=0 {t.Fatal("explicit parent not cleaned",stages,e)}
  runs=append(runs,Object{"existing_destination":existing,"source24":schemas.Source24,"original25":schemas.Original25,"restored24":schemas.Restored24,"restored25":schemas.Restored25,"remaining_stages":len(stages)})
 }
 observation:=Object{"kind":"UNSIGNED_TEMPLATE_FIXTURE_NOT_NATIVE_AUTHORITY","pid":os.Getpid(),"environment_names":[]string{"SystemRoot","WINDIR"},"ambient_temp_reported_without_writing":os.TempDir(),"explicit_parent":parent,"options_hash":Digest(raw),"runs":runs}
 if e=os.WriteFile(*reviewStageOutput,Bytes(observation),0600);e!=nil {t.Fatal(e)}
}
