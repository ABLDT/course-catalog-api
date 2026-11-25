import httpx

BASE = "http://localhost:8000"


def login(email, password):
    response = httpx.post(
        f"{BASE}/auth/login",
        data={"username": email, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def ask(query, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    return httpx.post(
        f"{BASE}/graphql",
        json={"query": query},
        headers=headers,
    )


def first_error(response):
    return response.json()["errors"][0]["message"]


def me_line(response):
    user = response.json()["data"]["me"]
    return f"{user['email']} {user['role']}"


def students_count(response):
    return str(len(response.json()["data"]["students"]))


def name_and_email(response):
    student = response.json()["data"]["student"]
    return f"{student['name']}, email {student['email']}"


def email_only(response):
    return response.json()["data"]["student"]["email"]


def emails_of_enrollments(response):
    rows = [
        row["student"]["email"]
        for row in response.json()["data"]["enrollments"]
    ]

    shown = sum(email is not None for email in rows)

    return f"{shown} shown, {len(rows) - shown} hidden"


def http_status(response):
    return f"HTTP {response.status_code}"


student = login("aigerim@example.com", "aigerim-demo-pass")
admin = login("admin@example.com", "admin-demo-password")

ME = "{ me { email role } }"
STUDENTS = "{ students { name } }"
STUDENT_2 = '{ student(id: "2") { name email } }'
STUDENT_1 = '{ student(id: "1") { email } }'
ENROLLMENTS = "{ enrollments(limit: 4) { student { email } } }"


CASES = [
    ("me, no token", ME, None,
     first_error, "Authentication required"),

    ("me, student", ME, student,
     me_line, "aigerim@example.com student"),

    ("students, student", STUDENTS, student,
     first_error, "Admin role required"),

    ("students, admin", STUDENTS, admin,
     students_count, "3"),

    ("student(2).email, student", STUDENT_2, student,
     name_and_email, "Daulet, email None"),

    ("student(1).email, student", STUDENT_1, student,
     email_only, "aigerim@example.com"),

    ("student(2).email, admin", STUDENT_2, admin,
     email_only, "daulet@example.com"),

    ("enrollments -> student.email", ENROLLMENTS, student,
     emails_of_enrollments, "2 shown, 2 hidden"),

    ("bad token", ME, "abc.def.ghi",
     http_status, "HTTP 401"),
]


failed = 0

for title, query, token, pick, expected in CASES:
    response = ask(query, token)

    try:
        actual = pick(response)
    except (KeyError, IndexError, TypeError):
        actual = "?"

    ok = actual == expected
    failed += not ok

    print(f"{'ok ' if ok else 'FAIL'} {title:<30} {actual}")

print(f"{len(CASES) - failed} of {len(CASES)} as expected")