# course-catalog-api

Backend of the course catalog: FastAPI, SQLAlchemy 2.1, PostgreSQL, Alembic and GraphQL on Strawberry as a second entrance (Labs 4–8, Advanced Web Technologies).

## How to run

You need Python 3.11+ and PostgreSQL 16+.

Create the role and database once as the `postgres` superuser:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

From the project folder on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
fastapi dev main.py
```

REST docs: `http://localhost:8000/docs`  
GraphiQL: `http://localhost:8000/graphql`

The password `change-me` is only for the training project. Real secrets must not be committed.

Useful checks while the server is running:

```powershell
python try_errors.py
python try_graphql.py
python try_n_plus_1.py
python try_protection.py
python flood_likes.py
python measure.py
```

Expected core results on the starting data:

```text
try_errors.py     -> 5 of 5 as expected
try_graphql.py    -> 8 of 8 as expected
try_n_plus_1.py   -> 3 SQL queries and 3 SQL queries
measure.py        -> REST: 5 requests, 2 rounds, 5 SQL queries
                     GraphQL: 1 request, 1 round, 3 SQL queries
```

The byte counts printed by `measure.py` must be copied from the actual local run because they depend on the exact response data.

## What changed in the API

- Application rules were moved to `services.py`. The services layer knows the database rules but does not know HTTP or GraphQL.
- REST translates `ServiceError` into RFC 9457 Problem Details in `problem.py`. Rule errors use `application/problem+json`, a stable `type`, HTTP status, title, detail and instance.
- GraphQL is available at `/graphql` alongside REST. GraphiQL is available through a browser while introspection is enabled.
- The GraphQL schema contains `Course`, `Student` and `Enrollment` types and the `courses`, `course`, `students`, `student` and `enrollments` queries.
- `enroll` and `likeCourse` mutations use the same services as REST. Expected rule failures are returned in `userErrors`; unexpected GraphQL execution failures remain in `errors`.
- Every HTTP response gets an `X-SQL-Queries` header. It is used to expose N+1 behavior and to verify the DataLoader optimization.
- DataLoaders are created per GraphQL request and batch relation loads by key. The nested queries use three SQL queries instead of a number that grows with the amount of data.
- GraphQL protection limits query depth to 5 and aliases to 10, validates `limit` and student IDs, masks unexpected internal exceptions, and controls introspection through `GRAPHQL_INTROSPECTION`.
- REST now also has `GET /students/{id}` and `GET /students/{id}/enrollments` for the REST version of the My courses page.

## Example queries

