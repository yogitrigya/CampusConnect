# CampusConnect

CampusConnect is a Flask + MySQL campus management and placement portal for the DBMS project. It keeps the existing relational coursework and adds secure role-based web workflows for students, faculty, administrators, and placement officers.

## Current features

- Student-only registration, bcrypt login/logout, server-side roles, signed sessions, CSRF checks, and a CLI for privileged accounts.
- Student profiles, academic data, skills, departments, courses, semesters, enrollments, attendance, and examination results.
- Company/recruiter records, job eligibility by academic criteria and required skills, applications, interviews, and offers.
- SQL-backed overview and placement reports with department charts.
- Parameterized SQL, foreign keys, uniqueness/range checks, additive schema migrations, and transaction helpers.

The original schema is required for the application: `users`, `departments`, `students`, `faculty`, `semesters`, `courses`, and `enrollments`. See [schema notes](docs/SCHEMA.md) and [API reference](docs/API.md).

## Requirements

- Python 3.11 or newer
- MySQL 8.0.16 or newer (CHECK constraints are enforced from MySQL 8.0.16)
- Existing `campusconnect` core tables, or a new empty database initialized as below

## Windows setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally. Set a random `SECRET_KEY`, MySQL host, database, and an application account. Do not commit `.env` or put credentials in frontend code.

For a **new empty development database only**, execute `database/01_Database_Creation.sql` and then `database/02_Table_Creation.sql` in MySQL Workbench. If the original database already exists, do not rerun its table creation script as a schema repair; inspect it first. The app never creates or drops the original database/core tables.

The migration runner first verifies all seven core tables, reports pending migration files by default, and applies additive tables only with `--apply`:

```powershell
python scripts/audit_database.py
python scripts/migrate.py
python scripts/migrate.py --apply
```

When using a least-privilege runtime account, set temporary `MIGRATION_DB_USER` and `MIGRATION_DB_PASSWORD` values for migration execution. Grant that account DDL rights only for the migration window. The normal `DB_USER` should have only the SELECT, INSERT, UPDATE, and DELETE rights the app needs. For example, a DBA can create the runtime principal with:

```sql
CREATE USER 'campusconnect_app'@'localhost' IDENTIFIED BY 'set-a-local-secret';
GRANT SELECT, INSERT, UPDATE, DELETE ON campusconnect.* TO 'campusconnect_app'@'localhost';
```

Set `.env` back to the runtime principal after migrating. Never use MySQL root credentials in the app.

Optional demo records are in `database/seed_data.sql`. Execute only in a development/demo database. They create visible sample profiles without fake passwords; create login users with the CLI instead.

## Run the application

```powershell
python scripts/create_user.py
python app.py
```

Open `http://127.0.0.1:5000`. Student registration requires an existing department. For local demonstration, set `SESSION_COOKIE_SECURE=false`; use HTTPS and set it to `true` behind a production TLS proxy.

Create the first administrator using `python scripts/create_user.py` and choose `admin`. The same command provisions faculty and placement officer users. Only students can register through the public form.

## Testing

Run the local, database-independent suite:

```powershell
python -m unittest discover -s tests -v
```

Optional MySQL integration checks require a separate database named with a `_test` suffix (for example `campusconnect_test`) containing the seven existing core tables. Configure its connection using the environment variables and `TEST_DB_NAME`; then enable explicitly:

```powershell
$env:TEST_DB_NAME = 'campusconnect_test'
$env:CAMPUSCONNECT_RUN_DB_TESTS = '1'
python -m unittest discover -s tests -v
```

The integration test refuses database names without the `_test` suffix. It applies only the additive project migration and creates disposable, uniquely named records to verify connectivity, eligibility, duplicate application prevention, interview/offer workflows, and rollback behavior. Do not point tests at your development database.

## API and CSRF

JSON API paths and role access are listed in [docs/API.md](docs/API.md). Obtain a CSRF token from `GET /api/auth/csrf`; include it in the `X-CSRF-Token` header for every state-changing request. Login returns a session cookie. API and form errors do not return SQL details or stack traces.

## Role guide

- **Admin:** manage students, departments, academic catalogs, companies and placement operations; view reports.
- **Student:** view own profile, update own skills, see job openings and own applications/interviews/offers, apply when eligible.
- **Faculty:** manage courses, enrollment, attendance, assessment results, and academic profiles.
- **Placement officer:** manage recruiters, companies, jobs, applications, interviews, and offers; view placement reporting.

Backend route guards enforce these boundaries; hiding a dashboard action is not treated as authorization.

## Demonstration workflow

1. Run migrations and optional demo seed data; create an admin with the CLI.
2. As admin, review students/departments and create a placement officer account.
3. As faculty, record course, enrollment, attendance, and marks information.
4. As placement officer, create a company and job with CGPA, percentage, backlog, and skill requirements; inspect eligible students.
5. Register a student, enter verified academic data as faculty/admin, add skills, and apply to an eligible opening.
6. As placement officer, review the application, schedule interview rounds, record an offer, and mark it accepted.
7. Review the placement officer/admin dashboard and department placement report.

## DBMS coursework and safety

Existing joins, aggregates, subqueries, view, index, triggers, procedure/function, transaction, and constraint scripts remain in `database/`. Demo scripts are separate from app startup. Transaction and trigger data-changing examples are disabled by default to prevent accidental updates/deletes. The enrollment audit triggers remain the database's audit mechanism; inspect `enrollment_audit` to demonstrate event history. Run query plans with `EXPLAIN` in Workbench using representative rows.

## Limitations and future work

- Live schema compatibility, migration execution, and SQL query plans must be verified against the developer's actual MySQL instance before demonstration; this workspace did not include database connection settings.
- The current UI provides dashboards and quick actions; advanced editing/search screens, pagination, email notifications, file uploads, and production deployment configuration can be expanded in a later iteration.
- Academic scores are maintained by admin/faculty roles; verify source records before using eligibility decisions in a real hiring process.
