# Course Catalog API

Backend API for the Course Catalog project built with FastAPI, SQLAlchemy 2.1, PostgreSQL, Pydantic, and Alembic.

The project was developed during Labs 4–7 of the Advanced Web Technologies course.

## How to run

### Requirements

You need:

- Python 3.11 or newer
- PostgreSQL 16 or newer

### 1. Create the PostgreSQL role and database

Run the following commands as the PostgreSQL `postgres` superuser:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';

CREATE DATABASE course_catalog
OWNER catalog_app;
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses:

- FastAPI
- SQLAlchemy
- psycopg
- Alembic
- pydantic-settings

### 4. Create the environment file

Copy `.env.example` to `.env`.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain:

```env
DATABASE_URL=postgresql+psycopg://catalog_app:change-me@localhost:5432/course_catalog
SQL_ECHO=true
```

The `.env` file is ignored by Git and must not be committed.

### 5. Apply database migrations

```bash
alembic upgrade head
```

On a clean database, Alembic applies both migrations:

```text
Running upgrade -> 0001, create catalog tables
Running upgrade 0001 -> 0002, add course level
```

### 6. Load initial data

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

If `psql` is not available in `PATH` on Windows:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

Expected output:

```text
TRUNCATE TABLE
INSERT 0 6
INSERT 0 3
INSERT 0 6
```

The database contains:

- 6 courses
- 3 students
- 6 enrollments

### 7. Check the schema

```bash
alembic check
```

Expected result:

```text
No new upgrade operations detected.
```

### 8. Start the FastAPI server

```bash
python -m fastapi dev main.py
```

or:

