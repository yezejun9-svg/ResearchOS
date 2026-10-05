"""Finite driver/reuse adversarial checks; synthetic evidence is never a gate."""
import collections
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import bridge
import gate_driver as g

def parse_go(raw, expected, exit_code):
    return g.parse_go(raw, expected, exit_code, {name: "researchos.local/research-os/internal/domain" for name in expected})

class Routing(unittest.TestCase):
    def env(self, task="W03", check="W03-G01", case=""):
        return {"RESEARCHOS_TASK_ID": task, "RESEARCHOS_CHECK_ID": check, "RESEARCHOS_CASE_ID": case, "RESEARCHOS_GO": "locked-go.exe"}

    def test_exact_three_parents(self):
        for gate,key in g.KEYS.items():
            self.assertEqual(bridge.route(key,self.env(check=gate)),("parent",gate))

    def test_wrong_key_refused(self):
        for gate,key in g.KEYS.items():
            other="test.domain" if key=="contracts.validate" else "contracts.validate"
            with self.assertRaises(ValueError): bridge.route(other,self.env(check=gate))

    def test_parent_case_refused(self):
        for case in ("A03","C04","C19"):
            with self.assertRaises(ValueError): bridge.route("contracts.validate",self.env(case=case))

    def test_child_original_commands(self):
        for key,child,directory in (("contracts.validate","W03-02","contracts"),("test.domain","W03-01","domain")):
            self.assertEqual(bridge.route(key,self.env(check=child)),("forward",["locked-go.exe","run","./tests/"+directory+"/check"]))

    def test_legacy_tuples_forward(self):
        for key,file in (("contracts.validate","contracts"),("test.domain","domain")):
            for task,check,case in (("W04","W03-G01",""),("W06","W06-G01","A03"),("W13","",""),("","",""),("W03","","")):
                self.assertEqual(bridge.route(key,self.env(task,check,case)),("legacy",[sys.executable,"-X","utf8","ops/ci/"+file+".py"]))

    def test_child_exit_streams_env_inherited(self):
        with patch.object(sys,"argv",["bridge.py","test.domain"]),patch.dict(os.environ,self.env(check="W03-01"),clear=True),patch.object(bridge.subprocess,"call",return_value=37) as call:
            self.assertEqual(bridge.main(),37)
            call.assert_called_once_with(["locked-go.exe","run","./tests/domain/check"],cwd=bridge.ROOT)
            # Absence of capture, stdout, stderr and env is deliberate inheritance.

    def test_unknown_key_and_wrong_child_refused(self):
        for key,env in (("bad",self.env()),("test.domain",self.env(check="W03-02")),("contracts.validate",self.env(check="W03-01"))):
            with self.assertRaises(ValueError):bridge.route(key,env)

    def test_actual_unsupported_legacy_stdout_stderr_exit(self):
        for key,file in (("contracts.validate","contracts"),("test.domain","domain")):
            env=dict(os.environ);env.update(self.env(task="UNSUPPORTED",check="unknown"))
            old=subprocess.run([sys.executable,"-X","utf8","ops/ci/"+file+".py"],cwd=bridge.ROOT,env=bridge.legacy_environment(key,env),capture_output=True)
            forwarded=subprocess.run([sys.executable,"-B",str(Path(bridge.__file__)),key],cwd=bridge.ROOT,env=env,capture_output=True)
            self.assertEqual((forwarded.returncode,forwarded.stdout,forwarded.stderr),(old.returncode,old.stdout,old.stderr))

    def test_legacy_frozen_registry_environment(self):
        for key in ("contracts.validate","test.domain"):
            inherited=self.env(task="W06",check="W06-G01",case="A03")
            inherited.update(RESEARCHOS_EXECUTOR_ID="changed",GOPATH="new-child-only",GOCACHE="new-child-only")
            env=bridge.legacy_environment(key,inherited)
            entry=g.plan()["legacy_entries"][key]
            for name,value in entry["fixed_env"].items():self.assertEqual(env[name],value)
            self.assertNotIn("GOPATH",env);self.assertNotIn("GOCACHE",env)
            self.assertEqual(env["RESEARCHOS_CASE_ID"],"A03")
            with patch.object(sys,"argv",["bridge.py",key]),patch.dict(os.environ,inherited,clear=True),patch.object(bridge.subprocess,"call",return_value=23) as call:
                self.assertEqual(bridge.main(),23)
                call.assert_called_once_with([sys.executable,*entry["argv"]],cwd=bridge.ROOT,env=env)

