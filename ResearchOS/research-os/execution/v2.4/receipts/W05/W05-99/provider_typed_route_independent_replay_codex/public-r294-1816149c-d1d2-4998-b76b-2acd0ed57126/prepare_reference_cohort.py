import pathlib,json,hashlib,difflib
H=pathlib.Path(__file__).resolve().parent;O=H.parent/'79e9ab97-1451-4537-94db-e8259c9c67fa';M=pathlib.Path('D:/作品集/ResearchOS/research-os');I=M/'.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c';A=M/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli6-and-reference-closure-r294/public12_reference_scope_amendment.json'
def ref(p):p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,v):
 with (H/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
assert ref(A)['sha256']=='32c41db93f2ed3408951728ec75cee117afb02699504268ba178bade6aa8af5e'
source=I/'internal/domain/store.go';assert ref(source)['sha256']=='3cde487cd621cabb307f12bf0d1aae4dce51285de68f843f05a5f0ac0b51beb1'
sr=source.read_text('utf8');mapping=sr[sr.index('var idTargets = ')+len('var idTargets = '):sr.index('\n\nfunc relationKind')]
oldp=O/'independent_provider_public_boundary_windows_test.go';old=oldp.read_text('utf8');lo=old.index('\trefs := independentNewRows(t, before, after, "domain_refs")');hi=old.index('\t// Every original effect row remains.',lo)
branch=r'''	// Independent frozen producer reconstruction: never invoke Service.refs/ref/put.
	refs := independentNewRows(t, before, after, "domain_refs")
	relationTargets := FROZEN_MAPPING
	currentAtPut := map[string]Object{}
	for k, row := range oldobj { currentAtPut[k] = row }
	historyRows := map[string]Object{}
	for _, row := range independentCellRows(after, "domain_versions") {
		k := versionKey(Str(row,"project"),Str(row,"kind"),Str(row,"id"),independentNumber(t,row,"revision"))
		if historyRows[k] != nil { t.Fatal("duplicate immutable target version") }
		historyRows[k] = row
	}
	expectedRefCounts := map[string]int{}
	expectedRefTotal := 0
	generatedOwners := map[string]bool{}
	var generateOwner func(string,string,Object)
	generateOwner = func(project, kind string, body Object) {
		id := Str(body,"id"); revision := independentNumber(t,body,"revision")
		ownerKey := versionKey(project,kind,id,revision)
		expected := expectedVersions[ownerKey]
		if expected == nil || generatedOwners[ownerKey] || Hash(body) != Hash(expected["body"]) { t.Fatal("reference producer owner mismatch",ownerKey) }
		generatedOwners[ownerKey] = true
		ownerRow := historyRows[ownerKey]
		if ownerRow == nil || Hash(independentBody(t,ownerRow)) != Hash(body) || Hash(ownerRow["content_hash"]) != Hash(expected["content_hash"]) { t.Fatal("reference owner immutable witness") }
		currentAtPut[project+"|"+kind+"|"+id] = ownerRow
		add := func(field,tp,tk,tid string,tr int64,wantHash any,exact bool) {
			if tp!=project && !(tp=="" && (tk=="BudgetPolicy" || tk=="RunPolicy")) { t.Fatal("reference foreign target") }
			latest := currentAtPut[tp+"|"+tk+"|"+tid]
			if latest==nil { t.Fatal("reference producer-time target absent",field) }
			latestRev := independentNumber(t,latest,"revision")
			target := latest
			// Newly produced owner kinds are fixed Run/ProjectState/EventEnvelope.
			// EventEnvelope may carry an exact historical VersionRef; other two require current.
			if exact && kind=="EventEnvelope" { target=historyRows[versionKey(tp,tk,tid,tr)]
			} else if exact && latestRev!=tr { t.Fatal("reference exact producer-time revision mismatch") }
			if target==nil { t.Fatal("reference immutable target absent") }
			targetRevision := independentNumber(t,target,"revision")
			if targetRevision!=tr { t.Fatal("reference requested target revision differs") }
			witness:=historyRows[versionKey(tp,tk,tid,tr)]
			if witness==nil || Str(witness,"body")!=Str(target,"body") || Hash(witness["content_hash"])!=Hash(target["content_hash"]) { t.Fatal("reference complete target history witness differs") }
			if exact && Hash(wantHash)!=Hash(witness["content_hash"]) { t.Fatal("reference VersionRef content hash mismatch") }
			tuple:=Object{"project":project,"kind":kind,"id":id,"revision":fmt.Sprint(revision),"field":field,"target_project":tp,"target_kind":tk,"target_id":tid,"target_revision":fmt.Sprint(tr)}
			expectedRefCounts[Hash(tuple)]++; expectedRefTotal++
		}
		var walk func(string,any)
		walk = func(path string,value any) {
			switch v:=value.(type) {
			case map[string]any:
				if _,ok:=v["entity_type"];ok {
					if len(v)!=4 { t.Fatal("VersionRef shape") }
					tk,ok1:=v["entity_type"].(string);tid,ok2:=v["id"].(string);if !ok1||!ok2||tk==""||tid=="" {t.Fatal("VersionRef identity")}
					if _,ok:=v["content_hash"];!ok {t.Fatal("VersionRef missing content hash")}
					add(path,project,tk,tid,independentNumber(t,v,"revision"),v["content_hash"],true);return
				}
				for field,x:=range v {
					if field=="id" || field=="project_id" {continue}
					target:=relationTargets[field]
					if kind=="RuntimeRegistration" && field=="qualification_ids" {target="AcceptanceReceipt"}
					if field=="supersedes_id" || field=="parent_policy_id" {target=kind}
					if target!="" && x!=nil {
						values:=[]any{x};if array,ok:=x.([]any);ok {values=array}
						for _,member:=range values {
							tid,ok:=member.(string);if !ok {t.Fatal("relation member is not string")}
							tp:=project;if field=="parent_policy_id" && currentAtPut[tp+"|"+target+"|"+tid]==nil {tp=""}
							row:=currentAtPut[tp+"|"+target+"|"+tid];if row==nil {t.Fatal("relation target missing",field)}
							add(path+"/"+field,tp,target,tid,independentNumber(t,row,"revision"),nil,false)
						}
					} else {walk(path+"/"+field,x)}
				}
			case []any:
				for n,x:=range v {walk(fmt.Sprintf("%s/%d",path,n),x)}
			}
		}
		walk("",body)
	}
	// Each original Run is put, then its ProjectState, then EventEnvelope; use the
	// already independently checked per-project actual event order, not final latest.
	for _, entry:=range chain {
		c:=entry.(Object);run:=c["restored_run"].(Object);event:=c["event"].(Object);snapshot:=c["snapshot"].(Object)
		project:=Str(event,"project_id")
		generateOwner(project,"Run",run)
		generateOwner(project,"ProjectState",snapshot)
		generateOwner(project,"EventEnvelope",event)
	}
	if len(generatedOwners)!=len(expectedVersions) || len(refs)!=expectedRefTotal {t.Fatal("reference complete producer closure count")}
	rowids:=map[int64]bool{}
	for _,r:=range independentCellRows(before,"domain_refs") {id:=independentNumber(t,r,"rowid");if id<1||rowids[id] {t.Fatal("old reference rowid")};rowids[id]=true}
	actualRefCounts:=map[string]int{}
	for _,r:=range refs {
		id:=independentNumber(t,r,"rowid");if id<1||rowids[id] {t.Fatal("new reference rowid duplicate")};rowids[id]=true
		if len(r)!=10 {t.Fatal("reference row shape")}
		actualRefCounts[Hash(independentClone(r,"rowid"))]++
	}
	if Hash(actualRefCounts)!=Hash(expectedRefCounts) {t.Fatal("complete reference multiset differs",actualRefCounts,expectedRefCounts)}
'''.replace('FROZEN_MAPPING',mapping)
new=old[:lo]+branch+old[hi:];(H/oldp.name).write_text(new,encoding='utf8',newline='\n');(H/'overlay-reference-only.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(oldp),tofile=str(H/oldp.name))),encoding='utf8')
write('edit-boundary-proof.json',{'original_overlay':ref(oldp),'original_branch_lines':[old[:lo].count('\n')+1,old[:hi].count('\n')],'unchanged_prefix_sha256':hashlib.sha256(old[:lo].encode()).hexdigest(),'unchanged_suffix_sha256':hashlib.sha256(old[hi:].encode()).hexdigest(),'new_prefix_same':new[:lo]==old[:lo],'new_suffix_same':new.endswith(old[hi:]),'frozen_producer_source':ref(source),'scope':ref(A)})
(H/'export.json').write_bytes((O/'export.json').read_bytes());(H/'synthetic_workspace_evidence.txt').write_bytes((O/'synthetic_workspace_evidence.txt').read_bytes());(H/'inputs').mkdir();originals=json.loads((O/'original7.before.json').read_text('utf8'))
for e in originals:
 src=pathlib.Path(e['original']['path']);assert ref(src)==e['original'];dst=H/'inputs'/(e['id']+'.sqlite');dst.write_bytes(src.read_bytes());e['copy']=ref(dst)
write('original7.before.json',originals);write('amendment-ref.json',ref(A));(H/'driver.py').write_text((O/'driver.py').read_text('utf8').replace('cache-r292','cache-r294'),encoding='utf8',newline='\n')
write('cohort.json',{'scope':ref(A),'prior_stopped_public_review':ref(O/'review.json'),'prior_stopped_public_binary':ref(O/'independent.domain.test.exe'),'original_internal64_review':ref(H.parent/'cc88ef8c-d066-4b10-b6c5-1d9bba89baad/review.json'),'original_internal64_binary':ref(H.parent/'cc88ef8c-d066-4b10-b6c5-1d9bba89baad/independent.domain.test.exe'),'prior_actual':66,'prior_PASS':64,'prior_FAIL':2,'new_public_limit':12,'cumulative_max78':True,'no_executable_equivalence_claim':True})
print(json.dumps({'overlay':ref(H/oldp.name),'bounds':ref(H/'edit-boundary-proof.json')},ensure_ascii=True))
