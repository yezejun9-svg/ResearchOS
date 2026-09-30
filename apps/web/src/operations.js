// Paths and methods from spec/v2.0/contracts/openapi.json.
export const operations = {
  "sealArtifact": { "method": "POST", "path": "/v1/projects/{project_id}/artifacts" },
  "listProjects": {
    "method": "GET",
    "path": "/v1/projects"
  },
  "createProject": {
    "method": "POST",
    "path": "/v1/projects"
  },
  "getProjectProfile": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/profile"
  },
  "getProjectState": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/state"
  },
  "listRequirement": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/requirements"
  },
  "createRequirement": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/requirements"
  },
  "listGoal": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/goals"
  },
  "createGoal": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/goals"
  },
  "getGoal": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/goals/{object_id}"
  },
  "listTask": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/tasks"
  },
  "getTask": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/tasks/{object_id}"
  },
  "listRun": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/runs"
  },
  "getRun": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/runs/{object_id}"
  },
  "listArtifact": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/artifacts"
  },
  "sealArtifact": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/artifacts"
  },
  "getArtifact": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/artifacts/{object_id}"
  },
  "listEvidence": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/evidence"
  },
  "getEvidence": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/evidence/{object_id}"
  },
  "listResearchCycle": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/research-cycles"
  },
  "getResearchCycle": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/research-cycles/{object_id}"
  },
  "listExperiment": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/experiments"
  },
  "getExperiment": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/experiments/{object_id}"
  },
  "listDecisionReceipt": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/decisions"
  },
  "getDecisionReceipt": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/decisions/{object_id}"
  },
  "listQualification": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/qualifications"
  },
  "getQualification": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/qualifications/{object_id}"
  },
  "createChangeProposal": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/change-proposals"
  },
  "listResourceRequest": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/resource-requests"
  },
  "getResourceRequest": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/resource-requests/{object_id}"
  },
  "listMilestoneRelease": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/releases"
  },
  "getMilestoneRelease": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/releases/{object_id}"
  },
  "listSkillVersion": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/skills"
  },
  "getSkillVersion": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/skills/{object_id}"
  },
  "getAcceptanceReceipt": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/acceptances/{object_id}"
  },
  "listAgentMessage": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/messages"
  },
  "listSourceCursor": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/source-cursors"
  },
  "getSourceCursor": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/source-cursors/{object_id}"
  },
  "listBudgetLedgerEntry": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/budget-ledger"
  },
  "getBudgetLedgerEntry": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/budget-ledger/{object_id}"
  },
  "listRuntimeRegistration": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/runtimes"
  },
  "getRuntimeRegistration": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/runtimes/{object_id}"
  },
  "listNotification": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/notifications"
  },
  "actOnRequirement": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/requirements/{object_id}/actions"
  },
  "actOnTask": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/tasks/{object_id}/actions"
  },
  "cancelRun": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/runs/{object_id}/cancel"
  },
  "uploadContent": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/content"
  },
  "getArtifactContent": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/artifacts/{object_id}/content"
  },
  "applyChangeProposal": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/change-proposals/{object_id}/apply"
  },
  "getBudgetPolicy": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/budget-policy"
  },
  "updateBudgetPolicy": {
    "method": "PUT",
    "path": "/v1/projects/{project_id}/budget-policy"
  },
  "getRunPolicy": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/run-policy"
  },
  "updateRunPolicy": {
    "method": "PUT",
    "path": "/v1/projects/{project_id}/run-policy"
  },
  "resolveResourceRequest": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/resource-requests/{object_id}/resolve"
  },
  "getProgressProjection": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/progress"
  },
  "promoteSkill": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/skills/{object_id}/promote"
  },
  "markNotificationRead": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/notifications/{object_id}/read"
  },
  "searchEvidence": {
    "method": "POST",
    "path": "/v1/projects/{project_id}/search"
  },
  "listEvents": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/events"
  },
  "streamEvents": {
    "method": "GET",
    "path": "/v1/projects/{project_id}/events/stream"
  },
  "createDevicePairing": {
    "method": "POST",
    "path": "/v1/device-pairings"
  },
  "listDevices": {
    "method": "GET",
    "path": "/v1/devices"
  },
  "updateDeviceGrants": {
    "method": "PUT",
    "path": "/v1/devices/{device_id}/grants"
  },
  "revokeDevice": {
    "method": "POST",
    "path": "/v1/devices/{device_id}/revoke"
  }
}
