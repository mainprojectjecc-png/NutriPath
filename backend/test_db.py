from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    result = db.execute(text("SELECT 1"))
    print("Database session successful!")
    print("Test result:", result.scalar())

except Exception as error:
    print("Database session failed:")
    print(error)

finally:
    db.close()