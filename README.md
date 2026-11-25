# course-catalog-api

Backend for the course catalog: FastAPI, SQLAlchemy, PostgreSQL, Alembic, Strawberry GraphQL, and JWT authentication with roles (Advanced Web Technologies, Labs 4–9). The Next.js frontend is maintained in the separate `course-catalog` repository.

## How to run

Requirements: Python 3.11+, PostgreSQL 16+, and Node.js for the frontend.

For a new local installation, create the database role and database once as the PostgreSQL superuser. Replace the example password with your own local password.

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

From the backend project directory in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` in `.env` to match the local database credentials. Generate a random signing key with the following command and set `SECRET_KEY` in `.env` to the generated value. Do not publish the key or the `.env` file. The application requires a key of at least 32 characters.

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Keep `GRAPHQL_INTROSPECTION=true` for the local GraphiQL interface. Then initialize the database and start the API:

```powershell
alembic upgrade head
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
python seed_users.py
alembic check
uvicorn main:app --reload
```

`seed.sql` resets the demo data, including the users table. Always run `seed_users.py` after it. Do not use this reset procedure on a database containing important data.

REST documentation: http://localhost:8000/docs. GraphiQL: http://localhost:8000/graphql.

Demo accounts (local course fixtures only; never use these passwords in production):

| E-mail | Role | Password |
|---|---|---|
| admin@example.com | admin | admin-demo-password |
| aigerim@example.com | student (student 1) | aigerim-demo-pass |
| daniyar@example.com | student (student 2) | daniyar-demo-pass |
| asel@example.com | student (student 3) | asel-demo-password |

The account e-mail and the linked student profile e-mail are separate fields. In my seed data, student 2 is Daulet and student 3 is Arman.

For the frontend, in the `course-catalog` directory, run `npm install`, set `API_URL=http://localhost:8000` and `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`, and run `npm run dev`. Open http://localhost:3000/login or http://localhost:3000/account. The session cookie is HttpOnly, Secure and SameSite=Lax, with path `/` and a configured lifetime of 900 seconds.

### Verification results

The local database was dropped and recreated, all three Alembic migrations (0001–0003) were applied from scratch, and the seed scripts restored 6 courses, 3 students, 6 enrollments and 4 users. The final test suite was then rerun successfully. The GraphQL protection checks were also verified before the database rebuild.

| Script or check | Observed result |
|---|---|
| `check_users.py` | 4/4 |
| `try_auth.py` | 6/6 |
| `try_tokens.py` | 9/9 |
| `try_timing.py` | 40 requests per case; unknown e-mail median 40.3 ms, known e-mail median 40.2 ms |
| `try_access.py` | 14/14 |
| `try_errors.py` | 5/5 |
| `try_graphql_access.py` | 9/9 |
| `try_graphql.py` | 8/8 |
| `try_n_plus_1.py` | 3 student rows and 6 enrollment rows; 4 SQL queries for each request |
| `try_protection.py` | Depth, alias and argument limits work; unexpected errors are masked; introspection enabled |
| `measure.py` | REST: 5 requests, 2 rounds, 1116 bytes, 5 SQL queries; GraphQL: 1 request, 1 round, 332 bytes, 3 SQL queries |
| `scan_routes.py` | 11 routes checked, 8 open without a token |
| `scan_graphql.py` | 11 fields checked, 8 open without a token |
| `alembic current` | 0003 (head) |
| `alembic check` | No new upgrade operations detected |

All 55 checks in the seven counted test scripts passed again after the clean database rebuild. The additional SQL query in the authenticated N+1 tests is the user lookup, not a regression in DataLoader batching. The measurement script uses unauthenticated public reads, so its GraphQL request still uses three SQL queries.

## Access matrix

Actual results from `try_access.py` (14 of 14 as expected). The administrator has no linked student profile, so the self-enrollment case is not applicable.

| Request | Anonymous | Student | Admin |
|---|---:|---:|---:|
| GET /courses | 200 | 200 | 200 |
| GET /me | 401 | 200 | 200 |
| GET /enrollments | 401 | 403 | 200 |
| POST /enrollments, for yourself | 401 | 201 | — |
| POST /enrollments, for another | 401 | 403 | 201 |

GraphQL access checks passed 9/9. The public course catalog is available without login; `me` requires authentication, `students` requires the admin role, and `Student.email` is restricted to the owner or admin. An unauthorized nullable field returns null with an error. An invalid bearer token is rejected with HTTP 401 before GraphQL execution.

## Open spots

The following 16 entries were reported open by the two local scanners. These are observations of the lab's current scope, not a claim that all open entries are security defects. The proposed access rules are design recommendations for the final project and have not been implemented in this lab.

| Route or field | Verdict | How to close it |
|---|---|---|
| `GET /` | Public service status by design | Keep public; return no sensitive details |
| `GET /courses` | Public catalog by design | No change needed |
| `GET /courses/{course_id}` | Public course details by design | No change needed |
| `POST /courses/{course_id}/like` | Unrestricted modification of the like counter | Require authentication and enforce a per-user like rule |
| `POST /students` | Unrestricted profile creation | Restrict profile creation to an approved registration workflow or admin |
| `GET /students/{student_id}` | Student profile privacy concern | Require owner or admin access to private profile data |
| `GET /students/{student_id}/enrollments` | Enrollment privacy concern | Require owner or admin access |
| `GET /stats/courses` | Public aggregate statistics if approved | Keep public only if the final specification permits it |
| GraphQL `Query.courses` | Public catalog by design | No change needed |
| GraphQL `Query.course` | Public course details by design | No change needed |
| GraphQL `Query.student` | Student identity and profile privacy concern | Apply the final profile access policy; keep sensitive fields protected |
| GraphQL `Query.enrollments` | Enrollment privacy concern | Restrict the full list to admin |
| GraphQL `Course.enrollments` | Enrollment relationship privacy concern | Restrict access or return only permitted records |
| GraphQL `Student.enrollments` | Enrollment relationship privacy concern | Require owner or admin access |
| GraphQL `Mutation.enroll` | Inconsistent access policy with REST | Enforce the same authenticated owner/admin rule in the shared business layer |
| GraphQL `Mutation.likeCourse` | Unrestricted modification of the like counter | Enforce the same authenticated per-user rule as REST |

