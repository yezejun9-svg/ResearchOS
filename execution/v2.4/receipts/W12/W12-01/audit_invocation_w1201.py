# Second half of the W12-01 self-audit: derive the counts from the frozen invocation
# reports themselves rather than from anything the generator typed by hand.
import collections, glob, json, os

def _root():
    d = os.path.abspath(os.path.dirname(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "execution", "v2.4", "commands.json")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("repository root not found from " + __file__)


REPO = _root()
RD = os.path.join(REPO, "execution", "v2.4", "receipts", "W12", "W12-01")
rc = json.load(open(os.path.join(RD, "receipt.json"), encoding="utf-8"))
bid = rc["check_results"]["binding_invocation"]
reports = []
for p in glob.glob(os.path.join(REPO, "execution", "invocations", bid, "**", "*.json"), recursive=True):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(d, dict) and "assertion_ids" in d:
        reports.append((p, d))
# the dispatcher receipt re-derives ids from the harness stdout; the harness report itself
# is stdout.txt, which is the only frozen artifact that carries not_verified.
for root, _, files in os.walk(os.path.join(REPO, "execution", "invocations", bid)):
    for fn in files:
        if fn == "stdout.txt":
            fp = os.path.join(root, fn)
            for line in open(fp, encoding="utf-8", errors="replace"):
                line = line.strip()
                if line.startswith("{") and '"assertion_ids"' in line:
                    reports.append((fp + ":" + fn, json.loads(line)))
print("report files found:", len(reports))
fails = []
for p, d in reports:
    ids = d["assertion_ids"]
    hist = collections.Counter(i.split("-")[0] + "-" + i.split("-")[1] for i in ids)
    want = rc["check_results"]["assertion_id_prefix_histogram"]
    print(os.path.basename(p), d.get("status"), "assertions:", len(ids),
          "reported:", d.get("assertions"), "not_verified:", len(d.get("not_verified", [])))
    if dict(hist) != want:
        diff = {k: (want.get(k), hist.get(k)) for k in set(hist) | set(want) if want.get(k) != hist.get(k)}
        fails.append(("histogram", p, diff))
    if len(ids) != rc["check_results"]["assertions"]:
        fails.append(("count", p, len(ids)))
    if d.get("failures"):
        fails.append(("failures", p, d["failures"]))
    nv = sorted(d.get("not_verified", []))
    rn = sorted(x.split(":")[0] for x in rc["check_results"]["not_verified"])
    nv_id = sorted(x.split(":")[0] for x in nv)
    if nv_id != rn:
        fails.append(("not_verified", p, (nv_id, rn)))
    if d.get("scope") != "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE":
        fails.append(("scope", p, d.get("scope")))
print("MISMATCHES:", json.dumps(fails, ensure_ascii=False)[:1500] if fails else "none")
