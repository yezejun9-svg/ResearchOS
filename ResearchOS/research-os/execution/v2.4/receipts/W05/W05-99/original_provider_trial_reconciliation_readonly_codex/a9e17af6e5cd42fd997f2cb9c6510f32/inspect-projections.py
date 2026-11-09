import sys
sys.dont_write_bytecode=True
import json
import os
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent

def main():
    rows=json.loads((Q/"associated-public-records.json").read_text(encoding="utf-8"))
    life=json.loads((Q/"projection-root-coordinator-lifecycle-json.json").read_text(encoding="utf-8"))["projection"]
    flat=[]
    def walk(value,pointer):
        if isinstance(value,dict):
            if all(key in value for key in ("path","sha256","bytes")):
                return
            for key,child in value.items():
                if not re.search(r"guard|inventory|binary|compile|program.*pin",str(key),re.I):
                    walk(child,pointer+"/"+str(key))
        elif isinstance(value,list):
            for index,child in enumerate(value):
                walk(child,pointer+"/"+str(index))
        else:
            if not isinstance(value,str) or len(value)<1200:
                if isinstance(value,int) and abs(value)>2**53:
                    value=str(value)
                flat.append({"pointer":pointer,"value":value})
    walk(life,"")
    rootrefs=[]
    for item in rows["associated_public_refs"]:
        if "root-model-trial-v5" in item["parent_ref"]["path"] and re.search(r"trial-output|input.model|launch.refs|authority|lifecycle",item["resolved_public_path"]):
            rootrefs.append(item)
    print(json.dumps({"lifecycle_top_keys":sorted(life),"lifecycle_safe_flat":flat,
        "real_trial_associated_refs":rootrefs},ensure_ascii=False))

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
