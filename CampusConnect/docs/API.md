# API reference

All JSON responses use `{ "data": ... }` on success and `{ "error": { "code": "...", "message": "..." } }` on failure. Login uses a Flask session cookie. Send `X-CSRF-Token` on each POST, PUT, PATCH, and DELETE; get it from `GET /api/auth/csrf`. Parameter errors return 400, unauthenticated requests 401, forbidden actions 403, conflicts 409, and ineligible job applications 422.

| Method | Path | Access |
| --- | --- | --- |
| POST | `/api/auth/register` | Public; creates student only |
| POST | `/api/auth/login` | Public |
| POST | `/api/auth/logout` | Signed in |
| GET | `/api/dashboard` | Signed in |
| GET/POST | `/api/students` | Admin/faculty/placement officer for list; admin for create |
| GET/PUT/DELETE | `/api/students/<id>` | Scoped read; admin write |
| PUT | `/api/students/<id>/academic-profile` | Admin/faculty |
| GET/PUT | `/api/students/<id>/skills` | Own student skills; admin/faculty for edits |
| GET | `/api/students/<id>/performance` | Own student, faculty in department, admin/placement officer |
| GET/POST | `/api/departments` | Public read; admin write |
| PUT/DELETE | `/api/departments/<id>` | Admin; deletes are blocked by existing foreign key references |
| GET/POST | `/api/courses` | Signed-in read; admin/faculty write |
| GET/POST | `/api/semesters` | Signed-in read; admin write |
| POST | `/api/enrollments`, `/api/attendance`, `/api/marks` | Admin/faculty |
| GET/POST | `/api/companies` | Signed-in read; admin/placement officer write |
| GET/POST | `/api/companies/<id>/recruiters` | Admin/placement officer |
| GET/POST | `/api/jobs` | Signed-in read; admin/placement officer write |
| PATCH | `/api/jobs/<id>` | Admin/placement officer; update job status |
| GET | `/api/jobs/<id>/eligible-students` | Admin/placement officer |
| POST | `/api/jobs/<id>/apply` | Student; backend eligibility required |
| GET/PATCH | `/api/applications` | Own student list or placement/admin; status update placement/admin |
| GET/POST | `/api/applications/<id>/interviews` | Scoped student read; placement/admin write |
| GET/POST | `/api/applications/<id>/offers` | Student own read; placement/admin write |
| PATCH | `/api/offers/<id>` | Admin/placement officer; update offer status |
| GET | `/api/reports/overview`, `/api/reports/placements` | Admin/placement officer |

Successful resource creation returns 201. Use numeric IDs from the relevant list endpoints. Skills in a job are supplied as `required_skills: ["Python", "SQL"]` and all listed skills are required.
