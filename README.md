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

## ☁️ Deployment

You can deploy this backend for free using:

- [Render.com](https://render.com)
- [Railway.app](https://railway.app)
- [Deta.sh](https://deta.space)

Just make sure to set your environment variables (`MONGO_URI`, `DB_NAME`) in the platform settings.

---

## 🤝 Collaborators

To add or manage collaborators, go to the GitHub repo → Settings → Collaborators.

---

## 📅 Last Updated
May 19, 2025

---

## 🔮 Future Enhancements

- ✅ User authentication (via Firebase or OAuth)
- 🤖 AI-based smart grocery suggestions
- 🔔 Notification system
- 📤 Export lists or sync to cloud drives

---

## 📬 Contact

Made with 💻 by Ryan Alfa  
[GitHub: @ryanalfa94](https://github.com/ryanalfa94)
