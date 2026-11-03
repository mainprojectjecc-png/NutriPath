Coach Workflow Test Plan

Module: Health Coach (Member 4) Location: tests/coach_workflow_tests/coach_flow.md Goal: Verify the full flow: user request -> coach suggestion -> user accepts or rejects.

Before you start
Backend running: uvicorn app.main:app --reload (http://localhost:8000/docs)
Frontend running: npm run dev inside frontend/
A test user account exists (use sample data only, never real user data)
A coach account or coach view is available
Status reference
Status	Meaning
pending	User submitted a request, coach has not responded
suggested	Coach has sent a replacement suggestion
accepted	User accepted the suggestion
rejected	User rejected the suggestion
Test cases
TC1: Submit a food change request

Steps

Log in as the test user.
Open the Health Coach page.
Submit a request to replace a food (example: "White rice", reason: "Too many carbs").

Expected

A success message appears.
The request shows in the user's list with status pending.

Result: [ ] Pass [ ] Fail Notes:

TC2: Coach sees the pending request

Steps

Open the coach view.
Look at the list of requests.

Expected

The request from TC1 appears with status pending.
Food name and reason are shown correctly.

Result: [ ] Pass [ ] Fail Notes:

TC3: Coach sends a suggestion

Steps

Click the pending request.
Enter a replacement (example: "Brown rice").
Click Send suggestion.

Expected

A confirmation message appears.
Status changes from pending to suggested.
The suggestion text is saved on the request.

Result: [ ] Pass [ ] Fail Notes:

TC4: User accepts the suggestion

Steps

Log in as the user.
Open the request with status suggested.
Click Accept.

Expected

Status changes to accepted.
A notification or message confirms it.
The coach view also shows accepted.

Result: [ ] Pass [ ] Fail Notes:

TC5: User rejects the suggestion

Steps

Submit a new request and have the coach suggest a replacement.
As the user, click Reject.

Expected

Status changes to rejected.
The coach view also shows rejected.

Result: [ ] Pass [ ] Fail Notes:

TC6: Empty suggestion is blocked

Steps

As the coach, open a pending request.
Leave the suggestion box empty and click Send suggestion.

Expected

The suggestion is not sent, or a clear error message is shown.
Status stays pending.

Result: [ ] Pass [ ] Fail Notes:

TC7: Status cannot jump backwards

Steps

Open a request that is already accepted.
Try to send another suggestion or accept again.

Expected

The action is blocked or ignored.
Status stays accepted.

Result: [ ] Pass [ ] Fail Notes:

TC8: Loading and error states

Steps

Stop the backend.
Reload the Health Coach page.

Expected

The page does not crash.
A clear error message is shown.
After restarting the backend, the data loads again.

Result: [ ] Pass [ ] Fail Notes:

TC9: Data persists after refresh

Steps

Complete TC3.
Refresh the browser.

Expected

The request still shows status suggested with its suggestion text.

Result: [ ] Pass [ ] Fail Notes:

API checks (Swagger UI at /docs)
Endpoint	Method	Check
/api/v1/food-change-requests	POST	Returns the new request with status pending
/api/v1/coach/requests	GET	Lists requests for the coach
/api/v1/coach/requests/{id}/suggestion	POST	Status becomes suggested
/api/v1/food-change-requests/{id}/accept	POST	Status becomes accepted
Bug log
#	Test case	What happened	Severity	Fixed?
1				
Sign-off
Tester: ______________
Date: ______________
Overall result: [ ] All passed [ ] Issues found