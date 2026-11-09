package domain

import (
 "context"
 "fmt"
 "io"
 "net/http"
 "strconv"
 "strings"
 "testing"
 "time"
 "researchos.local/research-os/adapters/sources"
)

// Every request is answered in memory. No socket, browser, or provider is used.
type verifierTransport func(*http.Request) (*http.Response,error)
func(f verifierTransport) RoundTrip(r *http.Request)(*http.Response,error){ return f(r) }
func verifierResponse(r *http.Request, body string, h http.Header)*http.Response{
 if h==nil {h=make(http.Header)}
 return &http.Response{StatusCode:200,Header:h,Body:io.NopCloser(strings.NewReader(body)),Request:r}
}

func TestVerifierW07MalformedEmpty(t *testing.T){
 from:=time.Date(2026,9,28,0,0,0,0,time.UTC)
 q:=sources.Query{SourceID:"g",Text:"repo:paperclipai/paperclip",From:from,To:from.Add(24*time.Hour),Limit:20}
 for _, body:=range []string{"null","[]"}{
  client:=&http.Client{Transport:verifierTransport(func(r *http.Request)(*http.Response,error){return verifierResponse(r,body,nil),nil})}
  p,e:=(sources.GitHubReleases{Client:client}).Fetch(context.Background(),q)
  t.Logf("github raw=%q complete=%v failure=%q items=%d err=%v",body,p.Complete,p.Failure,len(p.Items),e)
  if body=="null"&&p.Complete {t.Error("invalid null release response was accepted as complete empty coverage")}
  if body=="[]"&&(e!=nil||!p.Complete||p.Failure!=""){t.Error("valid GitHub empty positive control failed")}
 }
 q.Text="id:2304.03442v2"
 for _,body:=range []string{`<html><body>upstream temporarily unavailable</body></html>`,`<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>0</opensearch:totalResults></feed>`}{
  client:=&http.Client{Transport:verifierTransport(func(r *http.Request)(*http.Response,error){return verifierResponse(r,body,nil),nil})}
  p,e:=(&sources.Arxiv{Client:client}).Fetch(context.Background(),q)
  t.Logf("arxiv raw=%q complete=%v failure=%q items=%d err=%v",body,p.Complete,p.Failure,len(p.Items),e)
  if strings.HasPrefix(body,"<html>")&&p.Complete {t.Error("HTML error response was accepted as complete empty arXiv coverage")}
  if strings.HasPrefix(body,"<feed")&&(e!=nil||!p.Complete||p.Failure!=""){t.Error("valid arXiv empty positive control failed")}
 }
}