## Threat table

| Where | What can break | How it is covered | How I checked |
|---|---|---|---|
| The login form | Account enumeration and password guessing | Generic login error, dummy password hash verification for unknown accounts; login rate limiting is not implemented | `try_auth.py`: 6/6; final timing check: 40.3 ms vs 40.2 ms median |
| Passwords and the key | Plaintext password storage or weak signing key | Argon2id password hashes; required secret with minimum length of 32 characters; secrets belong in local environment files | `check_users.py`: 4/4; missing and short keys rejected; two hashes of the same password differed |
| Token and role | Invalid tokens or stale permissions | Token signature and claims are validated; current user and role loaded from the database | `try_tokens.py`: 9/9; role changes immediately affected access in experiment 4 |
| Permissions on objects | Access to another student's records | REST role and owner checks; GraphQL permissions on selected queries and the email field | `try_access.py`: 14/14; `try_graphql_access.py`: 9/9; remaining gaps documented above |
| Cookie and Next.js | Exposure of the session to client-side scripts or invalid sessions accepted | HttpOnly, Secure, SameSite=Lax; server-only session helpers; DAL verifies the session through FastAPI | DevTools confirmed the flags; `document.cookie` did not show `session`; an invalid session resulted in 307 redirect and API 401 |
| Logout and lifetime | Session credentials remain valid longer than intended | Cookie removed at logout; JWT has a 15-minute lifetime | Cookie disappearance confirmed; JWT claim interval was 900 seconds; direct post-logout token validity check not yet performed |

Deliberately not closed:

- Login rate limiting: a shared store such as Redis can maintain short-lived counters across API workers. Combining account and source-based limits avoids relying on a single e-mail counter and reduces the risk of abusive account lockouts.
- Immediate JWT revocation at logout: a server-side revocation list or token-version mechanism could invalidate credentials before expiration, at the cost of shared state and an additional lookup. Currently logout removes the browser session, but does not guarantee immediate server-side token revocation.

## Experiment log

| No. | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | Secret key validation and Argon2id hashes | Missing key: Field required. Short key: minimum 32 characters. Two hashes of one password differed; correct password verified, wrong password did not. | Settings validation and independent random salts. | Set a valid local secret and restored the normal environment. |
| 2 | Login timing with and without the dummy hash | Initial protected: unknown 40.1 ms, known 39.8 ms. Without defense: 3.1 ms vs 40.7 ms. Restored: 40.4 ms vs 40.5 ms. Final clean-start run: 40.3 ms vs 40.2 ms. Each case used 40 requests. | Password verification work explains the timing difference. | Restored the original login logic; `try_auth.py` passed 6/6. |
| 3 | Token validation | Normal configuration: 9/9. Temporary experimental configuration: 3/9. Restored: 9/9. | Token authenticity and claims must be verified before trusting the user identity. | Restored `security.py` and reran the test. |
| 4 | Role changes with the same token | Admin → student → admin: 200, 403, 200. Student → admin → student: 403, 200, 403. | Role is read from the database on each authenticated request. | Restored both original roles. |
| 5 | Object-level authorization | Access matrix changed from 14/14 to 13/14 in the temporary experiment. A test enrollment (ID 20) was created and confirmed in PostgreSQL. | Authentication alone does not enforce ownership. | Removed the test enrollment, restored `main.py`, and obtained 14/14 again. Database count returned to 6 enrollments. |
| 6 | Field permissions and nullable behavior | Part B: non-nullable protected email caused 7/9; restored nullable field gave 9/9 and `2 shown, 2 hidden`. Part A was not separately performed. | A non-nullable field error propagates to its parent. Field-level permissions apply regardless of the query path. | Restored `email: str \| None` with its permission class. |
| 7 | Invalid session cookie and server-side verification | Without a cookie: 307 to `/login`. Invalid session cookie: 307 to `/login`; API `/me`: 401. Valid session: API 200. The second experimental configuration was not separately performed. | Cookie presence is only an optimistic check; the API validates the token. | Kept `verifySession()` in the account page; no temporary code change was needed for the completed checks. |
| 8 | Token after logout | Logout deleted the `session` cookie and returned to the login page. The 900-second JWT lifetime was confirmed earlier. Direct post-logout token verification remains untested. | Browser cookie deletion is different from server-side token revocation. | No revocation mechanism was added in this lab; document the limitation. |

## Decisions

**Why read the role from the database?** It costs an extra SQL query per authenticated request, but permission changes take effect immediately. Experiment 4 demonstrated both role changes with unchanged tokens.

**Why protect a nullable GraphQL field?** Field-level authorization applies regardless of which query reaches the field. Allowing null preserves permitted data when access to the email is denied; experiment 6 showed that a non-nullable field can cause otherwise permitted parent data to disappear.

**Why are both proxy and verifySession needed?** The proxy gives a quick redirect when a cookie is absent, but presence alone does not establish a valid identity. The DAL asks the API to validate the session before returning account data. The invalid-session test confirmed the API's 401 and the frontend redirect.
