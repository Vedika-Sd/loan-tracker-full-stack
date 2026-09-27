# LoanFlow — Personal Loan Tracker

LoanFlow is a full-stack personal-loan workflow application that helps customers and loan officers manage the complete loan journey from enquiry to disbursement — replacing scattered emails, manual document tracking, and unclear status updates with one structured, role-based workspace.

---

## Demo
<img width="1269" height="575" alt="image" src="https://github.com/user-attachments/assets/b4159cdf-9798-4e65-9907-9b530e3f86ad" />
<img width="1366" height="689" alt="image" src="https://github.com/user-attachments/assets/5515259c-d065-4e27-bb0b-3527cb9d3214" />
<img width="1297" height="612" alt="image" src="https://github.com/user-attachments/assets/fadbf99a-a927-4264-b78d-422966ebc358" />



## Business Problem

Personal-loan processing is often fragmented:

- Requests and documents pass through email, chat apps, or physical copies.
- Officers manually track which documents have arrived and been verified.
- Customers lack visibility into application status.
- Rejected documents require ad-hoc resubmission.
- Approvals can happen before every document is properly reviewed.
- There's no clear audit trail of who did what, and when.

This leads to delays, repeated back-and-forth, and a higher risk of incomplete or incorrectly processed applications.

## Solution

LoanFlow gives customers and officers one controlled workspace, split by role:

**Customer** — register, sign in (JWT), submit a loan enquiry (amount + tenure), upload ID/income/address proof, replace rejected documents, and track status and timeline.

**Loan Officer** — sign in to an officer workspace, view applications across all customers, verify or reject documents with reasons, approve/reject applications, and mark approved loans as disbursed.

Public registration is restricted to customers — officer accounts are provisioned via Django admin or the shell.

---

## Loan Processing Pipeline

```text
Registration → JWT login → Loan enquiry submitted → Documents uploaded
      → Officer reviews documents → verified ──────────────┐
                                   → rejected → customer    │
                                      replaces → re-review ─┘
      → Approval or rejection → (if approved) → Disbursed
```

**Key workflow rules:**

- Each application needs exactly three document types: `id_proof`, `income_proof`, `address_proof` (enforced via a unique constraint on `application + document_type`).
- Files are stored locally under `media/<user_id>/<application_id>/<uuid-filename>` and start as `pending`.
- Once all three document types are uploaded, the application moves to `documents_submitted`.
- A rejected document can be replaced by the customer; on replacement, its status resets to `pending`, the rejection reason and verifying officer are cleared, and it must be reviewed again.
- Approval is blocked unless **all three** document types are `verified`.
- Only an `approved` application can be disbursed.
- Every meaningful action (submission, verification, decision, disbursement) writes an entry to the application timeline.

## Application Status Lifecycle

| Status | Meaning |
|---|---|
| `enquiry` | Customer created a loan enquiry. |
| `documents_submitted` | All required document types uploaded. |
| `documents_rejected` | At least one document was rejected. |
| `approved` | Officer approved after verifying all documents. |
| `rejected` | Officer rejected the application. |
| `disbursed` | Approved loan marked as disbursed. |

Status transitions are enforced entirely in the backend, so they can't be bypassed by calling the API directly.

## Timeline / Audit Trail

Every important event (enquiry submitted, documents uploaded, each document verified/rejected, decision made, disbursement) is recorded in `ApplicationTimeline` with the status at that time, a human-readable message, the acting user, and a timestamp — giving both roles a full chronological history per application.

---

## Architecture

```text
Browser → Frontend (static HTML/CSS/JS, :5173)
            │  REST calls with JWT Bearer token, multipart uploads
            ▼
        Django REST API (:8000)
            │  Auth & roles · workflow validation · documents · timeline
            ▼
        SQLite (db.sqlite3)  +  local file storage (media/)
```

- **Frontend** (`frontend/`) — vanilla HTML/CSS/JS using `fetch`, storing the JWT session in `localStorage`. Renders a customer dashboard or an officer console based on role.
- **Backend** (`core/`, `accounts/`, `loans/`) — Django project handling authentication, authorization, validation, persistence, workflow rules, and file storage.

## Project Structure

