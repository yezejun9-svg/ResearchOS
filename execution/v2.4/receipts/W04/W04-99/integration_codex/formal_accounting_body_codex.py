# Construction source for the public read-only aggregator. Concatenated after
# the frozen strict W04 compatibility profile; never imported from receipts.


def _catalog(reader, plan_path):
    plan_path = Path(plan_path).resolve(strict=True)
    documents = {}
    for name, digest in FROZEN_HASHES.items():
        path = plan_path.parent / name
        require(sha256(path) == digest, "FROZEN_BASELINE", name)
        documents[name] = reader.read(path)
    acceptance, tasks, plan = (documents[name] for name in FROZEN_HASHES)
    rows = sequence(acceptance.get("cases"), "formal catalog")
    cases = {text(row.get("id"), "case id"): row for row in rows}
    require(len(cases) == len(rows) == 42, "CATALOG_CASES", "42 unique formal cases required")
    task_rows = sequence(tasks.get("tasks"), "tasks")
    task_map = {text(row.get("task_id"), "task id"): row for row in task_rows}
    require(len(task_rows) == len(task_map) == 22, "CATALOG_TASKS", "22 unique tasks required")
    plan_rows = sequence(plan.get("steps"), "plan")
    planned = {text(row.get("id"), "step id"): row for row in plan_rows}
    require(len(planned) == len(plan_rows), "DUPLICATE_ID", "plan")
    parents = {row["parent_task"]: row for row in plan_rows if row.get("phase") == "PARENT_FINAL_GATE"}
    require(len(parents) == 22 and set(parents) == set(task_map), "CATALOG_PARENTS", "22 final owners required")
    final_owners = obj(tasks.get("acceptance_final_owners"), "final owners")
    require(set(final_owners) == set(cases), "CATALOG_OWNERS", "complete final owner map")
    owned = {}
    for task_id, task in task_map.items():
        wanted = [cid for cid, case in cases.items() if case.get("final_owner_task") == task_id]
        for values in (task.get("owned_acceptance_ids"), parents[task_id].get("formal_final_cases")):
            sequence(values, "owned cases", False)
            require(len(values) == len(set(values)) and set(values) == set(wanted), "CATALOG_OWNERS", task_id)
        require(parents[task_id]["id"] == task_id + "-99", "CATALOG_PARENTS", task_id)
        owned[task_id] = wanted
    for cid, case in cases.items():
        require(case["final_owner_task"] in task_map and final_owners[cid] == case["final_owner_task"], "CATALOG_OWNERS", cid)
        assertions = sequence(case.get("assertions"), "assertions")
        ids = [text(row.get("id"), "assertion id") for row in assertions]
        require(len(ids) == len(set(ids)), "DUPLICATE_ID", cid)
    bindings = tasks["verification_command_selection"]["formal_case_bindings"]
    for cid, case in cases.items():
        selected = [row for row in bindings if row.get("case_id") == cid]
        require(bool(selected), "CATALOG_BINDINGS", cid)
        for binding in selected:
            require(binding.get("task_id") == case["final_owner_task"], "CATALOG_BINDINGS", cid)
            exact_ids(binding.get("expected_assertion_ids"), [a["id"] for a in case["assertions"]], cid)
    return cases, task_map, parents, owned, planned


def _canonical_state(reader, state_path, planned):
    path = Path(state_path).resolve(strict=True)
    require(path == (reader.repo / "execution/v2.4/step_state.json").resolve(), "CANONICAL_STATE", str(path))
    state = obj(reader.read(path), "canonical state")
    require(state.get("schema_version") == "1.0" and state.get("package_version") == "2.4.0"
            and state.get("plan_sha256") == FROZEN_HASHES["execution.plan.json"], "STATE_BASELINE", str(path))
    rows = sequence(state.get("steps"), "state steps", False)
    ids = [text(row.get("id"), "state id") for row in rows]
    require(len(ids) == len(set(ids)) and set(ids) <= set(planned), "STATE_IDS", "duplicate or unknown step")
    statuses = {"NOT_STARTED", "IN_PROGRESS", "EXECUTION_REPORTED", "ACCEPTED", "BLOCKED", "FAILED", "CANCELLED"}
    for row in rows:
        require(row.get("status") in statuses, "STATE_STATUS", row["id"])
    return {row["id"]: row for row in rows}