```bash
fastapi dev main.py
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 9. Test database error handling

Keep the server running and open another terminal.

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run:

```bash
python try_errors.py
```

Expected result:

```text
ok email already taken  409
ok already enrolled     409
ok unknown course       404
ok unknown student      404
ok name too short       422
5 of 5 as expected
```

---

## What changed in the API

The application now uses PostgreSQL as its persistent data storage instead of keeping data only in Python memory.

Because the data is stored in the database, restarting the FastAPI server does not remove courses, students, or enrollments.

### Courses

Courses are loaded from PostgreSQL using SQLAlchemy.

Example:

```text
GET /courses
```

Courses can be filtered by elective status:

```text
GET /courses?is_elective=true
```

They can also be filtered by level:

```text
GET /courses?level=beginner
```

Supported course levels in the initial data are:

```text
beginner
intermediate
```

Courses can also be sorted and paginated.

Example:

```text
GET /courses?sort=title&page=1&page_size=3
```

### Likes

Course likes are incremented directly in PostgreSQL using an atomic `UPDATE`.

Conceptually:

```sql
UPDATE courses
SET likes = likes + 1
WHERE id = ...;
```

This prevents a lost-update problem when several requests try to increment the same value.

### Students

Students are stored in the `students` table.

Example:

```text
POST /students
```

A student's name must contain at least two characters.

Student email addresses must be unique.

### Enrollments

Enrollments are stored in the `enrollments` table.

`POST /enrollments` now expects an existing `courseId` and `studentId`.

Example request:

```json
{
  "courseId": "modern-frontend",
  "studentId": 1
}
```

`GET /enrollments` returns enrollment information together with the related course title and student name.

### Course statistics

A statistics route was added:

```text
GET /stats/courses
```

It returns the number of enrolled students for every course.

Example result:

```json
[
  {
    "courseId": "ai-integration",
    "enrolled": 3
  },
  {
    "courseId": "modern-frontend",
    "enrolled": 2
  },
  {
    "courseId": "backend-fastapi",
    "enrolled": 1
  },
  {
    "courseId": "api-design",
    "enrolled": 0
  },
  {
    "courseId": "databases-postgresql",
    "enrolled": 0
  },
  {
    "courseId": "web-security",
    "enrolled": 0
  }
]
```

### Database errors

Database constraint violations are converted into meaningful HTTP responses.

Examples:

| Situation                                 | HTTP response              |
| ----------------------------------------- | -------------------------- |
| Student email already exists              | `409 Conflict`             |
| Student is already enrolled in the course | `409 Conflict`             |
| Course does not exist                     | `404 Not Found`            |
| Student does not exist                    | `404 Not Found`            |
| Student name is too short                 | `422 Unprocessable Entity` |

---

## Migrations

Alembic is used to manage the PostgreSQL schema.

| Command                                     | What it does                                                                  |
| ------------------------------------------- | ----------------------------------------------------------------------------- |
| `alembic upgrade head`                      | Applies all missing migrations                                                |
| `alembic downgrade -1`                      | Rolls back the latest migration                                               |
| `alembic current`                           | Shows the current database revision                                           |
| `alembic heads`                             | Shows the current migration head or heads                                     |
| `alembic history`                           | Shows the migration history                                                   |
| `alembic revision --autogenerate -m "text"` | Generates a migration draft from model/database differences                   |
| `alembic check`                             | Checks whether models and the database schema are different                   |
| `alembic upgrade 0001:0002 --sql`           | Prints migration SQL without executing it                                     |
| `alembic stamp head`                        | Marks a database as being at the latest revision without executing migrations |
| `alembic merge heads`                       | Creates a merge migration for multiple migration heads                        |

The real migration history of the project is:

```text
<base> -> 0001, create catalog tables
0001 -> 0002, add course level
```

The current migration head is:

```text
0002 (head)
```

### Migration 0001

Migration `0001` creates the main database tables:

- `courses`
- `students`
- `enrollments`

It also creates the required primary keys, foreign keys, unique constraints, check constraints, and indexes.

### Migration 0002

Migration `0002` adds the required `level` column to `courses`.

It uses three steps:

1. Add `level` as nullable.
2. Fill `level` for existing rows.
3. Change `level` to `NOT NULL`.

This was necessary because the table already contained data.

---

## Experiment log

| #   | Experiment                                                                           | What I saw                                                                                              | Cause                                                                                 | How I fixed it                                                                                                                            |
| --- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Changed the `uq` template in `naming_convention`                                     | `check_models.py` showed constraint names only in models and only in the database                       | SQLAlchemy generated unique constraint names that did not match PostgreSQL            | Restored `%(table_name)s_%(column_0_N_name)s_key`                                                                                         |
| 2   | Removed `min_length` from `StudentIn` and sent the name `N`                          | Pydantic accepted the request, but PostgreSQL rejected the row and the API returned an error            | API validation was removed while the database still had `students_name_check`         | Restored `Field(min_length=2)`                                                                                                            |
| 3   | Added a typo to a constraint name in `CONSTRAINT_ERRORS`                             | Duplicate email returned `500` instead of `409`                                                         | The dictionary key did not match the real PostgreSQL constraint name                  | Restored the correct `students_email_key` name                                                                                            |
| 4   | Removed `NOT NULL` from `courses.title` and later changed its type to `varchar(100)` | `alembic check` detected `modify_nullable`, then detected a type change from `VARCHAR(100)` to `Text()` | The real PostgreSQL schema had been manually changed and no longer matched the models | Restored `NOT NULL` and changed the type back to `text`                                                                                   |
| 5   | Used the automatically generated `0002` migration on a table with existing rows      | Migration failed with `NotNullViolation` because existing courses had no value for `level`              | Alembic generated a required column immediately                                       | Rewrote `0002` as three steps: nullable column, data update, then `NOT NULL`                                                              |
| 6   | Commented out `import models` in `alembic/env.py`                                    | Autogenerate detected `courses`, `students`, and `enrollments` as removed tables                        | Alembic could not see the application model metadata                                  | Restored `import models` and deleted the experimental migration                                                                           |
| 7   | Added `phone` to the `Student` model without a migration                             | `alembic check` reported `Detected added column 'students.phone'`                                       | The model contained a column that did not exist in PostgreSQL                         | Removed the temporary field; a real change would require a new migration                                                                  |
| 8   | Created migrations `0003` and `0004` from the same revision `0002`                   | `alembic heads` showed two heads and `alembic upgrade head` could not choose one                        | Two migration branches had the same parent                                            | Created merge revision `0005`, verified the merged history, then deleted all experimental migrations and returned to the real `0002` head |

---

## Decisions

### Why use PostgreSQL constraint names for API errors?

The application maps database errors using the PostgreSQL constraint name.

For example:

```text
students_email_key
```

and:

```text
enrollments_course_id_student_id_key
```

This is more precise than using only SQLSTATE.

SQLSTATE describes a general category of database error, while a constraint name identifies the exact database rule that was violated.

For example, several unique constraints can produce the same SQLSTATE, but their constraint names are different.

The application therefore knows whether the problem is a duplicate student email or a duplicate enrollment.

The application also catches the database error after `commit()` instead of performing a `SELECT` before every insert.

A pre-check such as:

```text
SELECT → if not found → INSERT
```

can cause a race condition.

Two requests could both perform the `SELECT` before either request performs the `INSERT`.

The database constraint is therefore used as the final source of truth.

### Why is a like incremented directly in the database?

The application uses an SQL update equivalent to:

```sql
UPDATE courses
SET likes = likes + 1
WHERE id = ...;
```

instead of:

```text
read likes
→ increase in Python
→ save new value
```

The database-side operation is atomic.

If two requests read the same old value before updating it, one increment could be lost.

Updating `likes = likes + 1` directly in PostgreSQL reduces this lost-update problem.

### Why does migration 0002 have three steps?

The `courses` table already contained data when the new required `level` column was introduced.

Adding this directly:

```sql
level TEXT NOT NULL
```

would fail because existing rows would initially contain `NULL`.

Migration `0002` therefore:

1. adds the column while allowing `NULL`;
2. fills the value for every existing row;
3. enables `NOT NULL`.

This allows the migration to work with an existing database without losing course data.

---

## Migration 0002 self-check

| What to check     | Result                                                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Goal and steps    | **Yes.** The goal is clear: add one required `level` field. The migration is split into three controlled steps.              |
| Data              | **Yes.** Existing rows are handled before `NOT NULL` is enabled. No existing course is left without a level.                 |
| Renames and drops | **Yes.** The upgrade does not rename or delete existing columns. The downgrade removes only the new `level` column.          |
| Rollback          | **Yes.** `alembic downgrade -1` successfully removed the column. `alembic upgrade head` recreated it successfully.           |
| Verification      | **Yes.** The SQL was reviewed with `--sql`. The upgrade → downgrade → upgrade cycle was tested and `alembic check` is clean. |
| History           | **Yes.** `alembic heads` shows only `0002 (head)`. The temporary experiment revisions were deleted.                          |
| Application       | **Yes.** The SQLAlchemy model, Pydantic schema, API filtering, and `seed.sql` were updated for the new `level` field.        |

---

## Clean-start verification

The project was tested from an empty database.

The original `course_catalog` database was deleted and recreated:

```sql
DROP DATABASE course_catalog WITH (FORCE);