func TestVerifierW07ChangedPageLimit(t *testing.T){
 f,_,cursor:=sourceProject(t)
 actor:=Principal{ID:"verifier-w07-page-limit",Roles:[]string{"SOURCE_ADAPTER"},Grants:[]Grant{{ProjectID:f.project}}}
 if e:=f.s.ProvisionPrincipal(context.Background(),actor);e!=nil{t.Fatal(e)}
 token,e:=f.s.IssueCredential(context.Background(),actor.ID,time.Minute);if e!=nil{t.Fatal(e)}
 f.token=token
 client:=&http.Client{Transport:verifierTransport(func(r *http.Request)(*http.Response,error){
  if strings.Contains(r.URL.Path,"/commits/"){return verifierResponse(r,`{"sha":"0123456789abcdef0123456789abcdef01234567"}`,nil),nil}
  limit,_:=strconv.Atoi(r.URL.Query().Get("per_page")); page,_:=strconv.Atoi(r.URL.Query().Get("page"))
  start:=(page-1)*limit; end:=start+limit;if end>100{end=100}
  entries:=[]string{}
  for i:=start;i<end;i++{entries=append(entries,fmt.Sprintf(`{"id":%d,"html_url":"https://github.com/paperclipai/paperclip/releases/tag/v%d","body":"full release %d","tag_name":"v%d","published_at":"2026-09-28T12:00:00Z","author":{"login":"maintainer"}}`,i+1,i+1,i+1,i+1))}
  h:=make(http.Header);if end<100{h.Set("Link",fmt.Sprintf(`<https://api.github.com/repos/paperclipai/paperclip/releases?per_page=%d&page=%d>; rel="next"`,limit,page+1))}
  t.Logf("memory provider request page=%d per_page=%d returned=%d dataset=100",page,limit,len(entries))
  return verifierResponse(r,"["+strings.Join(entries,",")+"]",h),nil
 })}
 adapter:=sources.GitHubReleases{Client:client}
 from:=time.Date(2026,9,28,0,0,0,0,time.UTC);to:=from.Add(24*time.Hour)
 config,current,e:=f.s.sourceConfig(context.Background(),token,f.project,Str(cursor,"id"));if e!=nil{t.Fatal(e)}
 first,e:=f.s.captureSourcePage(context.Background(),token,f.project,current,config,from,to,1,adapter);if e!=nil{t.Fatal(e)}
 if len(first.Evidence)!=1||first.Page.NextCursor!="2"{t.Fatalf("unexpected initial page: %+v",first.Page)}
 update:=Object{"opaque_cursor":"2","covered_until":nil,"last_success_at":Now(),"retry_after":nil,"pending_window_from":from.Format(time.RFC3339Nano),"pending_window_to":to.Format(time.RFC3339Nano),"last_cycle_id":nil}
 current=f.expect(200,"PUT",f.path("/source-cursors/"+Str(cursor,"id")),ID(),testTag(current),update)
 config,current,e=f.s.sourceConfig(context.Background(),token,f.project,Str(cursor,"id"));if e!=nil{t.Fatal(e)}
 second,e:=f.s.captureSourcePage(context.Background(),token,f.project,current,config,from,to,100,adapter);if e!=nil{t.Logf("changed limit rejected: %v",e);return}
 update=Object{"opaque_cursor":nil,"covered_until":to.Format(time.RFC3339Nano),"last_success_at":Now(),"retry_after":nil,"pending_window_from":nil,"pending_window_to":nil,"last_cycle_id":nil}
 status,after,_:=f.request("PUT",f.path("/source-cursors/"+Str(cursor,"id")),ID(),testTag(current),update)
 t.Logf("second complete=%v items=%d advance_status=%d evidence_count=%d covered_until=%v",second.Page.Complete,len(second.Evidence),status,countKind(t,f.db,"Evidence"),after["covered_until"])
 if status==200&&after["covered_until"]==to.Format(time.RFC3339Nano){t.Error("coverage advanced across 99 omitted releases after changing per_page from 1 to 100")}
}

func TestVerifierW07ProviderRetryIsPersisted(t *testing.T){
 f,_,cursor:=sourceProject(t)
 actor:=Principal{ID:"verifier-w07-retry",Roles:[]string{"SOURCE_ADAPTER"},Grants:[]Grant{{ProjectID:f.project}}}
 if e:=f.s.ProvisionPrincipal(context.Background(),actor);e!=nil{t.Fatal(e)}
 token,e:=f.s.IssueCredential(context.Background(),actor.ID,time.Minute);if e!=nil{t.Fatal(e)}
 calls:=0
 client:=&http.Client{Transport:verifierTransport(func(r *http.Request)(*http.Response,error){
  calls++;h:=make(http.Header);h.Set("Retry-After","60")
  response:=verifierResponse(r,`{"message":"rate limited"}`,h);response.StatusCode=429
  return response,nil
 })}
 adapter:=sources.GitHubReleases{Client:client}
 from:=time.Date(2026,9,28,0,0,0,0,time.UTC);to:=from.Add(24*time.Hour)
 for attempt:=1;attempt<=2;attempt++{
  config,current,e:=f.s.sourceConfig(context.Background(),token,f.project,Str(cursor,"id"));if e!=nil{t.Fatal(e)}
  result,e:=f.s.captureSourcePage(context.Background(),token,f.project,current,config,from,to,1,adapter)
  t.Logf("attempt=%d stored_retry_after=%v result_failure=%s returned_retry_after=%v provider_calls=%d err=%v",attempt,current["retry_after"],result.Page.Failure,result.Page.RetryAfter,calls,e)
  if e!=nil||result.Page.Failure!="RATE_LIMITED"||result.Page.RetryAfter==nil {t.Fatal("unexpected rate-limit response")}
 }
 if calls!=1{t.Error("second product capture issued a provider request before the returned Retry-After expired")}
}
