# Loan Tracker Full Stack

A local-first loan-operations system for personal-loan processing, built with a Django REST API and a static vanilla JavaScript frontend.

## Business problem

Personal-loan operations are often fragmented across calls, chat threads, and disconnected spreadsheets. That causes four recurring problems:

- poor visibility into required KYC/supporting documents,
- unclear ownership between customer and loan officer,
- ambiguous application status during review,
- manual coordination that slows approvals and disbursements.

This project centralizes that process into one role-aware workflow so customers and officers can move applications from enquiry to disbursement with explicit gates and audit events.

## Who uses the system

- **Customer**: creates applications, uploads required documents, replaces rejected documents, tracks timeline and status.
- **Officer**: verifies/rejects documents with reasons, approves/rejects applications, disburses approved loans, monitors status counts.

## End-to-end loan-processing pipeline

The implemented pipeline is:

1. **Customer registration + JWT login**
   - `POST /api/auth/register/` creates customer accounts only.
   - `POST /api/auth/login/` returns JWT access/refresh tokens.
2. **Loan enquiry/application creation**
   - Customer creates an application with `amount` and `tenure_months`.
   - Application starts in `enquiry`.
3. **Required document submission**
   - Customer uploads exactly these document types: `id_proof`, `income_proof`, `address_proof`.
4. **Document storage + pending state**
   - Uploaded files are saved under `media/` (via Django storage).
   - Documents are created/reset with `pending` status.
5. **Officer verification/rejection**
   - Officer marks each document `verified` or `rejected` and can include rejection reason.
6. **Rejected-document replacement**
   - Customer can re-upload only when that document type is currently `rejected`.
   - Replacement resets status back to `pending`.
7. **Approval gate (all three docs verified)**
   - Application approval is blocked unless all three required document types are `verified`.
8. **Officer application decision**
   - Officer sets application decision to `approved` or `rejected`.
9. **Disbursement gate (approved only)**
   - Disbursement is blocked unless status is `approved`.
10. **Timeline + dashboard visibility**
   - Each major action is recorded in timeline/audit events.
   - Officer dashboard exposes counts by application status.

## Application status lifecycle

`LoanApplication.status` uses:

- `enquiry`
- `documents_submitted`
- `documents_rejected`
- `approved`
- `rejected`
- `disbursed`

Typical progression:

- `enquiry` → `documents_submitted` (after all required document types are uploaded)
- `documents_submitted` → `documents_rejected` (if any document is rejected)
- `documents_submitted`/`documents_rejected` → `approved` or `rejected` (officer decision)
- `approved` → `disbursed`

## Frontend ↔ backend integration

- **Frontend**: static files in `frontend/`, served on **port 5173**.
- **Backend**: Django REST API served on **port 8000**.
- **Auth**: JWT ****** in `Authorization` header for protected endpoints.
- **Session state**: frontend persists token/user in `localStorage` keys:
  - `loanflow_access`
  - `loanflow_user`
- **Role-aware UI**: frontend renders customer or officer dashboard based on `user.role`.
- **Document upload**: multipart form submissions (`document_type` + `file`).
- **CORS**: backend allows `http://localhost:5173` and `http://127.0.0.1:5173`.

## Architecture and project structure

```text
loan-tracker-full-stack/
├─ accounts/          # custom User, auth serializers/views/urls, auth tests
├─ loans/             # loan/domain models, workflow views, permissions, tests
├─ core/              # project settings and root URL config
├─ frontend/          # static HTML/CSS/JS dashboard (customer + officer views)
├─ manage.py
├─ requirements.txt
├─ .env.example
├─ db.sqlite3         # local SQLite database (created/used locally)
└─ media/             # uploaded loan documents
```

## API endpoints

Base URL: `http://127.0.0.1:8000`

### Auth (`/api/auth/`)

| Method | Path | Purpose | Access |
|---|---|---|---|
| POST | `/api/auth/register/` | Register a new customer account | Public |
| POST | `/api/auth/login/` | Obtain JWT access/refresh tokens | Public |
| POST | `/api/auth/login/refresh/` | Refresh access token | Public (with refresh token) |
| GET | `/api/auth/me/` | Current authenticated user profile | Authenticated |

