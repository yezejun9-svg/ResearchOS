package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"regexp"
	"time"
	"researchos.local/research-os/internal/canonical"
)

const NativeCreateAttestationHeader = "X-ResearchOS-Native-Attestation"
var nativeAttestationRefPattern = regexp.MustCompile(`^natt-[0-9a-f]{64}$`)

type NativeCreateCredential struct {
	Principal, AuthorityRoot, CredentialHash string
	ExpiresAt time.Time
}

type nativeMarkedCommandHeader struct {
	Schema string `json:"schema"`
	Encoding string `json:"encoding"`
	Raw string `json:"raw_envelope_base64"`
	Origin nativeCreateOriginMarker `json:"native_create_origin"`
}

func nativeOriginMarkedHeader(old string,marker nativeCreateOriginMarker)(string,error){
	var h clientCommandHeader
	if json.Unmarshal([]byte(old),&h)!=nil||h.Schema!=clientCommandHeaderSchema||h.Encoding!="base64"{return "",fmt.Errorf("NATIVE_ORIGIN_HEADER_SEAL")}
	return string(Bytes(nativeMarkedCommandHeader{nativeCommandHeaderSchema,h.Encoding,h.Raw,marker})),nil
}

func readNativeMarkedCommandEnvelope(doc *SchemaDoc,headers string)(clientIdentityRequest,bool,error){
	var zero clientIdentityRequest
	if len(headers)>clientCommandHeaderMax+1024{return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_SIZE")}
	strict,err:=canonical.JSON([]byte(headers));if err!=nil{return zero,true,err}
	var fields map[string]json.RawMessage
	if json.Unmarshal(strict,&fields)!=nil||len(fields)!=4{return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_SCHEMA")}
	for _,name:=range []string{"schema","encoding","raw_envelope_base64","native_create_origin"}{if _,ok:=fields[name];!ok{return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_SCHEMA")}}
	var h nativeMarkedCommandHeader;d:=json.NewDecoder(bytes.NewReader(strict));d.DisallowUnknownFields()
	if d.Decode(&h)!=nil||h.Schema!=nativeCommandHeaderSchema||h.Encoding!="base64"||h.Origin.SchemaVersion!=1||!nativeAttestationRefPattern.MatchString(h.Origin.AttestationRef)||!nativeDigest(h.Origin.WitnessHash)||!nativeDigest(h.Origin.OriginHash)||!bytes.Equal(Bytes(h),[]byte(headers)){return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_SCHEMA")}
	raw,err:=base64.StdEncoding.Strict().DecodeString(h.Raw)
	if err!=nil||len(raw)==0||len(raw)>clientIdentityMaxRequest||base64.StdEncoding.EncodeToString(raw)!=h.Raw{return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_BASE64")}
	env,err:=decodeClientIdentityEnvelope(doc,raw);if err!=nil{return zero,true,err}
	if deref(env.Method)!="session.create"||env.SessionID!=nil||env.ExpectedRevision!=nil||env.WriterEpoch!=nil{return zero,true,fmt.Errorf("NATIVE_ORIGIN_HEADER_METHOD")}
	req,err:=validateClientIdentityRequest(doc,raw,env);if err!=nil{return zero,true,err};req.nativeOrigin=&h.Origin;return req,true,nil
}


// Real bearer resolution, not an identity constructor or a new credential issuer.
func (s *Service) ResolveNativeCreateCredential(ctx context.Context, tx *sql.Tx, token, project string) (NativeCreateCredential, error) {
	if s == nil || tx == nil || token == "" || project == "" { return NativeCreateCredential{}, ErrNoCredential }
	p, credential, err := authenticateWithCredential(tx, token)
	if err != nil { return NativeCreateCredential{}, err }
	owner, err := clientPrincipal(ctx, tx, p.ID, project, true)
	if err != nil || owner.DeviceID != "" { return NativeCreateCredential{}, Fail(403,"FORBIDDEN","local project Owner required") }
	root, err := s.currentAuthorityRoot(ctx, tx, p.ID)
	if err != nil { return NativeCreateCredential{}, err }
	return NativeCreateCredential{p.ID,root,credential.hash,credential.expiresAt},nil
}

type NativeCreateProofQuery struct {
	Service *ClientService
	Store *sql.DB
	AttestationRef, Principal, AuthorityRoot, CredentialHash string
	CredentialExpiresAt time.Time
	CommandID, ClientID, ProjectID, Method, ActualRawSHA256 string
	SessionID *string
	ExpectedRevision, WriterEpoch *int64
}

type VerifiedNativeCreateOrigin struct {
	WitnessRef, WitnessSHA256, ClientInstanceRef string
	HostInstanceID, HostGenerationRef, OSSubjectRef string
	Principal, AuthorityRoot, CredentialHash string
	CommandID, ClientID, ProjectID, Method, ActualRawSHA256 string
	IssuedAt, ExpiresAt time.Time
}

type NativeCreateAuthority interface {
	VerifyNativeCreate(context.Context,*sql.Tx,NativeCreateProofQuery)(VerifiedNativeCreateOrigin,error)
}
type NativeCreateAuthorityBinder interface {
	BindNativeCreateAuthority(*ClientService)(NativeCreateAuthority,error)
}

type nativeCreateClaimKey struct{}

// The value is only an untrusted selector. It cannot create credential or Native facts.
func WithNativeCreateAttestationReference(ctx context.Context, ref string)(context.Context,error) {
	if ctx == nil || !nativeAttestationRefPattern.MatchString(ref) { return nil,fmt.Errorf("NATIVE_CREATE_REFERENCE_INVALID") }
	return context.WithValue(ctx,nativeCreateClaimKey{},ref),nil
}

func (s *ClientService) authorizeNativeCreate(ctx context.Context,tx *sql.Tx,env *Envelope,principal string)(*VerifiedNativeCreateOrigin,error) {
	ref,_:=ctx.Value(nativeCreateClaimKey{}).(string)
	if ref=="" { return nil,nil }
	if deref(env.Method)!="session.create" || env.ProjectID==nil || env.SessionID!=nil || env.ExpectedRevision!=nil || env.WriterEpoch!=nil {
		return nil,Fail(403,"FORBIDDEN","Native origin supports fresh session.create only")
	}
	if err:=requireNativeOriginSchema(ctx,tx);err!=nil{return nil,err}
	credential,ok:=commandCredentialFromContext(ctx,tx,s,principal)
	if !ok || !time.Now().Before(credential.expiresAt) || s.Domain==nil || s.NativeCreateAuthority==nil {
		return nil,Fail(403,"FORBIDDEN","current Native create authority required")
	}
	owner,err:=clientPrincipal(ctx,tx,principal,deref(env.ProjectID),true)
	if err!=nil || owner.DeviceID!="" {return nil,Fail(403,"FORBIDDEN","local Owner required")}
	root,err:=s.Domain.currentAuthorityRoot(ctx,tx,principal);if err!=nil{return nil,err}
	q:=NativeCreateProofQuery{Service:s,Store:s.Domain.DB,AttestationRef:ref,Principal:principal,AuthorityRoot:root,CredentialHash:credential.hash,CredentialExpiresAt:credential.expiresAt,
		CommandID:deref(env.CommandID),ClientID:deref(env.ClientID),ProjectID:deref(env.ProjectID),Method:deref(env.Method),ActualRawSHA256:Digest(env.originalRaw)}
	v,err:=s.NativeCreateAuthority.VerifyNativeCreate(ctx,tx,q);if err!=nil{return nil,Fail(403,"FORBIDDEN","current Native create witness unavailable")}
	if v.WitnessRef!=ref || v.Principal!=principal || v.AuthorityRoot!=root || v.CredentialHash!=credential.hash || v.CommandID!=q.CommandID || v.ClientID!=q.ClientID || v.ProjectID!=q.ProjectID || v.Method!="session.create" || v.ActualRawSHA256!=q.ActualRawSHA256 || !time.Now().Before(v.ExpiresAt) || v.ExpiresAt.After(credential.expiresAt) || v.IssuedAt.After(v.ExpiresAt) || !nativeAttestationRefPattern.MatchString(v.WitnessRef) || !nativeDigest(v.WitnessSHA256) || !nativeDigest(v.HostGenerationRef) || !nativeConnectionRef(v.ClientInstanceRef) || !nativeHostRef(v.HostInstanceID) || !clientIdentityLabel(v.OSSubjectRef) {
		return nil,Fail(403,"FORBIDDEN","Native create witness binding mismatch")
	}
	return &v,nil
}

func (s *ClientService) recordNativeCreateOrigin(ctx context.Context,tx *sql.Tx,env *Envelope,principal string,res *Response,v *VerifiedNativeCreateOrigin) error {
	if v==nil || deref(res.Status)!="COMPLETED" {return nil}
	if deref(env.Method)!="session.create" || env.SessionID!=nil || res.SessionID==nil || Str(res.Result,"session_id")!=*res.SessionID || !time.Now().Before(v.ExpiresAt) {return fmt.Errorf("NATIVE_ORIGIN_CREATE_RESULT")}
	var project,client string;var epoch int64
	if err:=tx.QueryRowContext(ctx,`SELECT project_id,writer_client_id,writer_epoch FROM client_sessions WHERE id=?`,*res.SessionID).Scan(&project,&client,&epoch);err!=nil{return err}
	if project!=deref(env.ProjectID) || client!=deref(env.ClientID) || epoch!=1 {return fmt.Errorf("NATIVE_ORIGIN_INITIAL_WRITER")}
	requestHash,err:=env.ContentHash();if err!=nil{return err}
	var headers,body string
	if err=tx.QueryRowContext(ctx,`SELECT headers,body FROM idempotency WHERE principal=? AND project=? AND operation='v2:session.create' AND key=? AND request_hash=?`,principal,project,deref(env.CommandID),requestHash).Scan(&headers,&body);err!=nil{return err}
	original,known,err:=readClientCommandEnvelope(s.Doc,headers)
	if err!=nil || !known || original.nativeOrigin!=nil || Digest(original.env.originalRaw)!=v.ActualRawSHA256 {return fmt.Errorf("NATIVE_ORIGIN_ORIGINAL_REQUEST")}
	b:=clientNativeWriterOriginBody{OriginSchema:nativeWriterOriginSchema,SchemaVersion:1,AttestationRef:v.WitnessRef,WitnessHash:v.WitnessSHA256,Principal:principal,AuthorityRoot:v.AuthorityRoot,CommandID:deref(env.CommandID),RequestHash:requestHash,RequestWireHash:v.ActualRawSHA256,ResponseHash:Digest([]byte(body)),Project:project,SessionID:*res.SessionID,WriterEpoch:1,WriterClientID:client,HostInstanceRef:v.HostInstanceID,HostGenerationRef:v.HostGenerationRef,ConnectionInstanceRef:v.ClientInstanceRef,OSSubjectRef:v.OSSubjectRef,CredentialHash:v.CredentialHash,AttestedAt:v.IssuedAt.UTC().Format(time.RFC3339Nano),AttestationExpiresAt:v.ExpiresAt.UTC().Format(time.RFC3339Nano),CreatedAt:time.Now().UTC().Format(time.RFC3339Nano)}
	row,err:=makeNativeOriginRow(b);if err!=nil{return err}
	if err=insertNativeOrigin(ctx,tx,row);err!=nil{return err}
	marked,err:=nativeOriginMarkedHeader(headers,nativeCreateOriginMarker{1,b.AttestationRef,b.WitnessHash,row.hash});if err!=nil{return err}
	result,err:=tx.ExecContext(ctx,`UPDATE idempotency SET headers=? WHERE principal=? AND project=? AND operation='v2:session.create' AND key=? AND request_hash=? AND headers=? AND body=?`,marked,principal,project,b.CommandID,b.RequestHash,headers,body)
	if err!=nil{return err};n,err:=result.RowsAffected();if err!=nil{return err};if n!=1{return fmt.Errorf("NATIVE_ORIGIN_MARKER_CAS")}
	return validateNativeOriginPair(ctx,tx,s.Doc,row)
}
