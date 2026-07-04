# 🛒 Listalicious Backend

**Listalicious** is a collaborative grocery list backend built with **FastAPI** and **MongoDB**. It supports authenticated list and item management, sharing, invites, and secure session handling.

---

## 🚀 Key Features

- 📝 Create and manage grocery lists and items
- 👥 Share lists with collaborators
- 🔐 JWT authentication, email verification, and session revocation
- 📦 MongoDB for flexible document storage
- 🩺 `/health` and `/ready` endpoints for liveness and readiness checks
- 🐳 Docker Compose support for local development
- 📄 OpenAPI docs at `/v1/docs`

---

## 📁 Project Structure

```
listalicious-backend/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
├── .venv/                    # Local Python virtual environment
├── requirements.txt          # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── run.sh
├── README.md
```

---

## ⚙️ Running the app locally

### Option 1 — Python local development

1. Create and activate the virtual environment:
```bash
python -m venv .venv
source .venv/Scripts/activate
```

2. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Copy the example env file:
```bash
cp .env.example .env
```

4. Update `.env` with your values. At minimum:
```env
MONGO_URI=mongodb://localhost:27017/listalicious
MONGO_DB_NAME=listalicious
JWT_SECRET=replace-me-with-a-long-random-secret
ALLOWED_ORIGINS=http://localhost:3000
APP_URL=http://localhost:3000
EMAIL_FROM=no-reply@example.com
```

5. Start the app:
```bash
./run.sh
```

6. Open the API docs:

`http://127.0.0.1:8000/v1/docs`

---

## 🐳 Running with Docker Compose

This repo supports a Docker Compose workflow for local development.

1. Make sure Docker Desktop is running.

2. Build the app image once:
```bash
docker build -t listalicious-app .
```

3. Start the stack:
```bash
docker compose up --no-build -d
```

4. Verify the services:
```bash
docker compose ps
```

5. View the API docs:

`http://127.0.0.1:8000/v1/docs`

### Notes
- The app service uses `MONGO_URI=mongodb://mongo:27017/listalicious` when running via Compose.
- If `docker compose up --build` fails on Windows, the above manual build plus `docker compose up --no-build -d` is the recommended workaround.
- To stop and remove containers and volumes:
```bash
docker compose down -v
```

---

## 📄 Environment variables

Use `.env.example` as the source of truth. The backend currently reads:
- `MONGO_URI`
- `MONGO_DB_NAME`
- `JWT_SECRET`
- `ALLOWED_ORIGINS`
- `APP_URL`
- `SENDGRID_API_KEY`
- `EMAIL_FROM`
- `ENV`

> The app requires `JWT_SECRET` and `ALLOWED_ORIGINS` in production mode.

---

## 🧪 Testing

Run the test suite:
```bash
pytest -q
```

---

## 📦 API docs

- OpenAPI docs: `http://127.0.0.1:8000/v1/docs`
- Additional API reference: `backend/docs/api_reference.md`

---

## 📚 Developer docs

- Developer onboarding: `DEVELOPMENT.md`
- Contributor guide: `CONTRIBUTING.md`
- Deployment guide: `DEPLOYMENT.md`
- API examples: `API_EXAMPLES.md`
- Architecture overview: `ARCHITECTURE.md`
- API reference: `backend/docs/api_reference.md`

---

## ✅ Current status

- Docker Compose development is supported
- Local Python development is supported
- Health, readiness, and metrics endpoints are implemented
- The app is ready for local or containerized testing

---

## 📬 Contact

Made with 💻 by Ryan Alfa  
[GitHub: @ryanalfa94](https://github.com/ryanalfa94)