### Loan workflow (`/api/loans/`)

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | `/api/loans/` | List applications (customer: own only, officer: all) | Authenticated |
| POST | `/api/loans/` | Create loan enquiry (`amount`, `tenure_months`) | Customer |
| GET | `/api/loans/dashboard/` | Status-count dashboard payload | Officer |
| GET | `/api/loans/{application_id}/` | Get full application detail with documents + timeline | Customer(owner) / Officer |
| POST | `/api/loans/{application_id}/documents/` | Upload/replace required document | Customer(owner) |
| POST | `/api/loans/{application_id}/documents/{document_id}/verify/` | Verify or reject document (`status`, optional `reason`) | Officer |
| POST | `/api/loans/{application_id}/decision/` | Approve/reject application (`decision`, optional `reason`) | Officer |
| POST | `/api/loans/{application_id}/disburse/` | Mark approved application as disbursed | Officer |

## Data model overview

- **User (`accounts.User`)**
  - Extends Django `AbstractUser` with role enum: `customer` or `officer`.
- **LoanApplication (`loans.LoanApplication`)**
  - Belongs to one customer (`User`).
  - Stores amount, tenure, status, rejection reason, timestamps.
  - Has many documents and timeline events.
- **LoanDocument (`loans.LoanDocument`)**
  - Belongs to one application.
  - Types: `id_proof`, `income_proof`, `address_proof`.
  - Statuses: `pending`, `verified`, `rejected`.
  - Includes `verified_by` officer reference and optional rejection reason.
  - Enforces **one-document-per-type-per-application** via unique constraint (`one_document_per_type`).
- **ApplicationTimeline (`loans.ApplicationTimeline`)**
  - Belongs to one application.
  - Records status-linked events (`message`, `actor`, timestamp) as audit trail.

## Security and business rules

- Public registration is restricted to **customers**; officer creation is intentionally blocked in public API.
- Officers should be created through Django admin or Django shell.
- API defaults to `IsAuthenticated`; only explicit public endpoints are open.
- Role permissions enforce customer/officer actions (`IsCustomer`, `IsOfficer`).
- Approval gate: all three required document types must be verified before approval.
- Disbursement gate: only approved applications can be disbursed.
- If local development/demo credentials exist in your local DB, treat them as **development-only** and change/remove them outside local use.

## Local setup

This project runs fully local with no required external services.

- Database: SQLite (`db.sqlite3`)
- File storage: local filesystem (`media/`)
- No PostgreSQL, Supabase, cloud storage, or other cloud dependency is required for local execution.

### Environment variables (`.env`)

Copy from `.env.example`:

```env
SECRET_KEY=any-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Windows PowerShell

```powershell
cd "<path-to>\loan-tracker-full-stack"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py runserver
```

In a second PowerShell window:

```powershell
cd "<path-to>\loan-tracker-full-stack"
python -m http.server 5173 --directory frontend
```

Open:

- Frontend: `http://127.0.0.1:5173/`
- API: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

### Short cross-platform equivalent (macOS/Linux)

```bash
cd /path/to/loan-tracker-full-stack
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
# separate terminal:
python -m http.server 5173 --directory frontend
```

## Verification commands

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Quick auth-protection check (expect 401 when unauthenticated):

```bash
curl -i http://127.0.0.1:8000/api/loans/
```

## Manual smoke-test flow

1. Register customer via UI or `POST /api/auth/register/`.
2. Login and create application (`amount`, `tenure_months`).
3. Upload `id_proof`, `income_proof`, `address_proof`.
4. Login as officer and verify/reject documents.
5. If any document is rejected, login as customer and replace only rejected type.
6. Verify all three documents; approve application.
7. Disburse approved application.
8. Confirm timeline entries and officer status counts.

## Tech stack

- Python
- Django **5.2.17**
- Django REST Framework **3.18.1**
- Simple JWT (`djangorestframework-simplejwt`) **5.5.1**
- `django-cors-headers` **4.9.0**
- `python-dotenv` **1.2.3**
- SQLite
- Vanilla HTML/CSS/JavaScript frontend