class GoParsing(unittest.TestCase):
    def events(self):
        events=[{"Action":"run","Test":"TestSynthetic","Package":"researchos.local/research-os/internal/domain"},{"Action":"pass","Test":"TestSynthetic","Package":"researchos.local/research-os/internal/domain"}]
        events.extend({"Action":"pass","Package":"researchos.local/research-os/"+x[2:]} for x in g.PACKAGES)
        return events

    def raw(self,events):return "\n".join(json.dumps(x) for x in events)

    def test_valid_synthetic_parser_control(self):
        self.assertEqual(parse_go(self.raw(self.events()),["TestSynthetic"],0)["top_level_test_count"],1)

    def test_zero_missing_duplicate_fail_skip_exit(self):
        events=self.events()
        variants=[([],0),(events[1:],0),(events+[events[0]],0),(events+[events[1]],0),(events[:-1],0),(events+[{"Action":"fail","Test":"TestSynthetic/sub"}],0),(events+[{"Action":"skip","Test":"TestSynthetic/sub"}],0),(events,2)]
        for ev,code in variants:
            with self.subTest(events=ev,code=code),self.assertRaises(g.EvidenceError):parse_go(self.raw(ev),["TestSynthetic"],code)

    def test_extra_or_missing_expected(self):
        for expected in ([],["Other"],["TestSynthetic","Missing"],["TestSynthetic","TestSynthetic"]):
            with self.assertRaises(g.EvidenceError):parse_go(self.raw(self.events()),expected,0)

    def test_duplicate_json_key(self):
        with self.assertRaises(g.EvidenceError):g.loads('{"status":"FAIL","status":"PASS"}')

    def test_go_wrong_package_same_test_and_completions(self):
        ev=self.events()
        for event in ev[:2]:event["Package"]="researchos.local/research-os/apps/control"
        with self.assertRaises(g.EvidenceError):parse_go(self.raw(ev),["TestSynthetic"],0)

    def test_nonfinite_and_boolean_exit_rejected(self):
        raw=self.raw(self.events())
        for value in (False,True,0.0):
            with self.assertRaises(g.EvidenceError):parse_go(raw,["TestSynthetic"],value)
        for constant in ("NaN","Infinity","-Infinity","1e9999"):
            ev=self.events();text=self.raw(ev)+'\n'+('{"Action":"output","Value":'+constant+'}')
            with self.assertRaises(g.EvidenceError):parse_go(text,["TestSynthetic"],0)

class Reuse(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="w03-driver-test-",dir=g.HERE)
        self.root=Path(self.tmp.name)
        self.directory=self.root/"runs"/"synthetic"
        self.directory.mkdir(parents=True)
        self.manifest={"expected_ids":["TestSynthetic"],"mode":"FIXTURE","source_hashes":{"source.go":"frozen"},"test_packages":{"TestSynthetic":"researchos.local/research-os/internal/domain"},"packages":g.PACKAGES}
        events=GoParsing().events();raw=GoParsing().raw(events)
        (self.directory/"stdout.txt").write_text(raw,encoding="utf8")
        (self.directory/"stderr.txt").write_text("",encoding="utf8")
        self.receipt={"gate":"W03-G02","mode":"FIXTURE","kind":"go","status":"PASS","exit_code":0,"invocation":["locked-go","test"],"input_digest":g.digest(self.manifest),"stdout_sha256":g.sha(self.directory/"stdout.txt"),"stderr_sha256":g.sha(self.directory/"stderr.txt"),"started_at":"synthetic-start","ended_at":"synthetic-end","source_head":"synthetic-head","cwd":"synthetic-only","formal_product_acceptance":"NOT_RUN","owned_acceptance_ids":[],"parsed":parse_go(raw,["TestSynthetic"],0)}
        self.save()
        self.patches=[patch.object(g,"HERE",self.root),patch.object(g,"input_manifest",return_value=deepcopy(self.manifest)),patch.object(g,"invocation",return_value=["locked-go","test"])]
        for p in self.patches:p.start()

    def save(self):
        g.write(self.directory/"manifest.json",self.manifest);g.write(self.directory/"receipt.json",self.receipt)
        self.ref={"path":"runs/synthetic","receipt_sha256":g.sha(self.directory/"receipt.json"),"manifest_sha256":g.sha(self.directory/"manifest.json")}

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()

    def verify(self):return g.verify_atom(self.ref,"go","W03-G02",{})

    def test_current_synthetic_control(self):self.assertEqual(self.verify()["top_level_test_count"],1)

    def test_raw_tamper(self):
        (self.directory/"stdout.txt").write_text("{}",encoding="utf8")
        with self.assertRaises(g.EvidenceError):self.verify()

    def test_receipt_tamper(self):
        self.receipt["exit_code"]=2;g.write(self.directory/"receipt.json",self.receipt)
        with self.assertRaises(g.EvidenceError):self.verify()

    def test_manifest_tamper(self):
        self.manifest["mode"]="LIVE";g.write(self.directory/"manifest.json",self.manifest)
        with self.assertRaises(g.EvidenceError):self.verify()

    def test_stale_source(self):
        with patch.object(g,"input_manifest",return_value={**self.manifest,"source_hashes":{"source.go":"changed"}}),self.assertRaises(g.EvidenceError):self.verify()

    def test_mode_exit_missing_zero_mismatch_even_rehashed(self):
        baseline=deepcopy(self.receipt)
        for field,value in (("mode","LIVE"),("gate","W03-G03"),("exit_code",1),("exit_code",False),("status","FAIL"),("parsed",{}),("invocation",["different"]),("owned_acceptance_ids",["A03"]),("source_head","")):
            self.receipt=deepcopy(baseline);self.receipt[field]=value;self.save()
            with self.subTest(field=field),self.assertRaises(g.EvidenceError):self.verify()

    def test_forged_zero_raw_even_rehashed(self):
        (self.directory/"stdout.txt").write_text("",encoding="utf8")
        self.receipt["stdout_sha256"]=g.sha(self.directory/"stdout.txt");self.save()
        with self.assertRaises(g.EvidenceError):self.verify()

    def test_unsafe_reference(self):
        for path in ("../receipt","/tmp/receipt","other/synthetic"):
            self.ref["path"]=path
            with self.assertRaises(g.EvidenceError):self.verify()

