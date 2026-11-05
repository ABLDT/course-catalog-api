-- seed.sql: initial data
-- For the training database only!

TRUNCATE enrollments, students, courses RESTART IDENTITY;

INSERT INTO courses (
    id,
    title,
    description,
    credits,
    is_elective,
    likes,
    level
)
VALUES
(
    'modern-frontend',
    'Modern Frontend: React & Next.js',
    'React 19, Server Components, and the App Router.',
    5,
    FALSE,
    24,
    'intermediate'
),
(
    'backend-fastapi',
    'Backend Foundations: FastAPI',
    'Async REST APIs in Python with FastAPI and Pydantic.',
    5,
    FALSE,
    19,
    'intermediate'
),
(
    'databases-postgresql',
    'Relational Databases: PostgreSQL',
    'Schemas, SQLAlchemy, and migrations with Alembic.',
    5,
    FALSE,
    15,
    'intermediate'
),
(
    'api-design',
    'API Design: REST vs GraphQL',
    'Comparing REST and GraphQL in one hands-on project.',
    4,
    TRUE,
    11,
    'beginner'
),
(
    'web-security',
    'Web Security Essentials',
    'JWT/OAuth2, XSS, CSRF, and SQL injection defense.',
    4,
    FALSE,
    21,
    'intermediate'
),
(
    'ai-integration',
    'AI/LLM Integration',
    'LLM features in an app via the OpenAI API.',
    5,
    TRUE,
    32,
    'beginner'
);


INSERT INTO students (name, email)
VALUES
    ('Aigerim', 'aigerim@example.com'),
    ('Daulet', 'daulet@example.com'),
    ('Arman', 'arman@example.com');


INSERT INTO enrollments (student_id, course_id)
VALUES
    (1, 'modern-frontend'),
    (1, 'ai-integration'),
    (2, 'modern-frontend'),
    (2, 'ai-integration'),
    (3, 'backend-fastapi'),
    (3, 'ai-integration');