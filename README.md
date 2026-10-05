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