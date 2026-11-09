package domain

import (
    "context"
    "database/sql"
    "path/filepath"
    "strings"

    "researchos.local/research-os/internal/recoveryauthority"
)

const historicalPreparedAbandonmentSchema = "researchos.prepared-run-abandonment.historical-adoption.v1"

type nativePreparedAbandonmentAuthority struct {
    token recoveryauthority.Token
    root, database, proof string
}
func (a *nativePreparedAbandonmentAuthority) verifyPreparedRunAbandonment(ctx context.Context,e PreparedRunAbandonmentEvidence) error {
    if ctx.Err()!=nil { return ctx.Err() }
    if Digest(Bytes(e))!=a.proof { return Fail(403,"FORBIDDEN","native abandonment proof differs") }
    return a.token.Check(a.root,a.database,a.proof)
}
func validateHistoricalPreparedAbandonment(e PreparedRunAbandonmentEvidence) error {
    a:=e.HistoricalAdoption
    if a==nil || e.Schema!=historicalPreparedAbandonmentSchema || e.Outcome!=preparedAbandonmentOutcome || e.ParentJobClosedUTC!="" || e.RootWitnessSignature!="" || e.ProviderRequests!=nil || e.ActualCost!=nil || e.FinancialClosed { return Fail(422,"GATE_FAILED","historical adoption must retain absent old signature and exact close time") }
    if err:=recoveryauthority.ValidateAdoption(*a); err!=nil { return err }
    t:=a.Tuple
    if e.ProjectID!=t.ProjectID || e.TaskID!=t.TaskID || e.RunID!=t.RunID || e.RuntimeID!=t.RuntimeID || e.OwnerRoot!=t.OwnerRoot || e.Epoch!=t.Epoch || e.RunRevision!=t.RunRevision || e.TaskRevision!=t.TaskRevision || e.DispatchKey!=t.DispatchKey || e.ManifestHash!=t.ManifestHash || e.ParentJobID!=a.Historical.HostJobID || !e.ParentJobTerminal || e.RootStartedUTC!=a.RootStartedUTC || e.RootClockExpiredUTC!=a.RootClockExpiredUTC || e.RootWitnessSHA256!=Digest(Bytes(a)) { return Fail(422,"GATE_FAILED","historical adoption tuple differs") }
    pins:=map[string]string{}; for _,p:=range a.Pins { pins[p.Role]=p.SHA256 }
    if e.HostJobContractSHA256!=pins["contract"] || e.HostJobProbeSHA256!=pins["probe"] || e.GOAuthoritySHA256!=pins["go"] { return Fail(422,"GATE_FAILED","historical raw pins differ") }
    return nil
}
func historicalPreparedEvidence(a recoveryauthority.Adoption) PreparedRunAbandonmentEvidence {
    t:=a.Tuple; pins:=map[string]string{}; for _,p:=range a.Pins { pins[p.Role]=p.SHA256 }
    return PreparedRunAbandonmentEvidence{HistoricalAdoption:&a,Schema:historicalPreparedAbandonmentSchema,Outcome:preparedAbandonmentOutcome,ProjectID:t.ProjectID,TaskID:t.TaskID,RunID:t.RunID,RuntimeID:t.RuntimeID,OwnerRoot:t.OwnerRoot,Epoch:t.Epoch,RunRevision:t.RunRevision,TaskRevision:t.TaskRevision,DispatchKey:t.DispatchKey,ManifestHash:t.ManifestHash,RootStartedUTC:a.RootStartedUTC,RootClockExpiredUTC:a.RootClockExpiredUTC,ParentJobID:a.Historical.HostJobID,ParentJobTerminal:true,HostJobContractSHA256:pins["contract"],HostJobProbeSHA256:pins["probe"],GOAuthoritySHA256:pins["go"],RootWitnessSHA256:Digest(Bytes(a))}
}

// The only production factory is private and concrete. New/NewCurrentMu and
// ordinary startup remain nil. No caller-selected interface/callback is stored.
func newNativePreparedAbandonmentService(ctx context.Context,db *sql.DB,contractsDir string,token recoveryauthority.Token) (*Service,PreparedRunAbandonmentEvidence,error) {
    var evidence PreparedRunAbandonmentEvidence
    a,err:=token.Adoption(); if err!=nil { return nil,evidence,err }
    evidence=historicalPreparedEvidence(a)
    if err=validatePreparedAbandonmentEvidence(evidence); err!=nil { return nil,evidence,err }
    rows,err:=db.QueryContext(ctx,"PRAGMA database_list"); if err!=nil { return nil,evidence,err }
    found:=false
    for rows.Next() { var seq int; var name,path string; if err=rows.Scan(&seq,&name,&path); err!=nil { rows.Close(); return nil,evidence,err }; if name=="main" { found=strings.EqualFold(filepath.Clean(path),filepath.Clean(a.Database)) } else if name!="temp" { rows.Close(); return nil,evidence,Fail(409,"STATE_CONFLICT","attached database forbidden during recovery") } }
    if err=rows.Err(); err!=nil { rows.Close(); return nil,evidence,err }; rows.Close()
    if !found { return nil,evidence,Fail(409,"STATE_CONFLICT","service database differs from native authority") }
    var version int; if err=db.QueryRowContext(ctx,"SELECT max(version) FROM schema_migrations").Scan(&version); err!=nil || version!=24 { return nil,evidence,Fail(409,"STATE_CONFLICT","separately accepted schema24 required; maintenance does not migrate") }
    var locking string; if err=db.QueryRowContext(ctx,"PRAGMA locking_mode").Scan(&locking); err!=nil || strings.ToLower(locking)!="exclusive" { return nil,evidence,Fail(409,"STATE_CONFLICT","maintenance exclusive SQLite connection required") }
    proof:=Digest(Bytes(evidence))
    if err=token.Check(a.Root,a.Database,proof); err!=nil { return nil,evidence,err }
    contracts,err:=LoadContracts(contractsDir); if err!=nil { return nil,evidence,err }
    service:=&Service{DB:db,Contracts:contracts,projectBindingRoute:"MU_FORK",preparedAbandonmentAuthority:&nativePreparedAbandonmentAuthority{token:token,root:a.Root,database:a.Database,proof:proof}}
    return service,evidence,nil
}

// ExecutePreparedAbandonmentMaintenance consumes only an opaque native token.
// It never returns an installed Service and exposes no authority setter.
func ExecutePreparedAbandonmentMaintenance(ctx context.Context,db *sql.DB,contractsDir string,token recoveryauthority.Token,ownerToken string) (Object,error) {
    service,evidence,err:=newNativePreparedAbandonmentService(ctx,db,contractsDir,token); if err!=nil { return nil,err }
    proof:=Digest(Bytes(evidence)); if err=token.Begin(proof); err!=nil { return nil,err }
    committed:=false; defer func(){ service.preparedAbandonmentAuthority=nil; token.Finish(committed) }()
    result,err:=service.AbandonPreparedQualification(ctx,ownerToken,evidence)
    committed=err==nil
    return result,err
}

