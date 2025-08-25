# 🛒 Listalicious Backend

**Listalicious** is a smart, intuitive grocery list management app designed for seamless collaboration among busy households or groups. This is the backend component built using **FastAPI** and **MongoDB**, built to support mobile clients such as React Native.

---

## 🚀 Features

- 📝 Create and manage grocery lists
- 👨‍👩‍👧‍👦 Collaborate and share lists in real-time
- 📦 MongoDB for flexible data storage
- ⚡ FastAPI for blazing fast REST API performance
- 🔒 Environment-safe with `.env` file support

---

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI (Python)
- **Database:** MongoDB Atlas (Free Tier)
- **Deployment:** Ready for Render.com or Railway
- **Auth (Optional):** Firebase Auth or custom token-based system

---

## 📁 Project Structure

```
listalicious-backend/
├── backend/
│   ├── main.py               # Entry point for FastAPI app
│   ├── schemas/              # Pydantic schemas for request & response validation (API input/output).
│   ├── routes/               # API route files (e.g., groceries.py, users.py)
│   ├── models/               # Pydantic models
│   └── database.py           # MongoDB connection setup
├── requirements.txt          # Python dependencies
├── .gitignore
└── README.md
```

---

## ⚙️ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/ryanalfa94/listalicious-backend.git
cd listalicious-backend
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/listalicious?retryWrites=true&w=majority
DB_NAME=listalicious
```

### 5. Run the server
```bash
uvicorn backend.main:app --reload
```

Go to `http://127.0.0.1:8000/docs` to explore the Swagger API docs.

---
## Docker and Mango

🐳 Running MongoDB with Docker (Optional Local Setup)
If you're working locally and prefer not to install MongoDB manually, you can spin it up with Docker:

1. Make sure Docker is installed
Install Docker Desktop and ensure it's running.

2. Start a MongoDB container
docker run -d \
  --name listalicious-mongo \
  -p 27017:27017 \
  -v listalicious_data:/data/db \
  mongo

This command:
Runs MongoDB in the background
Makes it available on localhost:27017
Persists data with a named volume (listalicious_data)

3. Update your .env for local use
MONGO_URI=mongodb://localhost:27017/listalicious
DB_NAME=listalicious

4. Verify the container is running
docker ps

if container is not running, you can run it manually by clicking on the start button inside the docker application. 

You should see a container named listalicious-mongo. You're ready to run the backend!

---
## Testing 
Optionally use Swagger docs
If you want to test things easily:

Visit: http://localhost:8000/docs

or Postman

---

## 📬 Contact

Made with 💻 by Ryan Alfa  
[GitHub: @ryanalfa94](https://github.com/ryanalfa94)
