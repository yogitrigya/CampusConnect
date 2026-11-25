# CampusConnect architecture

CampusConnect is a Flask server-rendered application with JSON endpoints. Flask blueprints separate authentication, HTML pages, and API operations. Business rules live in request handlers and small validation helpers; SQL remains explicit and parameterized through mysql-connector-python.

## Request and data flow

1. A browser sends a request with a signed Flask session cookie and, for writes, a session CSRF token.
2. Route decorators enforce authentication and role permissions on the server.
3. The route validates input and calls a parameterized SQL statement using the request-scoped MySQL connection.
4. Multi-row operations use the transaction context manager, which commits on success and rolls back on errors.
5. JSON endpoints return `{ "data": ... }` or `{ "error": { "code": ..., "message": ... } }`.

## Main areas

- `app/__init__.py`: application factory, CSRF checks, teardown, and safe error responses.
- `app/auth/`: student registration, login/logout, bcrypt password checks, and role decorators.
- `app/database/`: connection, cursor, query, and transaction helpers.
- `app/api.py`: academic, student, company, recruitment, and report endpoints.
- `templates/` and `static/`: Bootstrap/Jinja pages, responsive styles, and dashboard behavior.
- `database/`: preserved original SQL coursework, optional demo seed, and additive versioned migrations.

## Security boundaries

Public registration always creates a student role. Privileged accounts are created with the local CLI and are never assigned from user-submitted form data. Passwords are bcrypt hashes, SQL values are parameterized, writes require CSRF tokens, and sensitive APIs repeat authorization checks on the server. Use a MySQL account limited to the needed database operations rather than `root`.