CREATE DATABASE course_catalog
OWNER catalog_app;
```

The schema was then created only from Alembic migrations:

```bash
alembic upgrade head
```

Result:

```text
Running upgrade -> 0001, create catalog tables
Running upgrade 0001 -> 0002, add course level
```

Initial data was loaded with `seed.sql`.

The final data counts were:

```text
courses: 6
students: 3
enrollments: 6
```

Schema verification:

```bash
alembic check
```

Result:

```text
No new upgrade operations detected.
```

The API error test returned:

```text
5 of 5 as expected
```

The course statistics route returned:

```json
[
  { "courseId": "ai-integration", "enrolled": 3 },
  { "courseId": "modern-frontend", "enrolled": 2 },
  { "courseId": "backend-fastapi", "enrolled": 1 },
  { "courseId": "api-design", "enrolled": 0 },
  { "courseId": "databases-postgresql", "enrolled": 0 },
  { "courseId": "web-security", "enrolled": 0 }
]
```

This confirms that a new developer can recreate the database schema and initial data without manually creating the application tables.

---

## Previous API and CORS verification

During previous labs, the following API behavior was also verified:

- `GET /` returns the server status.
- `GET /courses` returns six courses.
- `GET /courses/web-security` returns the Web Security course.
- an unknown course returns `404`.
- elective and required courses can be filtered.
- courses can be sorted.
- pagination works.

### CORS experiment 1: middleware removed

The `CORSMiddleware` configuration was temporarily removed.

The browser reported that the `Access-Control-Allow-Origin` header was missing.

The enrollment preflight request failed, so the browser did not send the POST request.

The middleware was restored.

### CORS experiment 2: trailing slash in the allowed origin

The allowed origin was changed from:

```text
http://localhost:3000
```

to:

```text
http://localhost:3000/
```

The browser rejected the response because origins must match exactly.

The correct origin without the trailing slash was restored.

### CORS experiment 3: POST method not allowed

`allow_methods=["*"]` was temporarily removed.

GET requests continued working, but the enrollment preflight request failed because POST was not allowed.

The original CORS method configuration was restored.

### CORS experiment 4: different frontend origin

The frontend was opened using:

```text
http://127.0.0.1:3000
```

while the backend allowed:

```text
http://localhost:3000
```

These are different origins.

The browser therefore blocked the cross-origin request.

### CORS experiment 5: Python error that looked like CORS

The pagination key:

```python
p["offset"]
```

was intentionally changed to:

```python
p["ofset"]
```

The backend returned:

```text
500 Internal Server Error
```

with:

```text
KeyError: 'ofset'
```

The browser failure could initially look like a CORS problem, but the FastAPI terminal traceback showed that the real cause was a Python error.

The correct dictionary key was restored.