The My courses query (Variables: `{"id": "2"}`):

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments {
      id
      course {
        title
        credits
        level
      }
    }
  }
}
```

Successful enrollment mutation:

```graphql
mutation Enroll($input: EnrollInput!) {
  enroll(input: $input) {
    enrollment {
      id
      enrolledAt
      course { title }
    }
    userErrors { code message }
  }
}
```

Variables:

```json
{"input":{"courseId":"web-security","studentId":"3"}}
```

A repeated enrollment is an expected rule error and therefore remains inside `data`:

```json
{
  "data": {
    "enroll": {
      "enrollment": null,
      "userErrors": [
        {
          "code": "ALREADY_ENROLLED",
          "message": "Student is already enrolled in this course"
        }
      ]
    }
  }
}
```

## REST vs GraphQL comparison

The My courses screen of student 2, starting data.

| Criterion | REST | GraphQL | Source |
|---|---|---|---|
| Requests and rounds per screen | 5 requests, 2 rounds | 1 request, 1 round | `measure.py` |
| Bytes in the responses | 1116 bytes | 332 bytes | `measure.py` |
| SQL queries per screen | 5 | 3 | `measure.py`, `X-SQL-Queries` |
| SQL growth with more students | The REST page grows with the number of course requests | After DataLoaders the nested GraphQL checks stay at 3 SQL queries for both 3 and 20 students | `try_n_plus_1.py`, experiments 4–5 |
| Error in query text | REST usually uses HTTP 4xx/422 for route/parameter problems | Usually HTTP 200 with an `errors` key and possibly `data: null` | experiments 1 and 8 |
| Expected rule error | e.g. repeated enrollment -> `409 application/problem+json` | HTTP 200, `userErrors[0].code = ALREADY_ENROLLED` | steps 1 and 4 |
| HTTP cache | Natural fit for cacheable GET resources and standard HTTP cache semantics | Usually POST to one endpoint, so HTTP caching is less direct and often needs application/client tooling | lecture comparison |
| Protection from expensive queries | Cost is mostly fixed by each route implementation | Explicit depth, alias and argument limits are required because the client chooses query shape | experiments 6–7 |

**Conclusion.** For simple resource-oriented screens with a stable response shape, REST remains straightforward and works naturally with HTTP semantics. For My courses, GraphQL is a better fit because one request returns exactly the nested fields needed instead of five requests in two rounds. With DataLoaders, the GraphQL version also keeps the database work at three SQL queries. GraphQL flexibility requires additional query protections and careful client-side checking of the `errors` key.

## Experiment log

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | Typo `titel` and argument name in `snake_case` | HTTP status stayed 200, `data` was null, and `errors` contained `Cannot query field 'titel'...` / `Unknown argument 'is_elective'... Did you mean 'isElective'?` | GraphQL validates the query text against the schema before resolver execution, and Strawberry exposes camelCase names | Corrected `titel` to `title` and used `isElective` |
| 2 | Removed `| None` from `course` and queried a missing course | `Cannot return null for non-nullable field Query.course.`; with two aliases the error propagated and the whole `data` became null | The schema promised that `course` could never be null, but the resolver can return no row | Restored `CourseType | None` |
| 3 | Sent a mutation with GET | The read query over GET returned 200, but the mutation returned `400 Bad Request: mutations are not allowed when using GET` | GET is defined as safe; mutations change state and must not be executed through GET | Sent mutations through POST |
| 4 | Added 17 students and measured lazy-loaded nested queries | Starting data: 7 and 7 SQL queries. With 20 students: 27 and 24 | Lazy loading executes relation queries per parent object, so database work grows although the client still sends one POST | Replaced lazy relation loading with per-request DataLoaders |
| 5 | Replaced the batch function with a naive result list | One query failed loudly with `WrongNumberOfResultsReturned`; another returned the wrong course for several enrollments without an error | A DataLoader must return exactly one result slot per key and preserve key order. DB row order is not the key order | Grouped rows by key and rebuilt the result list in the original key order |
| 6 | Six dangerous queries before and after protection | Before: depth and aliases executed; DB/Value errors leaked. After: depth >5 and aliases >10 were rejected, bad limit/ID got safe messages, unexpected DB overflow became `Unexpected error.`; `flood_likes.py` used 0 SQL queries | Unprotected GraphQL lets the client choose expensive/deep query shapes and can expose internals | Added argument checks, `QueryDepthLimiter`, `MaxAliasesLimiter` and `MaskErrors` |
| 7 | Disabled introspection, then made a typo | `__schema` was rejected, ordinary queries still worked, and `Did you mean 'course' or 'courses'?` still exposed field hints | Disabling introspection hides the schema map but is not authorization and does not hide every field name | Restored `GRAPHQL_INTROSPECTION=true` for development; authorization must protect data, not schema secrecy |
| 8 | Frontend typo, removed GraphQL `errors` check, then stopped API | With the check: `GraphQLRequestError` named the bad field. Without it: only a null destructuring `TypeError` appeared. With API stopped: `fetch failed` | GraphQL application/query errors often use HTTP 200; network errors have no GraphQL body at all | `gql()` checks HTTP status and the GraphQL `errors` key and throws `GraphQLRequestError`; restored files after the experiment |

## Decisions

**Why are rules and their errors in `services.py` instead of being checked independently in REST and GraphQL?**  
The rule must have one source of truth. `services.py` produces a protocol-independent code such as `ALREADY_ENROLLED`; REST converts it to 409 Problem Details while GraphQL converts the same code to `userErrors`. Duplicating the rule in both interfaces would allow the behavior to drift.

**Why are DataLoaders created in `Context` per request, and why does the batch function match rows to keys by value?**  
A DataLoader caches values, so a process-global loader could leak stale or another request's data. A per-request loader keeps batching and caching scoped to one request. Database row order is not guaranteed to equal key order, so rows are grouped by key and results are reconstructed in the original keys order.

**Why do `check_limit` and `parse_id` coexist with `MaskErrors`?**  
Expected client mistakes deserve precise messages such as `Invalid ID: 'abc'` or `limit must be between 1 and 100`; these messages help the client fix the request. `MaskErrors` is the second layer for unforeseen implementation/database exceptions, where exposing the original text could leak internals.

