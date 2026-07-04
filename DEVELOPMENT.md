# Development Guide

This document describes how developers should run, test, and work with the Listalicious backend.

## Local development

### 1. Clone the repo

```bash
git clone https://github.com/ryanalfa94/listalicious-backend.git
cd listalicious-backend
```

### 2. Create and activate the Python virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Update `.env` with the required values.

Minimum values for local development:

```env
MONGO_URI=mongodb://localhost:27017/listalicious
MONGO_DB_NAME=listalicious
JWT_SECRET=replace-me-with-a-long-random-secret
ALLOWED_ORIGINS=http://localhost:3000
APP_URL=http://localhost:3000
EMAIL_FROM=no-reply@example.com
ENV=dev
```

> In production, `JWT_SECRET` must be long and random, and `ALLOWED_ORIGINS` must be set to the true frontend origin.

### 5. Run the app locally

```bash
./run.sh
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/health`
- Readiness: `http://127.0.0.1:8000/ready`

---

## Docker development

### 1. Make sure Docker Desktop is running

Docker Desktop must be started before running Compose.

### 2. Build the app image

```bash
docker build -t listalicious-app .
```

### 3. Start the stack

```bash
docker compose up --no-build -d
```

### 4. Verify status

```bash
docker compose ps
```

### 5. Stop and remove the stack

```bash
docker compose down -v
```

### Notes

- The compose service uses `MONGO_URI=mongodb://mongo:27017/listalicious` inside the Docker network.
- If `docker compose up --build` fails on Windows, use the manual image build step above.

---

## Testing

Run the test suite:

```bash
pytest -q
```

Run a specific test file:

```bash
pytest -q tests/test_auth.py
```

---

## API documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`
- Static API reference: `backend/docs/api_reference.md`

## Account and moderation notes

- Password recovery is available via `POST /v1/auth/forgot-password` and `POST /v1/auth/reset-password`.
- Admin moderation is available via `GET /v1/admin/users` and `PATCH /v1/admin/users/{user_id}/status`.
- Registration and login responses now include onboarding guidance and whether email verification is still required.

---

## Recommended docs additions

These are useful next steps for documentation:

- `CONTRIBUTING.md` for development conventions and PR process
- `DEPLOYMENT.md` for production deployment and environment hardening
- `ARCHITECTURE.md` for high-level data and service flow
- `API_EXAMPLES.md` for sample request/response usage
