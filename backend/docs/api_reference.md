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


### POST lists

Authorization: Bearer <access_token>

JSON Body:
{
  "title": "Test List"
}

Response (201 OK)
{
    "_id": "68a2686b4a39319087b95936",
    "title": "Test List",
    "owner_id": "6872aa4e80f5c2f731f9a62b",
    "items": [],
    "shared_with": [],
    "created_at": "2025-08-17T23:40:27.497486",
    "updated_at": "2025-08-17T23:40:27.497486"
}

### POST items/<list_id>

Authorization: Bearer <access_token>

JSON Body:
{
  "name": "Bananas",
  "quantity": 6,
  "unit": "pcs"
}

Response (200 OK)
{
    "_id": "68a268d04a39319087b95937",
    "name": "Bananas",
    "quantity": 6,
    "unit": "pcs",
    "list_id": "68a2686b4a39319087b95936",
    "created_at": "2025-08-17T23:42:08.420764",
    "updated_at": "2025-08-17T23:42:08.420766"
}