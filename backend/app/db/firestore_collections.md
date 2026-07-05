# Firestore Collections (real-time operational state)

Firestore holds the *live* state the dashboard subscribes to; BigQuery holds
history; AlloyDB holds the transactional system of record.

| Collection | Written by | Purpose | Key fields |
|---|---|---|---|
| `incidents` | Voice/Vision agents, API | Live incident board | type, severity, status, lat/lng, source, transcript |
| `decisions` | Decision Agent | Fused decisions with reasoning | risk_score, confidence, priority, reasoning, action_plan, estimated_impact |
| `decision_cycles` | Orchestrator | One doc per 5-min cycle | risk_score, priority, summary |
| `agent_runs` | BaseAgent.execute | Full agent audit trail | agent, status, risk_score, confidence, duration_ms |
| `notifications` | Notification service | Outbound alert audit | channel, recipient, subject, incident_id, status |
| `work_orders` | Workflow Agent | Dispatched work | type, priority, actions, status, incident_id |
| `incident_reports` | Workflow Agent | Auto-generated reports | incident_id, risk_score, reasoning, actions_taken |
| `chat_history` | Chat route | Conversation log | user, message, mode, answer |

## Security rules sketch

```
service cloud.firestore {
  match /databases/{db}/documents {
    match /incidents/{id}    { allow read: if request.auth != null;
                               allow write: if request.auth.token.role in ['responder','commander','admin']; }
    match /decisions/{id}    { allow read: if request.auth.token.role != 'citizen'; allow write: if false; }
    match /agent_runs/{id}   { allow read: if request.auth.token.role == 'admin'; allow write: if false; }
    match /notifications/{id}{ allow read: if request.auth.token.role == 'admin'; allow write: if false; }
  }
}
```
(Server writes go through the Admin SDK on Cloud Run and bypass rules.)