def _registered_roots(reader, owner, task_id):
    selected = {"review": [], "context": [], "issuance": []}
    schemas = {
        "researchos.w04.independent-review.v1": "review",
        "researchos.w04.current-context.v1": "context",
        "researchos.w04.root-observed-issuance.v1": "issuance",
    }
    seen = set()
    for reference in sequence(owner.get("evidence"), "registered owner evidence"):
        fields(reference, ("path", "sha256"), label="registered reference")
        translated = {"path": "execution/v2.4/" + reference["path"], "sha256": reference["sha256"]}
        path = reader.ref(translated)
        require(path not in seen, "DUPLICATE_REFERENCE", task_id)
        seen.add(path)
        if path.suffix != ".json":
            continue
        value = reader.read(path)
        if type(value) is dict and value.get("schema") in schemas:
            require(task_id == "W04", "UNSUPPORTED_PROTOCOL", task_id)
            key = schemas[value["schema"]]
            selected[key].append(path)
    require(all(len(values) == 1 for values in selected.values()),
            "CONFLICTING_REVIEW" if any(len(values) > 1 for values in selected.values()) else "MISSING_REGISTERED_GLOBAL_ROOT",
            task_id + ": review/context/issuance must each be registered exactly once")
    return {key: values[0] for key, values in selected.items()}


def _currentness(reader, context_path):
    context = obj(reader.read(context_path), "current applicability")
    vector_value = obj(context.get("version_vector"), "applicable vector")
    paths = set()
    for group in ("spec_files", "source_files", "input_files", "lock_files", "tool_files"):
        for reference in sequence(vector_value.get(group), group):
            paths.add(reference["path"])
            try:
                reader.ref(reference)
            except InvalidEvidence as exc:
                if exc.code in {"HASH_MISMATCH", "FILE_MISSING"}:
                    raise InvalidEvidence("NEEDS_REVALIDATION", "applicable file changed/removed: " + reference["path"]) from exc
                raise
    try:
        coverage(reader, context["source_coverage"], vector_value["source_files"])
    except InvalidEvidence as exc:
        if exc.code in {"SOURCE_COVERAGE", "SOURCE_COVERAGE_DIGEST", "FILE_MISSING"}:
            raise InvalidEvidence("NEEDS_REVALIDATION", "applicable source inventory changed: " + str(exc)) from exc
        raise
    return context, paths


def _verify_owner(reader, owner, task_id, roots, plan_path):
    require(task_id == "W04", "UNSUPPORTED_PROTOCOL", "No verified evidence profile is implemented for " + task_id)
    context, _ = _currentness(reader, roots["context"])
    require(not reader.read(roots["review"]).get("supersedes_review_refs"), "SUPERSESSION_NOT_SUPPORTED", task_id)
    review = reader.read(roots["review"])
    issuance = reader.read(roots["issuance"])
    require(stamp(review["issued_at"], "review issued_at") <= stamp(issuance["observed_at"], "root observed_at")
            <= stamp(owner.get("accepted_at"), "owner accepted_at"), "REGISTERED_TIME_ORDER", task_id)
    baseline = reader.ref(review["acceptance_baseline_ref"])
    require(baseline.name == "acceptance.json" and sha256(baseline) == FROZEN_HASHES["acceptance.json"], "FROZEN_BASELINE", task_id)
    result = _check_w04_profile(reader.repo, reader.repo / "execution/v2.4/step_state.json", baseline.parent.parent,
                                roots["context"], roots["review"], roots["issuance"], phase="registered")
    require(result["formal_accepted_count"] == 3 and set(result["eligible_owned_cases"]) == set(CASE_IDS), "PROFILE_RESULT", task_id)
    for absolute, digest in result["input_hashes"].items():
        path = Path(absolute)
        if path in reader.read_hashes:
            require(reader.read_hashes[path] == digest, "INPUT_CHANGED_DURING_READ", absolute)
        reader.read_hashes[path] = digest
    return context


def recheck_inputs(snapshot):
    """CAS dependency check; no product commands or authoritative input writes."""
    try:
        for name, digest in snapshot["files"].items():
            path = Path(name)
            require(path.is_file() and sha256(path) == digest, "INPUT_CHANGED_DURING_READ", name)
        for inventory in snapshot.get("inventories", []):
            repo = Path(inventory["repo"])
            check_reader = Reader(repo)
            coverage(check_reader, inventory["coverage"], [{"path": name} for name in inventory["paths"]])
    except (InvalidEvidence, OSError, ValueError) as exc:
        return {"status": "INVALID", "reason": str(exc)}
    return {"status": "PASS"}