class ProbeParsing(unittest.TestCase):
    def report(self):
        return {"status":"PASS","check_id":"W03-G03","formal_product_acceptance":"NOT_RUN","owned_acceptance_ids":[],"checks":[{"id":"scalar","group":"types","passed":True},{"id":"hash","group":"bindings","passed":True}]}

    def test_probe_good_synthetic_control(self):
        self.assertEqual(g.parse_probe(json.dumps(self.report()),["scalar","hash"],0,"W03-G03")["new_check_groups"],2)

    def test_probe_missing_duplicate_failure_wronggate(self):
        r=self.report();variants=[]
        for checks in ([],r["checks"][:1],r["checks"]+[r["checks"][0]],[{**r["checks"][0],"passed":False},r["checks"][1]]):variants.append({**r,"checks":checks})
        variants.append({**r,"check_id":"W03-G01"})
        for report in variants:
            with self.assertRaises(g.EvidenceError):g.parse_probe(json.dumps(report),["scalar","hash"],0,"W03-G03")

    def test_nonfinite_probe_and_boolean_exit(self):
        for value in (False,True,0.0):
            with self.assertRaises(g.EvidenceError):g.parse_probe(json.dumps(self.report()),["scalar","hash"],value,"W03-G03")
        for constant in ("NaN","Infinity","-Infinity","1e9999"):
            raw=json.dumps(self.report())[:-1]+',"extra":'+constant+'}'
            with self.assertRaises(g.EvidenceError):g.parse_probe(raw,["scalar","hash"],0,"W03-G03")

    def corpus_report(self):
        p=g.plan();checks=[]
        for i,name in enumerate(p["probe_ids"]["W03-G01"]):
            if name in p["fixture_metadata"]:
                meta=p["fixture_metadata"][name]
                checks.append({"id":name,"passed":True,"group":"fixtures","detail":{**meta,"actual_valid":meta["expected_valid"]}})
            else:
                group="fixture_metadata" if name in ("CORPUS-SHAPE","PROTOCOL-INVENTORY") else "projection" if i==0 else "aggregate"
                checks.append({"id":name,"passed":True,"group":group,"detail":{}})
        return {"status":"PASS","check_id":"W03-G01","formal_product_acceptance":"NOT_RUN","owned_acceptance_ids":[],"checks":checks},p

    def test_pinned_corpus_synthetic_control(self):
        report,p=self.corpus_report()
        self.assertEqual(g.parse_probe(json.dumps(report),p["probe_ids"]["W03-G01"],0,"W03-G01",p["fixture_metadata"])["fixture_decisions"],106)

    def test_fixture_actual_contradicts_passed(self):
        report,p=self.corpus_report();row=next(x for x in report["checks"] if x["group"]=="fixtures")
        row["detail"]["actual_valid"]=not row["detail"]["actual_valid"]
        with self.assertRaises(g.EvidenceError):g.parse_probe(json.dumps(report),p["probe_ids"]["W03-G01"],0,"W03-G01",p["fixture_metadata"])

    def test_fixture_expected_and_schema_swapped(self):
        report,p=self.corpus_report();rows=[x for x in report["checks"] if x["group"]=="fixtures"]
        positive=next(x for x in rows if x["detail"]["expected_valid"])
        negative=next(x for x in rows if not x["detail"]["expected_valid"])
        positive["detail"],negative["detail"]=negative["detail"],positive["detail"]
        with self.assertRaises(g.EvidenceError):g.parse_probe(json.dumps(report),p["probe_ids"]["W03-G01"],0,"W03-G01",p["fixture_metadata"])

    def test_fixture_schema_and_bool_types(self):
        baseline,p=self.corpus_report()
        for field,value in (("schema_definition","Unknown"),("expected_valid",1),("actual_valid",1)):
            report=deepcopy(baseline);row=next(x for x in report["checks"] if x["group"]=="fixtures");row["detail"][field]=value
            with self.assertRaises(g.EvidenceError):g.parse_probe(json.dumps(report),p["probe_ids"]["W03-G01"],0,"W03-G01",p["fixture_metadata"])

if __name__=="__main__":unittest.main(verbosity=2)
