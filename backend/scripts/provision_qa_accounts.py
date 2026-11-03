import getpass
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


def _verified_qa_target(db):
    bind = db.get_bind()
    if bind.dialect.name != "mssql":
        return None
    server, database = db.execute(
        text("SELECT CAST(SERVERPROPERTY('ServerName') AS nvarchar(128)), DB_NAME()")
    ).one()
    if str(server).casefold() != "imene" or database != "sampledb":
        return None
    return server, database


def _configure_qa_database_url() -> None:
    if os.getenv("NUTRIPATH_DATABASE_URL"):
        return
    odbc_connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=lpc:IMENE;"
        "DATABASE=sampledb;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes"
    )
    os.environ["NUTRIPATH_DATABASE_URL"] = (
        "mssql+pyodbc:///?odbc_connect="
        + quote_plus(odbc_connection_string)
    )


def _configured_account(prefix: str, role: str):
    from app.services.qa_accounts import QAAccount

    required = {
        "email": os.getenv(f"NUTRIPATH_QA_{prefix}_EMAIL"),
        "full_name": os.getenv(f"NUTRIPATH_QA_{prefix}_FULL_NAME"),
    }
    if any(not value for value in required.values()):
        raise ValueError(f"Missing required {role} QA account configuration.")
    password = os.getenv(f"NUTRIPATH_QA_{prefix}_PASSWORD")
    if not password:
        password = getpass.getpass(f"Password for the new {role} QA account: ")
    return QAAccount(
        email=required["email"],
        full_name=required["full_name"],
        password=password,
        role=role,
    )


def main() -> int:
    environment = os.getenv("NUTRIPATH_ENVIRONMENT", "").strip().casefold()
    if environment not in {"development", "qa"}:
        print("Refusing to provision accounts outside development or QA.")
        return 2
    if os.getenv("NUTRIPATH_ENABLE_QA_ACCOUNT_PROVISIONING") != "I_CONFIRM_QA_ACCOUNT_CREATION":
        print("Set the explicit QA account provisioning confirmation to proceed.")
        return 2

    _configure_qa_database_url()
    from app.database import SessionLocal
    from app.services.qa_accounts import provision_qa_accounts

    db = SessionLocal()
    try:
        target = _verified_qa_target(db)
        if target is None:
            print("Refusing to provision accounts outside SQL Server IMENE/sampledb.")
            return 2
        print(f"Verified QA database: server={target[0]}, database={target[1]}")

        try:
            accounts = [
                _configured_account("USER", "User"),
                _configured_account("COACH", "Coach"),
            ]
        except ValueError as error:
            print(error)
            return 2

        outcomes = provision_qa_accounts(db, accounts)
    finally:
        db.close()

    for outcome in outcomes:
        print(outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