def derive_formal_cases(repo_root, state_path, plan_path):
    """Derive all frozen owners from canonical registration, preserving history."""
    result = {"schema": "researchos.formal-case-index.v1", "scope": "DERIVED_READ_ONLY_CURRENT_FORMAL_STATUS",
              "integrity": "PASS", "required_formal_cases": 42, "accepted_case_ids": [], "formal_cases_accepted": 0,
              "cases": [], "owners": [], "reasons": [], "input_hashes": {}, "catalog_hashes": dict(FROZEN_HASHES),
              "product_business_acceptance_created": False, "dependency_snapshot": {"files": {}, "inventories": []}}
    reader = None
    try:
        reader = Reader(repo_root)
        cases, tasks, parents, owned, planned = _catalog(reader, plan_path)
        rows = _canonical_state(reader, state_path, planned)
    except (InvalidEvidence, OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        result.update(integrity="INVALID", reasons=[{"code": getattr(exc, "code", "GLOBAL_INPUT_INVALID"), "detail": str(exc)}])
        if reader is not None:
            result["input_hashes"] = {str(path): digest for path, digest in reader.read_hashes.items()}
            result["dependency_snapshot"]["files"] = dict(result["input_hashes"])
        return result
    for task_id in tasks:
        row = rows.get(parents[task_id]["id"], {})
        owner = {"task_id": task_id, "step_id": parents[task_id]["id"], "parent_status": row.get("status", "NOT_STARTED"),
                 "owned_case_ids": owned[task_id], "accepted_case_ids": [], "integrity": "NOT_RUN", "reasons": []}
        if not owned[task_id]:
            owner["integrity"] = "EMPTY_OWNER"
        elif row.get("status") != "ACCEPTED":
            owner["integrity"] = "NOT_RUN" if row.get("status", "NOT_STARTED") == "NOT_STARTED" else "PENDING_OWNER_ACCEPTANCE"
        else:
            try:
                require(task_id == "W04", "UNSUPPORTED_PROTOCOL", "Evidence profile has not been independently implemented for " + task_id)
                roots = _registered_roots(reader, row, task_id)
                context = _verify_owner(reader, row, task_id, roots, plan_path)
                owner.update(integrity="VALID_ACCEPTED", accepted_case_ids=list(owned[task_id]))
                result["dependency_snapshot"]["inventories"].append({"repo": str(reader.repo), "coverage": context["source_coverage"],
                                                                      "paths": [ref["path"] for ref in context["version_vector"]["source_files"]]})
            except (InvalidEvidence, OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
                code = getattr(exc, "code", "OWNER_EVIDENCE_INVALID")
                owner["integrity"] = "NEEDS_REVALIDATION" if code in {"NEEDS_REVALIDATION", "TOOL_CHANGED", "SOURCE_COVERAGE"} else (
                    "PARTIAL" if code in {"MISSING_REGISTERED_GLOBAL_ROOT", "MISSING_FIELD", "DEPENDENCY", "UNREGISTERED_REFERENCE"} else "INVALID")
                owner["reasons"] = [{"code": code, "detail": str(exc)}]
                result["reasons"].append({"task_id": task_id, **owner["reasons"][0]})
        result["owners"].append(owner)
        for cid in owned[task_id]:
            result["cases"].append({"case_id": cid, "final_owner_task": task_id, "required_mode": cases[cid]["mode"],
                                    "status": owner["integrity"], "reasons": owner["reasons"]})
        result["accepted_case_ids"].extend(owner["accepted_case_ids"])
    try:
        reader.finish()
    except (InvalidEvidence, OSError) as exc:
        result.update(integrity="INVALID", accepted_case_ids=[], reasons=result["reasons"] + [{"code": "INPUT_CHANGED_DURING_READ", "detail": str(exc)}])
        for owner in result["owners"]:
            owner["accepted_case_ids"] = []
            if owner["integrity"] == "VALID_ACCEPTED":
                owner["integrity"] = "NEEDS_REVALIDATION"
        for case in result["cases"]:
            if case["status"] == "VALID_ACCEPTED":
                case["status"] = "NEEDS_REVALIDATION"
    if result["integrity"] == "PASS" and result["reasons"]:
        result["integrity"] = "PARTIAL"
    result["accepted_case_ids"] = sorted(set(result["accepted_case_ids"]))
    result["formal_cases_accepted"] = len(result["accepted_case_ids"])
    result["input_hashes"] = {str(path): digest for path, digest in reader.read_hashes.items()}
    result["dependency_snapshot"]["files"] = dict(result["input_hashes"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    result = derive_formal_cases(args.repo, args.state, args.plan)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
