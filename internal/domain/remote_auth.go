package domain

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
)

var remoteOperations = map[string]bool{"createDevicePairing": true, "redeemDevicePairing": true, "refreshDeviceSession": true, "listDevices": true, "updateDeviceGrants": true, "revokeDevice": true}

func init() {
	for id := range remoteOperations {
		implemented[id] = true
	}
}

// Device grants are a live intersection with the issuing local owner's grants.
// A paired OWNER controls its explicit projects, never local administration,
// restricted artifacts, global policies, project creation, or other devices.
func constrainRemotePrincipal(tx *sql.Tx, p *Principal) error {
	var owner, body, roles string
	var revoked int
	e := tx.QueryRow("SELECT d.owner,d.body,p.roles,p.revoked FROM remote_devices d JOIN auth_principals p ON p.id=d.owner WHERE d.id=?", p.ID).Scan(&owner, &body, &roles, &revoked)
	if errors.Is(e, sql.ErrNoRows) {
		return nil
	}
	if e != nil {
		return e
	}
	var ownerRoles []string
	device, e := Decode([]byte(body))
	if e != nil {
		return e
	}
	if json.Unmarshal([]byte(roles), &ownerRoles) != nil || revoked != 0 || Str(device, "status") != "ACTIVE" || !(Principal{Roles: ownerRoles}).HasRole("OWNER") {
		return Fail(401, "UNAUTHENTICATED", "device or issuing owner is unavailable")
	}
	p.DeviceID = p.ID
	p.CanCreateProject = false
	p.Roles = []string{Str(device, "role")}
	grants := []Grant{}
	for _, g := range p.Grants {
		var count int
		if e = tx.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND task='' AND run=''", owner, g.ProjectID).Scan(&count); e != nil {
			return e
		}
		if count > 0 {
			g.Restricted = false
			grants = append(grants, g)
		}
	}
	p.Grants = grants
	return nil
}

func (s *Service) remoteOperationBoundary(w http.ResponseWriter, r *http.Request, op Operation) bool {
	// Dedicated credential-proof endpoints do their own authentication.
	if op.ID == "redeemDevicePairing" || op.ID == "refreshDeviceSession" {
		return true
	}
	token := r.Header.Get("Authorization")
	if len(token) < 8 || token[:7] != "Bearer " {
		return true
	}
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		s.writeError(w, ID(), e)
		return false
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token[7:])
	if e != nil {
		s.writeError(w, ID(), e)
		return false
	}
	if r.Header.Get("X-ResearchOS-Remote-Access") == "device" && p.DeviceID == "" {
		s.writeError(w, ID(), Fail(403, "FORBIDDEN", "paired device credential required at remote gateway"))
		return false
	}
	if p.DeviceID != "" && r.PathValue("project_id") == "" && op.ID != "listProjects" {
		s.writeError(w, ID(), Fail(403, "FORBIDDEN", "device is limited to its granted projects"))
		return false
	}
	return true
}
