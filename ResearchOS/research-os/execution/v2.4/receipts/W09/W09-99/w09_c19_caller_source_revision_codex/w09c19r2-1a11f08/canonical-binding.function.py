def bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,vector_path,vector_sha,vector_bytes):
 assert len(vector_sha)==64 and all(c in "0123456789abcdef" for c in vector_sha), "CANONICAL_VECTOR_HASH_FORMAT"
 assert type(vector_bytes) is int and 0<vector_bytes<=65536, "CANONICAL_VECTOR_SIZE"
 path=Path(vector_path)
 assert path.is_absolute(), "CANONICAL_VECTOR_ABSOLUTE_PATH"
 path=path.resolve(strict=True)
 assert path.name=="canonical-input-vector.json" and path.is_relative_to((R/"execution/v2.4/receipts/W09/W09-99").resolve()), "CANONICAL_VECTOR_NAMESPACE"
 with path.open("rb") as stream:raw=stream.read(vector_bytes+1)
 assert len(raw)==vector_bytes and hashlib.sha256(raw).hexdigest()==vector_sha, "CANONICAL_VECTOR_PIN"
 vector=json.loads(raw)
 assert isinstance(vector,dict) and set(vector)=={"schema","checkpoint_revision","refs"}, "CANONICAL_VECTOR_FIELDS"
 assert vector["schema"]=="researchos.w09-c19-canonical-input-vector.v1", "CANONICAL_VECTOR_SCHEMA"
 assert type(vector["checkpoint_revision"]) is int and vector["checkpoint_revision"]==checkpoint_revision and checkpoint_revision>0, "CANONICAL_VECTOR_REVISION"
 refs=vector["refs"]
 assert isinstance(refs,list) and len(refs)==4, "CANONICAL_VECTOR_EXACT_FOUR"
 fixed={str(p.resolve()):p for p in canonical};observed={}
 for ref in refs:
  assert isinstance(ref,dict) and set(ref)=={"path","sha256","bytes"}, "CANONICAL_REF_FIELDS"
  assert isinstance(ref["path"],str) and Path(ref["path"]).is_absolute(), "CANONICAL_REF_ABSOLUTE_PATH"
  key=str(Path(ref["path"]).resolve())
  assert key in fixed and key not in observed, "CANONICAL_REF_FIXED_UNIQUE_PATH"
  assert isinstance(ref["sha256"],str) and len(ref["sha256"])==64 and all(c in "0123456789abcdef" for c in ref["sha256"]), "CANONICAL_REF_HASH_FORMAT"
  assert type(ref["bytes"]) is int and 0<ref["bytes"]<=64*1024*1024, "CANONICAL_REF_SIZE"
  data=before[fixed[key]]
  assert len(data)==ref["bytes"] and hashlib.sha256(data).hexdigest()==ref["sha256"], "CANONICAL_REF_PIN"
  observed[key]={"path":key,"sha256":ref["sha256"],"bytes":ref["bytes"]}
 assert set(observed)==set(fixed), "CANONICAL_VECTOR_FIXED_SET"
 cp=observed[str(canonical[0].resolve())]
 assert cp["sha256"]==checkpoint_sha and cp["bytes"]==checkpoint_bytes, "CANONICAL_CHECKPOINT_ARGUMENTS"
 assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision, "CANONICAL_CHECKPOINT_REVISION"
 return {"path":str(path),"sha256":vector_sha,"bytes":vector_bytes},[observed[str(p.resolve())] for p in canonical]