```text
loan-tracker-full-stack/
├── accounts/        # custom user model, roles, auth endpoints
├── core/             # settings, urls, asgi/wsgi
├── loans/            # applications, documents, timeline, workflow views
├── frontend/          # index.html, app.js, styles.css
├── manage.py
├── requirements.txt
├── .env.example
├── db.sqlite3
└── media/
```

## Data Model (summary)

- **User** (`accounts.User`, extends `AbstractUser`): username, email, password, `role` (`customer` / `officer`).
- **LoanApplication**: customer, amount, tenure (months), status, rejection reason, timestamps.
- **LoanDocument**: application, document type, filename, storage path, content type, verification status, rejection reason, verifying officer, timestamps. One document per type per application.
- **ApplicationTimeline**: application, status at event time, message, actor, timestamp — ordered oldest to newest.

---

## API Reference

Base URL: `http://127.0.0.1:8000/api`. Protected routes require `Authorization: Bearer <access-token>`.

### Auth

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/auth/register/` | Public | Register a customer (officer registration is rejected here). |
| POST | `/auth/login/` | Public | Get access + refresh JWT tokens. |
| POST | `/auth/login/refresh/` | Public | Refresh an expired access token. |
| GET | `/auth/me/` | Authenticated | Current user profile and role. |

### Loans

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/loans/` | Authenticated | Customer's own apps, or all apps for officers. |
| POST | `/loans/` | Customer | Create a loan enquiry (`amount`, `tenure_months`). |
| GET | `/loans/dashboard/` | Officer | Application counts by status. |
| GET | `/loans/<id>/` | Customer/Officer | One application + documents + timeline. |
| POST | `/loans/<id>/documents/` | Customer | Upload/replace a document (multipart: `document_type`, `file`). |
| POST | `/loans/<id>/documents/<doc_id>/verify/` | Officer | `{"status": "verified"}` or `{"status": "rejected", "reason": "..."}`. |
| POST | `/loans/<id>/decision/` | Officer | `{"decision": "approve"}` or `{"decision": "reject", "reason": "..."}`. |
| POST | `/loans/<id>/disburse/` | Officer | Mark an approved application as disbursed. |

---

## Tech Stack

**Backend:** Python, Django 5.2.17, Django REST Framework 3.18.1, djangorestframework-simplejwt 5.5.1, django-cors-headers 4.9.0, python-dotenv 1.2.3
**Frontend:** HTML5, CSS3, vanilla JavaScript, Fetch API, `localStorage`
**Persistence:** SQLite (`db.sqlite3`) + local file storage (`media/`)

This project runs entirely locally — no external database, cloud storage, or third-party service is required.

---

## Local Setup

**Requirements:** Python 3.10+, Git, a modern browser (no Node.js needed — frontend is plain HTML/CSS/JS).

### Windows (PowerShell)

```powershell
git clone https://github.com/Vedika-Sd/loan-tracker-full-stack.git
cd loan-tracker-full-stack
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000/`.

### Start the frontend (separate terminal)

```bash
python -m http.server 5173 --directory frontend
```

Open `http://127.0.0.1:5173/`. The frontend calls the API at `http://127.0.0.1:8000/api`; CORS is configured to allow `http://localhost:5173` and `http://127.0.0.1:5173`.

### Create an officer account

Public registration only creates customers. To create an officer:

```powershell
python manage.py createsuperuser
```

Then open `http://127.0.0.1:8000/admin/`, edit the user, and set `role = officer`.

> Any demo credentials used locally are for development only — never reuse them in a real deployment.

### Verification

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Tests cover registration/login, role restrictions, document upload/rejection/replacement, the full approval → disbursement flow, and timeline creation.

---

## Manual Smoke Test

1. Open the frontend, register a customer, and sign in.
2. Create a loan enquiry and upload all three documents.
3. Confirm status becomes `documents_submitted`.
4. Sign in as an officer, verify each document.
5. Confirm approval is blocked until all are verified, then approve.
6. Disburse the application and confirm the final status is `disbursed`.
7. Review the timeline.

To test rejection: reject a document as officer → replace it as customer (status returns to `pending`) → re-verify as officer → continue the flow.

---

## Environment Variables

```dotenv
SECRET_KEY=change-this-value
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```
---
