## 🔐 Auth APIs

### POST /auth/register
- Registers a new user.
- Request Body:
```json
{
  "email": "user@example.com",
  "password": "secure123",
  "username": "user"
}

Response:
{
  "message": "User registered successfully"
}


### POST /auth/login
- Request Type
- application/x-www-form-urlencoded

Note: username here refers to the user's email.

Sample Form Submission (raw):
username=user@example.com
password=secure123
grant_type=password

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}



### GET /auth/me

Authorization: Bearer <access_token>

Response (200 OK)
{
  "email": "user@example.com",
  "username": "user",
  "_id": "60d9f9fa2e35a90012345678",
  "created_at": "2024-07-12T12:34:56.789Z",
  "updated_at": "2024-07-12T12:34:56.789Z"
}