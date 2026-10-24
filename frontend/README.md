# VeriFyra React frontend

A React + Vite client for the existing Django REST Framework API in `raheelhassangit/VeriFyra_AI`. The UI does not duplicate backend business logic: Django remains responsible for authentication, authorization, validation, project ownership, audit orchestration, and judging rules.

## Requirements

- Node.js 20+ and npm
- The VeriFyra Django API running at `http://127.0.0.1:8000`
- For audit execution, the backend's Redis/Celery worker and FastAPI agent service must also be running/configured

## Run locally (Windows PowerShell)

From this `frontend` directory:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. The default API URL is `http://127.0.0.1:8000/api/v1`.

If Django runs elsewhere, change `VITE_API_BASE_URL` in `.env`. Django's `CORS_ALLOWED_ORIGINS` already defaults to `http://localhost:5173` in this repository; make sure the active environment has that origin allowed.

## API routes used

| UI feature | Django API |
| --- | --- |
| Health/API availability | `GET /api/v1/health/` (backend endpoint; useful for manual check) |
| Register | `POST /api/v1/auth/register/` |
| Sign in / refresh / sign out | `POST /api/v1/auth/token/`, `POST /api/v1/auth/token/refresh/`, `POST /api/v1/auth/logout/` |
| Current user | `GET /api/v1/auth/me/` |
| Projects | `GET/POST /api/v1/projects/`, `POST /api/v1/projects/{uuid}/publish/`, `POST /api/v1/projects/{uuid}/unpublish/` |
| Start audit | `POST /api/v1/projects/{uuid}/audits/` |
| Audit history/details | `GET /api/v1/audits/`, `GET /api/v1/audits/{uuid}/`, `GET /api/v1/audits/{uuid}/agents/` |
| Audit actions | `POST /api/v1/audits/{uuid}/cancel/`, `POST /api/v1/audits/{uuid}/retry/` |
| Judge workspace | `GET /api/v1/judging/projects/`, `GET/POST /api/v1/judging/evaluations/`, `PATCH /api/v1/judging/evaluations/{uuid}/`, `POST /api/v1/judging/evaluations/{uuid}/submit/`, `GET /api/v1/judging/rubric/` |

The frontend follows the backend's role rules: public registration creates a `PARTICIPANT`; a `JUDGE` account must be provisioned through the backend/admin; only judges can use the judging API. The browser UI is not a substitute for backend authorization.

## Notes

- Access and refresh JWTs are stored in `localStorage`; refresh is attempted after an API `401` and the session is cleared if refresh fails. For higher-security production deployments, consider an HttpOnly secure-cookie architecture.
- No LLM/API secret belongs in Vite environment variables prefixed with `VITE_`; those variables are exposed to the browser.
- A successful project creation does not guarantee that an audit can run: Redis, Celery, and the agent service must be reachable, and agent implementations/configuration must be ready.


## Visual theme
The frontend uses the VeriFyra palette from the supplied reference: forest green `#3E503C`, muted sage `#7F886A`, warm cream `#F3ECDB`, and coral `#FF6F3D`. The public landing page is `/`; authentication and protected application routes are preserved.
