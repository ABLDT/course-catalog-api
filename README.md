# Course Catalog API

A FastAPI backend for the Course Catalog project.

## How to run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python -m fastapi dev main.py
```

Open Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## What was verified

- `GET /` returns a server status message.
- `GET /courses` returns all 6 courses.
- `GET /courses/web-security` returns the Web Security course.
- `GET /courses/nope` returns `404 Course not found`.
- `GET /courses?is_elective=true` returns 2 elective courses.
- `GET /courses?is_elective=false` returns 4 required courses.
- `GET /courses?sort=title` sorts courses alphabetically.
- `GET /courses?page=2&page_size=2` returns:
  - `web-security`
  - `backend-fastapi`


### Breakage 1: CORS middleware removed
- What I did: commented out the entire `app.add_middleware(...)` block.
- Console: `No 'Access-Control-Allow-Origin' header is present on the requested resource`.
- Network: browser requests were blocked; enrollment preflight `OPTIONS /enrollments` returned 405, so POST was not sent.
- Cause: CORSMiddleware was removed, so browser requests received no CORS permission.
- How I found it: checked Network status, response headers, and the backend terminal.


### Breakage 2: Trailing slash in allowed origin
- What I did: changed `allow_origins=["http://localhost:3000"]` to `allow_origins=["http://localhost:3000/"]`.
- Console: `No 'Access-Control-Allow-Origin' header is present on the requested resource`.
- Network: `/filter` and the like were blocked by CORS. The like POST reached the backend with 200, but the browser blocked the response. The enrollment preflight `OPTIONS /enrollments` returned 400, so the POST was not sent.
- Cause: the allowed origin had a trailing slash and did not exactly match `http://localhost:3000`.
- How I found it: checked the failed preflight status and compared the page origin with `allow_origins`.




### Breakage 3: POST method not allowed
- What I did: removed `allow_methods=["*"]` from CORSMiddleware.
- Console: `Response to preflight request doesn't pass access control check: It does not have HTTP ok status`.
- Network: `/filter` worked with GET 200. The like POST worked with 200. The enrollment preflight `OPTIONS /enrollments` returned 400, so the POST was not sent.
- Cause: without `allow_methods=["*"]`, POST was not allowed for the preflight request.
- How I found it: the origin header was present, but the OPTIONS request returned 400 and `access-control-allow-methods` showed only GET.


### Breakage 4: Different frontend origin
- What I did: opened the frontend at `http://127.0.0.1:3000` while the backend allowed only `http://localhost:3000`.
- Console: `No 'Access-Control-Allow-Origin' header is present on the requested resource`.
- Network: the request to `/courses` was blocked by CORS even though the backend returned 200.
- Cause: `localhost` and `127.0.0.1` are different origins.
- How I found it: compared the browser origin with the value in `allow_origins`.


### Breakage 5: Python error that looks like CORS
- What I did: changed `p["offset"]` to `p["ofset"]` in `list_courses`.
- Console: the browser showed a failed request that could be mistaken for a CORS problem.
- Network: `/filter` failed and `/courses` showed the error page, while the like request returned 200 and enrollment returned 201.
- Backend: FastAPI returned `500 Internal Server Error` for `/courses` and showed `KeyError: 'ofset'`.
- Cause: a Python dictionary key typo, not a CORS configuration problem.
- How I found it: checked the FastAPI terminal traceback instead of relying only on the browser error.