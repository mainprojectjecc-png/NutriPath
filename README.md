# NutriPath

NutriPath is a personalized nutrition and weight-journey application. User accounts,
profiles, goals, weight entries, and achievements are stored in the FastAPI/SQLite
backend. Meal and water entries and nutrition goals are also stored in the
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
available at `http://localhost:8000/docs`. SQLite data is written to
`backend/nutripath.db`. Set `NUTRIPATH_DATABASE_URL` to use another SQLAlchemy
database URL. Set a persistent, private `NUTRIPATH_SECRET_KEY` before production
deployment and set `NUTRIPATH_ENVIRONMENT=production`.

Password reset requires an SMTP service. Configure `NUTRIPATH_SMTP_HOST`,
`NUTRIPATH_SMTP_PORT`, `NUTRIPATH_SMTP_FROM`, and optionally
`NUTRIPATH_SMTP_USERNAME` / `NUTRIPATH_SMTP_PASSWORD`. Set
`NUTRIPATH_FRONTEND_URL` to the deployed frontend URL. Without SMTP, password
reset requests return an explicit configuration error.

### Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

The frontend uses `http://localhost:8000` by default. Override this with
`VITE_API_URL` when the API is hosted elsewhere.

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
