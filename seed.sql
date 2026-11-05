INSERT INTO courses (
    id,
    title,
    description,
    credits,
    is_elective,
    likes
)
VALUES
(
    'modern-frontend',
    'Modern Frontend: React & Next.js',
    'React 19, Server Components, and the App Router.',
    5,
    FALSE,
    24
),
(
    'backend-fastapi',
    'Backend Foundations: FastAPI',
    'Async REST APIs in Python with FastAPI and Pydantic.',
    5,
    FALSE,
    19
),
(
    'databases-postgresql',
    'Relational Databases: PostgreSQL',
    'Schemas, SQLAlchemy, and migrations with Alembic.',
    5,
    FALSE,
    15
),
(
    'api-design',
    'API Design: REST vs GraphQL',
    'Comparing REST and GraphQL in one hands-on project.',
    4,
    TRUE,
    11
),
(
    'web-security',
    'Web Security Essentials',
    'JWT/OAuth2, XSS, CSRF, and SQL injection defense.',
    4,
    FALSE,
    21
),
(
    'ai-integration',
    'AI/LLM Integration',
    'LLM features in an app via the OpenAI API.',
    5,
    TRUE,
    32
);


INSERT INTO students (name, email)
VALUES
    ('Aigerim', 'aigerim@example.com'),
    ('Daulet', 'daulet@example.com'),
    ('Arman', 'arman@example.com');


INSERT INTO enrollments (student_id, course_id)
VALUES
    (1, 'web-security'),
    (1, 'backend-fastapi'),
    (2, 'ai-integration'),
    (2, 'databases-postgresql'),
    (3, 'modern-frontend');