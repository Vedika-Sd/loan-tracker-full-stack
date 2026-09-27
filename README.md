# Loan Tracker Backend

Django REST API for a two-role personal-loan workflow.

## Setup

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

The project is fully local. It uses SQLite in `db.sqlite3` and stores uploaded documents in the local `media/` directory. No PostgreSQL, Supabase account, cloud database, or cloud storage configuration is required.

## Run and verify

Run the local SQLite application:

```powershell
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`. Uploaded files are written to `media/` automatically.

## Open the dashboard

Keep the Django server running in one PowerShell window, then open a second window:

```powershell
cd "g:\Sem - 7\Project\Loan Tracker\loan-tracker-backend"
python -m http.server 5173 --directory frontend
```

Open `http://127.0.0.1:5173/` in the browser. The dashboard changes automatically based on the signed-in role. Customers can submit enquiries, upload or replace documents, and follow the timeline. Officers can review documents, make decisions, disburse loans, and view the status bar chart.

## API flow

1. `POST /api/auth/register/` with `username`, `email`, `password`, and `role: customer`.
2. `POST /api/auth/login/` to receive `access` and `refresh` JWT tokens.
3. Send `Authorization: Bearer <access>` on all protected requests.
4. Customer: `POST /api/loans/` with `amount` and `tenure_months`.
5. Customer: `POST /api/loans/<id>/documents/` as multipart form data with `document_type` (`id_proof`, `income_proof`, or `address_proof`) and `file`.
6. Officer: `POST /api/loans/<id>/documents/<document_id>/verify/` with `status: verified` or `rejected`.
7. Officer: `POST /api/loans/<id>/decision/` with `decision: approve` or `reject`.
8. Officer: `POST /api/loans/<id>/disburse/` after approval.
9. Customer or Officer: `GET /api/loans/<id>/` to read the application, documents, and timeline.
10. Officer: `GET /api/loans/dashboard/` to read counts by application status.

The local demo includes an Officer account described below. Public registration rejects the Officer role. Additional Officers can be created through Django admin (`/admin/`) or the Django shell.

## Local demo accounts

Use the following local Officer account to test the admin and Officer dashboard:

```text
Admin URL: http://127.0.0.1:8000/admin/
Username: admin
Password: Admin@12345
```

You can also use the same Officer account in the frontend dashboard. Change this password before using the project outside local development.

## Quick checks

Unauthenticated access should return `401`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/loans/
```

Run the complete automated verification with:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```
