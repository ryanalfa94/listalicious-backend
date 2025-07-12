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
