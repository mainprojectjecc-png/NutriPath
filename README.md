# NutriPath

NutriPath is a personalized nutrition and weight-journey application. User accounts,
profiles, goals, weight entries, and achievements are stored in the FastAPI backend.
Meal and water entries and nutrition goals are also stored in the
authenticated user's database records. Existing browser-based meal logs are
migrated into the database on the next authenticated visit.

## Run locally

Use two PowerShell terminals from the repository root.

### Backend

```powershell
Set-Location backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:NUTRIPATH_SECRET_KEY = py -c "import secrets; print(secrets.token_urlsafe(48))"
py -m uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`; interactive API documentation is
available at `http://localhost:8000/docs`. By default, the backend connects to
the existing local SQL Server `NutriPathDB` using ODBC Driver 18 and Windows
trusted authentication. Set `NUTRIPATH_DATABASE_URL` to use another SQLAlchemy
database URL, such as `sqlite:///./nutripath.db` for local development.

The legacy `GET /api/v1/users/` route is a hard-coded placeholder that returns
no users and is not used by the frontend. It must not be used to discover or
verify QA accounts.

Application startup does not create or alter database tables. The SQL Server
database must be provisioned with the legacy API tables and the journey and
nutrition tables/profile columns modeled by the application before using those
routes. No real database schema or records are changed by the integration or its
tests; the API tests use an isolated in-memory SQLite database.
Set a persistent, private `NUTRIPATH_SECRET_KEY` before production deployment
and set `NUTRIPATH_ENVIRONMENT=production`.

Password reset requires an SMTP service. Configure `NUTRIPATH_SMTP_HOST`,
`NUTRIPATH_SMTP_PORT`, `NUTRIPATH_SMTP_FROM`, and optionally
`NUTRIPATH_SMTP_USERNAME` / `NUTRIPATH_SMTP_PASSWORD`. Set
`NUTRIPATH_FRONTEND_URL` to the deployed frontend URL. Without SMTP, password
reset requests return an explicit configuration error.

### Optional QA account provisioning

The private provisioning utility can create one missing User QA account and one
missing Coach QA account. It is not an API endpoint and it never changes the
role, password, or other data of an existing account. Do not run it against
production. Creating accounts writes to the configured database and requires
explicit approval before execution.

After approval, use the guarded QA launcher configuration. The provisioner
independently requires SQL Server `IMENE` and database `sampledb` before
creating accounts; if `NUTRIPATH_DATABASE_URL` is unset, it selects the
verified local ODBC Driver 18 `lpc:IMENE` connection to `sampledb`. It refuses
SQLite and any other explicitly configured SQL Server/database target. In
PowerShell, configure the QA environment and account identities, and set the
confirmation variable only when ready to create missing accounts:

```powershell
Set-Location backend
$env:NUTRIPATH_ENVIRONMENT = "qa"
$env:NUTRIPATH_QA_USER_EMAIL = "your-dedicated-user-qa-email"
$env:NUTRIPATH_QA_USER_FULL_NAME = "NutriPath QA User"
$env:NUTRIPATH_QA_COACH_EMAIL = "your-dedicated-coach-qa-email"
$env:NUTRIPATH_QA_COACH_FULL_NAME = "NutriPath QA Coach"
$env:NUTRIPATH_ENABLE_QA_ACCOUNT_PROVISIONING = "I_CONFIRM_QA_ACCOUNT_CREATION"
py .\scripts\provision_qa_accounts.py
```

The utility prompts for each password without echoing it. Alternatively, set
`NUTRIPATH_QA_USER_PASSWORD` and `NUTRIPATH_QA_COACH_PASSWORD` through a
credential-safe environment mechanism. It reports only whether each role was
created or an existing account was left unchanged; it does not display
credentials or hashes. The explicit confirmation variable should be removed
after use.

### Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

The frontend uses `http://localhost:8000` by default. Override this with
`VITE_API_URL` when the API is hosted elsewhere.

### SQL Server QA environment

Use the dedicated launcher to run a separate QA API on `127.0.0.1:8001`.
It pins the connection to the local SQL Server instance on `IMENE` using the
ODBC Driver 18 Shared Memory protocol (`lpc:`) and `sampledb`, then checks the
connected server and database before starting. It also permits the QA frontend
origin `http://127.0.0.1:5174`. If the check fails, the API does not start. Do
not redirect this QA server to another database.

```powershell
Set-Location backend
.\scripts\start_qa.ps1
```

To run only the read-only connection preflight without starting the API:

```powershell
.\scripts\start_qa.ps1 -PreflightOnly
```

Immediately before every API operation that creates, updates, or deletes data,
verify the running QA API still reports the expected database:

```powershell
$qaDatabase = Invoke-RestMethod "http://127.0.0.1:8001/db-check"
if ($qaDatabase.database -cne "sampledb") {
    throw "ABORT: QA API is not connected to sampledb."
}
```

Use only `127.0.0.1:8001` for QA writes; the regular API on port `8000` uses
the normal development configuration.

In a separate terminal, point the QA frontend at that API and use a separate
Vite port:

```powershell
Set-Location frontend
$env:VITE_API_URL = "http://127.0.0.1:8001"
npm run dev -- --host 127.0.0.1 --port 5174
```

The regular backend tests use isolated in-memory SQLite. They do not connect to
this SQL Server QA environment or verify SQL Server behavior.

## Tests

From the repository root, run the API integration tests against an isolated
in-memory SQLite database:

```powershell
py -m unittest discover -s tests -p test_journey_api.py -v
```

Build the frontend with `Set-Location frontend; npm run build`.

## Health data notes

Weight goals and target dates are estimates, not guaranteed outcomes. BMI is
provided only as a screening indicator, not a diagnosis. The current nutrition
insights are rule-based observations of logged data, not medical advice or an
AI-generated diagnosis.
