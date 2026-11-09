import hashlib,json,re,pathlib
root=pathlib.Path(r"D:/作品集/ResearchOS/research-os")
out=pathlib.Path(r"C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-artifact-scope")
out.mkdir(exist_ok=True)
module="researchos.local/research-os/"
oses=set("aix android darwin dragonfly freebsd hurd illumos ios js linux netbsd openbsd plan9 solaris wasip1 windows".split())
arches=set("386 amd64 arm arm64 loong64 mips mips64 mips64le mipsle ppc64 ppc64le riscv64 s390x wasm".split())
def tag(v):
    if v in ("windows","amd64","amd64.v1","gc"):return True
    if v.startswith("go1.") and v[4:].isdigit():return int(v[4:])<=27
    return False
def enabled(text):
    match=re.search(r"(?m)^//go:build (.+)$",text)
    if not match:return True
    values=re.findall(r"&&|\|\||!|\(|\)|[A-Za-z0-9_.]+",match.group(1));i=0
    def atom():
        nonlocal i
        v=values[i];i+=1
        if v=="!":return not atom()
        if v=="(":
            answer=expr_or()
            if values[i]!=")":raise ValueError("bad build condition")
            i+=1;return answer
        return tag(v)
    def expr_and():
        nonlocal i
        answer=atom()
        while i<len(values) and values[i]=="&&":
            i+=1;other=atom();answer=answer and other
        return answer
    def expr_or():
        nonlocal i
        answer=expr_and()
        while i<len(values) and values[i]=="||":
            i+=1;other=expr_and();answer=answer or other
        return answer
    answer=expr_or()
    if i!=len(values):raise ValueError("unparsed build expression")
    return answer
def file_enabled(p,text):
    name=p.stem
    if name.startswith(("_",".")) or name.endswith("_test"):return False
    bits=name.split("_")
    if bits[-1] in arches:
        if bits[-1]!="amd64":return False
        bits=bits[:-1]
    if bits[-1] in oses and bits[-1]!="windows":return False
    return enabled(text)
def lex(text):
    answer=[];i=0;n=len(text)
    while i<n:
        c=text[i]
        if c.isspace():i+=1;continue
        if text.startswith("//",i):
            end=text.find("\n",i);i=n if end<0 else end+1;continue
        if text.startswith("/*",i):
            end=text.find("*/",i+2)
            if end<0:raise ValueError("unclosed comment")
            i=end+2;continue
        if c in ('"', "'", chr(96)):
            quote=c;j=i+1
            while j<n:
                if quote!=chr(96) and text[j]=="\\":j+=2;continue
                if text[j]==quote:break
                j+=1
            answer.append(("string" if quote in ('"',chr(96)) else "rune",text[i+1:j]));i=j+1;continue
        if c.isalpha() or c=="_":
            j=i+1
            while j<n and (text[j].isalnum() or text[j]=="_"):j+=1
            answer.append(("word",text[i:j]));i=j;continue
        answer.append(("punct",c));i+=1
    return answer
def imports(text):
    ts=lex(text);answer=[];i=0
    while i<len(ts):
        if ts[i]!=("word","import"):i+=1;continue
        i+=1
        if ts[i]==("punct","("):
            i+=1
            while ts[i]!=("punct",")"):
                if ts[i][0]=="string":answer.append(ts[i][1])
                i+=1
        else:
            while i<len(ts) and ts[i][0]!="string":i+=1
            if i<len(ts):answer.append(ts[i][1])
        i+=1
    return answer
todo=["apps/cli"];packages={};missing=[];external=set();embeds=[]
while todo:
    name=todo.pop()
    if name in packages:continue
    directory=root/name
    if not directory.is_dir():missing.append(name);continue
    selected=[];local=set()
    for path in sorted(directory.glob("*.go")):
        text=path.read_text(encoding="utf-8-sig")
        if not file_enabled(path,text):continue
        selected.append(path)
        for item in imports(text):
            if item.startswith(module):local.add(item[len(module):])
            else:external.add(item)
        for line in re.findall(r"(?m)^//go:embed\s+(.+)$",text):
            for pattern in line.split():
                pattern=pattern.strip('"')
                if pattern.startswith("all:"):pattern=pattern[4:]
                for candidate in directory.glob(pattern):
                    if candidate.is_file():embeds.append(candidate)
                    elif candidate.is_dir():embeds.extend(x for x in candidate.rglob("*") if x.is_file())
    packages[name]={"files":selected,"imports":sorted(local)}
    todo.extend(sorted(local))
def row(p):
    data=p.read_bytes()
    return {"path":p.relative_to(root).as_posix(),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
rows=[row(p) for name in sorted(packages) for p in packages[name]["files"]]
embed_rows=[row(p) for p in sorted(set(embeds))]
plan={"schema":"researchos.cli-static-production-go-closure.v1","method":"read-only Go lexical import traversal; windows amd64 CGO_ENABLED=0; no Go tools/build/test invoked","root":str(root),"packages":[{"path":name,"file_count":len(packages[name]["files"]),"local_imports":packages[name]["imports"]} for name in sorted(packages)],"missing_packages":sorted(set(missing)),"production_go_files":rows,"embed_files":embed_rows,"standard_or_external_imports":sorted(external),"caveat":"Static scope only. Final clean worktree go list -deps -compiled -json under the exact build environment is authoritative for compiled/stdlib/module/assembly/embed closure; this is not a build or runtime qualification."}
(out/"static-go-closure.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"package_count":len(packages),"go_files":len(rows),"embed_files":len(embed_rows),"missing":plan["missing_packages"],"sparse_package_directories":sorted(packages)},ensure_ascii=False))

