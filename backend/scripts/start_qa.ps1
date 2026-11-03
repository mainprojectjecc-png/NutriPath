param(
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$env:NUTRIPATH_ENVIRONMENT = "qa"
$env:NUTRIPATH_CORS_ORIGINS = "http://127.0.0.1:5174"
$odbcConnectionString = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:IMENE;DATABASE=sampledb;Trusted_Connection=yes;TrustServerCertificate=yes"
$encodedConnectionString = [uri]::EscapeDataString($odbcConnectionString)
$env:NUTRIPATH_DATABASE_URL = "mssql+pyodbc:///?odbc_connect=$encodedConnectionString"

$backendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Backend virtual environment not found at $python"
}

Set-Location $backendRoot
$preflight = @'
from sqlalchemy import text
from app.database import engine
import pyodbc

required_driver = "ODBC Driver 18 for SQL Server"
if required_driver not in pyodbc.drivers():
    raise SystemExit(f"ABORT: required ODBC driver is not installed: {required_driver}")

with engine.connect() as connection:
    database_name, server_name = connection.execute(
        text("SELECT DB_NAME(), CAST(SERVERPROPERTY('ServerName') AS nvarchar(128))")
    ).one()

print(f"SQL Server preflight: server={server_name}, database={database_name}")
if database_name != "sampledb" or str(server_name).casefold() != "imene":
    raise SystemExit("ABORT: expected SQL Server IMENE and database sampledb.")
'@

$preflight | & $python -
if ($LASTEXITCODE -ne 0) {
    throw "QA database preflight failed. The API was not started."
}

if ($PreflightOnly) {
    exit 0
}

& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
exit $LASTEXITCODE
