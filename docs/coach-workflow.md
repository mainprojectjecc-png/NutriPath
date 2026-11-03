Health Coach Workflow

Module: Health Coach (Member 4) Location: docs/coach-workflow.md

Purpose

Lets a user ask for a food to be replaced, lets the health coach review the request and suggest an alternative, and lets the user accept or reject that suggestion.

The flow
User submits request  ->  Coach reviews  ->  Coach suggests  ->  User accepts or rejects
      (pending)                                 (suggested)        (accepted / rejected)
User submits a request. The user picks a food they want replaced and gives a reason. Status: pending.
Coach reviews. The coach sees all pending requests in a list and opens one to read the food and reason.
Coach suggests. The coach types a replacement food and sends it. Status: suggested.
User decides. The user accepts or rejects the suggestion. Status: accepted or rejected.
Statuses
Status	Set by	Meaning	Next possible status
pending	System, on user submit	Waiting for the coach	suggested
suggested	Coach	Coach proposed a replacement	accepted, rejected
accepted	User	User approved the suggestion	None (final)
rejected	User	User declined the suggestion	None (final)

Status colours in the UI:

pending: orange
suggested: blue
accepted: green
rejected: red
API endpoints
Endpoint	Method	Purpose	Owner
/api/v1/food-change-requests	POST	User submits a request	Member 2 + Member 4
/api/v1/coach/requests	GET	Coach views requests	Member 2 + Member 4
/api/v1/coach/requests/{id}/suggestion	POST	Coach sends a suggestion	Member 2 + Member 4
/api/v1/food-change-requests/{id}/accept	POST	User accepts a suggestion	Member 2 + Member 4
Example request object
json
{
  "id": 1,
  "userName": "Anita",
  "foodToReplace": "White rice",
  "reason": "Too many carbs",
  "status": "pending",
  "suggestion": null
}
Example suggestion request
json
POST /api/v1/coach/requests/1/suggestion
{
  "suggestion": "Brown rice"
}
Example response
json
{
  "id": 1,
  "status": "suggested",
  "suggestion": "Brown rice"
}
Frontend files
File	Purpose
frontend/src/pages/HealthCoach.jsx	Main Health Coach page, connected to services/nutrition
frontend/src/pages/coach/CoachDashboard.jsx	Mock coach dashboard (Day 1 prototype)
frontend/src/components/coach/RequestList.jsx	List of requests with status badges
frontend/src/components/coach/SuggestionForm.jsx	Form the coach uses to send a suggestion
frontend/src/components/coach/RequestStatusBadge.jsx	Coloured status label
frontend/src/mock/coachMockData.js	Sample requests used while the backend was not ready
Rules
Only the coach can move a request from pending to suggested.
Only the user can move a request from suggested to accepted or rejected.
accepted and rejected are final. A new request is needed to change the outcome.
A suggestion cannot be empty.
Use sample data only. Do not store real user data or sensitive health information in the repository.
Coach suggestions are general food alternatives, not medical advice. Weight progress figures are estimates, not promises.
Testing

See tests/coach_workflow_tests/coach_flow.md for the full test plan and checklist.

Known notes
HealthCoach.jsx already handles the real workflow through services/nutrition (create request, get requests, submit suggestion, accept, reject).
The mock components in components/coach were built as a Day 1 prototype and may be merged into, or replaced by, the real page after team review