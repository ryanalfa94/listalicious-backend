## 🔐 Auth APIs

### POST /auth/register
- Registers a new user.
- Request Body:
json
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

## Lists API 

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


### GET /lists

Returns all grocery lists owned by the authenticated user.
Authorization: Bearer <access_token>

Response (200 OK):
[
  {
    "_id": "68a260e6d44a93c87b3d2492",
    "title": "Weekly Costco Run",
    "owner_id": "6872aa4e80f5c2f731f9a62b",
    "items": [],
    "shared_with": [],
    "created_at": "2025-08-17T23:08:22.756000",
    "updated_at": "2025-08-17T23:08:22.756000"
  }
]


### GET /lists/{list_id}

Returns a single list.

Guarded by ownership (ensure_list_owned).

Authorization: Bearer <access_token>

Path Params

list_id (string)

Response (200 OK):
{
  "_id": "68a260e6d44a93c87b3d2492",
  "title": "Weekly Costco Run",
  "owner_id": "6872aa4e80f5c2f731f9a62b",
  "items": [],
  "shared_with": [],
  "created_at": "2025-08-17T23:08:22.756000",
  "updated_at": "2025-08-17T23:08:22.756000"
}

### PUT /lists/{list_id}

Partial update supported. Only fields you include are updated (payload.model_dump(exclude_unset=True)).

Typical updatable fields: title, items, shared_with.

Authorization: Bearer <access_token>

Path Params

list_id (string)

Request Body (JSON) - Update 1 or more fields at a time:
{
  "title": "Costco + Target",
}

Response (200 OK):
{
  "_id": "68a260e6d44a93c87b3d2492",
  "title": "Costco + Target",
  "owner_id": "6872aa4e80f5c2f731f9a62b",
  "items": ["paper towels", "dish soap"],
  "shared_with": [],
  "created_at": "2025-08-17T23:08:22.756000",
  "updated_at": "2025-08-18T23:23:43.093000"
}


### DELETE /lists/{list_id}

Deletes a list you own.

Authorization: Bearer <access_token>

Path Params

list_id (string)

Response (204 No Content):

(no body)



### Share List (Add Contributor)

POST /lists/{list_id}/share

Request (JSON)

{ "email": "contributor@example.com" }


200 OK

{
  "list_id": "68a260e6d44a93c87b3d2492",
  "shared_with": ["6872aa4e80f5c2f731f9a62b"]
}


### Unshare List (Remove Contributor)

POST /lists/{list_id}/unshare

Request (JSON)

{ "email": "contributor@example.com" }


200 OK

{
  "list_id": "68a260e6d44a93c87b3d2492",
  "shared_with": []
}

## Item APIs

### List Items

GET /lists/{list_id}/items

200 OK

[
  {
    "_id": "66f0c9f1a2...",
    "name": "Bananas",
    "quantity": 6,
    "unit": "pcs",
    "note": "ripe pls",
    "is_checked": false,
    "list_id": "68a260e6d44a93c87b3d2492",
    "created_at": "2025-08-18T00:00:00Z",
    "updated_at": "2025-08-18T00:00:00Z"
  }
]

### Create Item

POST /lists/{list_id}/items

Request (JSON)

{
  "name": "Paper Towels",
  "quantity": 2,
  "unit": "pack",
  "note": "Kirkland if possible",
  "is_checked": false
}


201 Created

{
  "_id": "66f0cab3d1...",
  "name": "Paper Towels",
  "quantity": 2,
  "unit": "pack",
  "note": "Kirkland if possible",
  "is_checked": false,
  "list_id": "68a260e6d44a93c87b3d2492",
  "created_at": "2025-08-18T00:05:00Z",
  "updated_at": "2025-08-18T00:05:00Z"
}



### Update Item

PUT /lists/{list_id}/items/{item_id}

Request (JSON) — any subset of fields

{
  "name": "Paper Towels",
  "quantity": 3,
  "is_checked": true,
  "note": "any brand ok"
}


200 OK

{
  "_id": "66f0cab3d1...",
  "name": "Paper Towels",
  "quantity": 3,
  "unit": "pack",
  "note": "any brand ok",
  "is_checked": true,
  "list_id": "68a260e6d44a93c87b3d2492",
  "created_at": "2025-08-18T00:05:00Z",
  "updated_at": "2025-08-18T00:10:30Z"
}



### Delete Item

DELETE /lists/{list_id}/items/{item_id}

204 No Content