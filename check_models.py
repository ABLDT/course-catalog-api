from sqlalchemy import select, text

from db import Base, SessionLocal
from models import Course, Enrollment, Student


DB_NAMES = """
SELECT conname
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
  AND contype IN ('p', 'u', 'f', 'c')

UNION

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
"""


with SessionLocal() as db:
    for model in (Course, Student, Enrollment):
        rows = db.scalars(select(model)).all()
        print(f"{model.__tablename__}: {len(rows)} rows")

    in_db = {
        name
        for name in db.scalars(text(DB_NAMES))
        if not name.startswith("alembic")
    }


in_models = {
    constraint.name
    for table in Base.metadata.tables.values()
    for constraint in [*table.constraints, *table.indexes]
}


print("names only in models:", sorted(in_models - in_db) or "none")
print("names only in database:", sorted(in_db - in_models) or "none")