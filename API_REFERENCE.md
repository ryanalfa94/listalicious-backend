# Listalicious API Reference

**Base URL:** `http://localhost:8000/v1`  
**Interactive docs (Swagger UI):** `http://localhost:8000/v1/docs`  
**OpenAPI schema:** `http://localhost:8000/v1/openapi.json`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Conventions](#conventions)
3. [Authentication](#authentication)
4. [Common Flows](#common-flows)
5. [Endpoints — Auth](#endpoints--auth)
6. [Endpoints — Email Verification](#endpoints--email-verification)
7. [Endpoints — Users](#endpoints--users)
8. [Endpoints — Lists](#endpoints--lists)
9. [Endpoints — Items](#endpoints--items)
10. [Error Reference](#error-reference)
11. [Rate Limits](#rate-limits)
12. [TypeScript Types](#typescript-types)

---

## Quick Start

### 1. Run the server
```bash
# from repo root
wsl bash -c "source venv/bin/activate && uvicorn backend.app.main:app --reload"
```

### 2. Register and get a token
```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Password1"}'
```

### 3. Use the token
```bash
curl http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Conventions

### Base URL
All endpoints are prefixed with `/v1`.

### Request headers
Send these on every request:

| Header | Value | When |
|---|---|---|
| `Content-Type` | `application/json` | All POST/PUT/PATCH with a body |
| `Authorization` | `Bearer <access_token>` | All 🔒 protected endpoints |
| `X-Request-ID` | any string | Optional — echoed back in response headers for tracing |

**Exception:** `POST /auth/login` uses `application/x-www-form-urlencoded` (OAuth2 standard).

### Dates
All timestamps are **UTC ISO 8601** strings: `"2024-01-15T10:30:00"`.  
No timezone suffix is included — treat all values as UTC.

### IDs
All IDs are **MongoDB ObjectId strings** — 24-character hex strings, e.g. `"64a1b2c3d4e5f6a7b8c9d0e1"`.

### Auth guard icons
- 🔒 — requires `Authorization: Bearer <token>`
- ⚠️ — additionally requires verified email (returns `403` otherwise)

---

## Authentication

### How tokens work

| Token | Lifetime | Purpose |
|---|---|---|
| `access_token` | 60 min (configurable) | Sent on every protected request |
| `refresh_token` | 30 days | Exchange for a new access token when it expires |

**Token invalidation** — all tokens for an account are immediately invalidated when:
- The user calls `POST /auth/logout-all`
- The user changes their password
- The user resets their password
- The user confirms an email change
- The user deletes their account

### Token refresh cycle
When a request returns `401`, refresh before retrying:

```
Request → 401
  ↓
POST /auth/refresh  { refresh_token }
  ↓
New access_token + refresh_token
  ↓
Retry original request with new access_token
```

If the refresh also returns `401`, the refresh token is expired or invalidated — send the user to the login screen.

### Token storage recommendations
- **`access_token`** — store in memory (React state, Zustand, etc.). Never in `localStorage`.
- **`refresh_token`** — store in an `HttpOnly` secure cookie so JavaScript cannot read it.

---

## Common Flows

### Registration & email verification
```
1. POST /auth/register               → get access_token + refresh_token
2. POST /auth/request-email-verification  → email sent to user
3. User clicks link → frontend extracts token from URL
4. POST /auth/verify-email  { token }     → email_verified becomes true
5. POST /lists  { title }                 → now allowed (requires verified email)
```

### Login & token refresh
```
1. POST /auth/login  (form-encoded)     → access_token + refresh_token
2. ... make requests with access_token ...
3. Any request returns 401
4. POST /auth/refresh  { refresh_token }  → new access_token + refresh_token
5. Retry original request
6. POST /auth/logout                      → revokes current session
```

### Share a list via invite link
```
1. POST /lists/{id}/invite              → { invite_token, expires_at }
2. Build URL: https://yourapp.com/join/<invite_token>
3. Share URL with recipient
4. Recipient opens URL (must be logged in)
5. POST /lists/join/<invite_token>      → recipient added as collaborator
```

### Share a list directly by email
```
1. GET /users/search?q=alice            → find user's id
2. POST /lists/{id}/share  { email }    → adds collaborator
3. GET /lists/{id}/shared-users         → confirm collaborators
4. POST /lists/{id}/unshare  { email }  → remove collaborator later
```

### Shopping trip flow
```
1. POST /lists  { title: "Weekly shop" }
2. POST /lists/{id}/items/bulk  { items: [...] }   → add all items at once
3. GET  /lists/{id}/items                           → load items (sorted by position)
4. PATCH /lists/{id}/items/{item_id}/check          → check off as you shop
5. GET  /lists/{id}/stats                           → see progress (checked/total)
6. DELETE /lists/{id}/items/checked                 → clear bought items when done
```

### Password reset (logged out)
```
1. POST /auth/forgot-password  { email }   → email sent (always 204, no enumeration)
2. User clicks link → frontend extracts token from URL
3. POST /auth/reset-password  { token, new_password, confirm_new_password }
4. All sessions invalidated — user must log in again
```

---

## Endpoints — Auth

### Register
`POST /auth/register` · Rate limit: **5/min**

**Body**
```json
{
  "email": "user@example.com",
  "password": "Password1",
  "username": "ryan"
}
```
| Field | Type | Required | Rules |
|---|---|---|---|
| `email` | string | yes | valid email |
| `password` | string | yes | min 8, max 128 chars, ≥1 letter, ≥1 digit |
| `username` | string | no | max 50 chars |

**Response `201`**
```json
{
  "user": {
    "_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "email": "user@example.com",
    "username": "ryan",
    "email_verified": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

---

### Login
`POST /auth/login` · Rate limit: **10/min**  
Uses `application/x-www-form-urlencoded` (OAuth2 standard — the field is `username` but pass the email).

**Body (form-encoded)**
```
username=user@example.com&password=Password1
```

**Response `200`** — same shape as Register.

---

### Refresh Tokens
`POST /auth/refresh` · Rate limit: **60/min** · No auth header needed

**Body**
```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiJ9..." }
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### Get Current User
`GET /auth/me` 🔒

**Response `200`**
```json
{
  "_id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "email": "user@example.com",
  "username": "ryan",
  "email_verified": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

---

### Update Profile
`PATCH /auth/me` 🔒  
Send only the fields you want to update. Unknown fields return `422`.

**Body**
```json
{ "username": "new_username" }
```

**Response `200`** — same shape as Get Current User.

---

### Change Password
`POST /auth/change-password` 🔒  
Invalidates all sessions. New password must differ from the current one.

**Body**
```json
{
  "current_password": "OldPass1",
  "new_password": "NewPass2",
  "confirm_new_password": "NewPass2"
}
```
| Field | Required | Notes |
|---|---|---|
| `current_password` | yes | |
| `new_password` | yes | min 8 chars, ≥1 letter, ≥1 digit |
| `confirm_new_password` | no | if provided, must match `new_password` |

**Response `204`**

---

### Change Email
`POST /auth/change-email` 🔒 · Rate limit: **3/min**  
Sends a verification link to the **new** address. The change is not applied until confirmed. Previous pending changes are invalidated.

**Body**
```json
{
  "new_email": "newemail@example.com",
  "password": "CurrentPass1"
}
```

**Response `204`**

---

### Confirm Email Change
`POST /auth/confirm-email-change` · No auth required  
Token comes from the link sent to the new email. Invalidates all sessions.

**Body**
```json
{ "token": "<token_from_email_link>" }
```

**Response `204`**

---

### List Sessions
`GET /auth/sessions` 🔒  
Returns all active (non-expired, non-revoked) sessions. One entry per successful login or token refresh.

**Response `200`**
```json
[
  {
    "jti": "abc123def456...",
    "created_at": "2024-01-01T10:00:00",
    "expires_at": "2024-01-01T11:00:00"
  }
]
```

---

### Revoke Session
`DELETE /auth/sessions/{jti}` 🔒  
Remotely log out a specific device. Get the `jti` from `GET /auth/sessions`.

**Response `204`**

---

### Logout (current device)
`POST /auth/logout` 🔒  
Revokes the current token only. Other sessions stay active.

**Response `204`**

---

### Logout All Devices
`POST /auth/logout-all` 🔒  
Immediately invalidates all tokens for this account.

**Response `204`**

---

### Delete Account
`DELETE /auth/delete-account` 🔒  
Permanently deletes the account and all associated data: owned lists, all items in those lists, and removes the user from any shared lists. Cannot be undone.

**Response `204`**

---

## Endpoints — Email Verification

### Request Verification Email
`POST /auth/request-email-verification` 🔒 · Rate limit: **3/min**  
Silent no-op if already verified or called within 60 seconds of the last request. Previous unused tokens are invalidated.

**Response `204`**

---

### Verify Email
`POST /auth/verify-email` · Rate limit: **10/min** · No auth required

**Body**
```json
{ "token": "<token_from_email_link>" }
```

**Response `204`**

---

### Forgot Password
`POST /auth/forgot-password` · Rate limit: **3/min** · No auth required  
Always returns `204` regardless of whether the email exists (prevents enumeration).

**Body**
```json
{ "email": "user@example.com" }
```

**Response `204`**

---

### Reset Password
`POST /auth/reset-password` · Rate limit: **10/min** · No auth required  
One-time token from the email link. Invalidates all sessions.

**Body**
```json
{
  "token": "<token_from_email_link>",
  "new_password": "NewPass1",
  "confirm_new_password": "NewPass1"
}
```

**Response `204`**

---

## Endpoints — Users

### Search Users
`GET /users/search` 🔒 · Rate limit: **30/min**  
Case-insensitive search by email or username. Returns up to 20 results, excluding yourself. Use this to find who to share a list with before calling `POST /lists/{id}/share`.

**Query params**
| Param | Type | Required | Notes |
|---|---|---|---|
| `q` | string | yes | 1–100 chars |

**Response `200`**
```json
[
  {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "email": "alice@example.com",
    "username": "alice"
  }
]
```

---

## Endpoints — Lists

### Create List
`POST /lists` 🔒 ⚠️

**Body**
```json
{ "title": "Weekly Groceries" }
```
- `title` — 1–200 chars

**Response `201`**
```json
{
  "_id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "title": "Weekly Groceries",
  "owner_id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "shared_with": [],
  "archived": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

---

### Get My Lists
`GET /lists` 🔒  
Returns all lists you own or are shared on, sorted newest first. Excludes archived lists by default.

**Query params**
| Param | Type | Default | Notes |
|---|---|---|---|
| `skip` | int | `0` | Pagination offset |
| `limit` | int | `50` | 1–100 |
| `include_archived` | bool | `false` | Pass `true` to include archived lists |

**Response `200`** — array of list objects.

---

### Get Single List
`GET /lists/{list_id}` 🔒

**Response `200`** — single list object.

---

### Update List
`PUT /lists/{list_id}` 🔒 Owner only

**Body**
```json
{ "title": "New Title" }
```

**Response `200`** — updated list object.

---

### Delete List
`DELETE /lists/{list_id}` 🔒 Owner only  
Permanently deletes the list and all its items, activity logs, and invite links.

**Response `204`**

---

### Archive List
`PATCH /lists/{list_id}/archive` 🔒 Owner only  
Hides the list from `GET /lists` unless `include_archived=true` is passed.

**Response `204`**

---

### Unarchive List
`PATCH /lists/{list_id}/unarchive` 🔒 Owner only

**Response `204`**

---

### Leave List
`DELETE /lists/{list_id}/leave` 🔒 Collaborators only  
Remove yourself as a collaborator. Owners must delete the list instead.

**Response `204`**

**Error cases**
- `400` if you are the owner
- `400` if you are not a collaborator

---

### Duplicate List
`POST /lists/{list_id}/duplicate` 🔒 ⚠️  
Copies the list title and all **unchecked** items into a new list owned by you. The copy is not shared with anyone.

**Response `201`** — new list object with title `"<original title> (copy)"`.

---

### Get List Stats
`GET /lists/{list_id}/stats` 🔒

**Response `200`**
```json
{
  "total": 10,
  "checked": 4,
  "unchecked": 6
}
```

---

### Get Shared Users
`GET /lists/{list_id}/shared-users` 🔒

**Response `200`**
```json
[
  {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "email": "alice@example.com",
    "username": "alice"
  }
]
```

---

### Share List
`POST /lists/{list_id}/share` 🔒 Owner only  
The target user must already have a Listalicious account.

**Body**
```json
{ "email": "alice@example.com" }
```

**Response `200`**
```json
{
  "list_id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "shared_with": ["64a1b2c3...", "64a1b2c4..."]
}
```

---

### Unshare List
`POST /lists/{list_id}/unshare` 🔒 Owner only

**Body**
```json
{ "email": "alice@example.com" }
```

**Response `200`** — same shape as Share.

---

### Create Invite Link
`POST /lists/{list_id}/invite` 🔒 Owner only  
Generates a **single-use** token valid for 7 days. Anyone with the link who has an account can join.

**Response `200`**
```json
{
  "invite_token": "abc123xyz...",
  "expires_at": "2024-01-08T00:00:00"
}
```

Construct the shareable URL on the frontend:
```
https://yourapp.com/join/<invite_token>
```
When the user opens that URL, call `POST /lists/join/<invite_token>`.

---

### Join via Invite
`POST /lists/join/{token}` 🔒  
Accepts an invite and adds the authenticated user as a collaborator. Tokens are single-use.

**Response `204`**

**Error cases**
- `400` if the token is invalid, already used, or expired

---

### Get Activity Log
`GET /lists/{list_id}/activity` 🔒  
Paginated activity log for a list, newest first. Entries auto-delete after 90 days.

**Query params**
| Param | Type | Default | Notes |
|---|---|---|---|
| `skip` | int | `0` | Pagination offset |
| `limit` | int | `50` | 1–100 |

**Response `200`**
```json
[
  {
    "list_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "user_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "user_email": "user@example.com",
    "action": "item_added",
    "meta": { "item_id": "...", "item_name": "Milk" },
    "created_at": "2024-01-01T10:00:00"
  }
]
```

**All `action` values**
| Action | When |
|---|---|
| `item_added` | Item created |
| `item_checked` | Item checked |
| `item_unchecked` | Item unchecked |
| `item_deleted` | Item deleted |
| `items_cleared` | All checked items deleted |
| `items_bulk_added` | Bulk items added |
| `item_moved_in` | Item moved into this list |
| `item_moved_out` | Item moved out of this list |
| `list_shared` | List shared with a user |
| `list_unshared` | User removed from list |
| `joined_via_invite` | User joined via invite link |
| `collaborator_left` | Collaborator left the list |

---

## Endpoints — Items

All item endpoints are nested under a list: `/lists/{list_id}/items/...`

### Get Items
`GET /lists/{list_id}/items` 🔒  
Sorted by `position` ascending, then `created_at` ascending.

**Query params**
| Param | Type | Default | Notes |
|---|---|---|---|
| `skip` | int | `0` | Pagination offset |
| `limit` | int | `50` | 1–200 |
| `checked` | bool | *(omit)* | `true` = checked only · `false` = unchecked only · omit = all |

**Response `200`**
```json
[
  {
    "_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "name": "Milk",
    "quantity": 2,
    "unit": "L",
    "note": "Full fat",
    "is_checked": false,
    "list_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "position": 0,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

### Add Item
`POST /lists/{list_id}/items` 🔒 ⚠️

**Body**
```json
{
  "name": "Milk",
  "quantity": 2,
  "unit": "L",
  "note": "Full fat",
  "is_checked": false
}
```
| Field | Type | Required | Rules |
|---|---|---|---|
| `name` | string | yes | 1–200 chars |
| `quantity` | int | yes | 1–9999 |
| `unit` | string | no | max 50 chars |
| `note` | string | no | max 1000 chars |
| `is_checked` | bool | no | defaults to `false` |

**Response `201`** — item object.

---

### Bulk Add Items
`POST /lists/{list_id}/items/bulk` 🔒 ⚠️  
Add up to 50 items in a single request. Useful for pre-populating a list.

**Body**
```json
{
  "items": [
    { "name": "Milk", "quantity": 2, "unit": "L" },
    { "name": "Bread", "quantity": 1 },
    { "name": "Eggs", "quantity": 12, "note": "Free range" }
  ]
}
```

**Response `201`** — array of item objects in the same order.

---

### Update Item
`PUT /lists/{list_id}/items/{item_id}` 🔒  
Send only the fields you want to change.

**Body**
```json
{
  "name": "Oat Milk",
  "quantity": 3,
  "unit": "L",
  "note": "Barista edition",
  "is_checked": true
}
```

**Response `200`** — updated item object.

---

### Toggle Checked
`PATCH /lists/{list_id}/items/{item_id}/check` 🔒  
Flips `is_checked` — no body needed.

**Response `200`** — updated item object with the new `is_checked` value.

---

### Reorder Items
`PATCH /lists/{list_id}/items/reorder` 🔒  
Set the display order by sending item IDs in the desired sequence. Each item's `position` becomes its index in the array. Items not listed keep their current position.

**Body**
```json
{
  "order": [
    "64a1b2c3d4e5f6a7b8c9d0e1",
    "64a1b2c3d4e5f6a7b8c9d0e2",
    "64a1b2c3d4e5f6a7b8c9d0e3"
  ]
}
```

**Response `204`**

---

### Move Item to Another List
`PATCH /lists/{list_id}/items/{item_id}/move` 🔒  
You must have access to both the source and target lists.

**Body**
```json
{ "target_list_id": "64a1b2c3d4e5f6a7b8c9d0e9" }
```

**Response `200`** — updated item object with the new `list_id` and `position`.

---

### Clear Checked Items
`DELETE /lists/{list_id}/items/checked` 🔒  
Deletes all checked items from the list at once.

**Response `204`**

---

### Delete Item
`DELETE /lists/{list_id}/items/{item_id}` 🔒

**Response `204`**

---

## Error Reference

All errors return JSON:
```json
{ "detail": "Human-readable message here" }
```

### Status codes
| Code | Meaning | Common causes |
|---|---|---|
| `400` | Bad request | Wrong password, token already used, owner trying to leave list |
| `401` | Unauthorized | Missing token, expired token, revoked token |
| `403` | Forbidden | Email not verified, action requires owner role |
| `404` | Not found | List/item/session doesn't exist or you don't have access |
| `409` | Conflict | Email already in use (during email change confirmation) |
| `422` | Validation error | Invalid field value, missing required field |
| `429` | Rate limited | Too many requests — see [Rate Limits](#rate-limits) |
| `500` | Server error | Something unexpected — report to backend team |

### Validation error shape (422)
Pydantic validation errors return an array in `detail`:
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "abc",
      "ctx": { "min_length": 8 }
    }
  ]
}
```
Use `detail[].loc` to know which field failed, `detail[].msg` for the user-facing message.

### Rate limit exceeded (429)
```json
{ "detail": "Rate limit exceeded: 5 per 1 minute" }
```

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| `POST /auth/register` | 5 / minute |
| `POST /auth/login` | 10 / minute |
| `POST /auth/refresh` | 60 / minute |
| `POST /auth/change-email` | 3 / minute |
| `POST /auth/request-email-verification` | 3 / minute |
| `POST /auth/verify-email` | 10 / minute |
| `POST /auth/forgot-password` | 3 / minute |
| `POST /auth/reset-password` | 10 / minute |
| `POST /auth/confirm-email-change` | 10 / minute |
| `GET /users/search` | 30 / minute |
| All other endpoints | 200 / minute (global) |

Rate limits are per IP address. When exceeded the server returns `429`.

### Account lockout
After **10 consecutive failed login attempts**, the account is locked for **15 minutes**. Successful login resets the counter.

---

## TypeScript Types

Copy these into your frontend project for full type safety.

```typescript
// ── Shared ────────────────────────────────────────────────────────────────────

export type ISODateString = string; // "2024-01-01T00:00:00"
export type ObjectId = string;      // 24-char hex string

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  _id: ObjectId;
  email: string;
  username: string | null;
  email_verified: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface RegisterRequest {
  email: string;
  password: string;
  username?: string;
}

// Login uses application/x-www-form-urlencoded: username + password fields

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface UpdateProfileRequest {
  username?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_new_password?: string;
}

export interface ChangeEmailRequest {
  new_email: string;
  password: string;
}

export interface Session {
  jti: string;
  created_at: ISODateString;
  expires_at: ISODateString;
}

// ── Email Verification ────────────────────────────────────────────────────────

export interface TokenRequest {
  token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirm_new_password?: string;
}

// ── Users ─────────────────────────────────────────────────────────────────────

export interface UserSearchResult {
  id: ObjectId;
  email: string;
  username: string | null;
}

// ── Lists ─────────────────────────────────────────────────────────────────────

export interface GroceryList {
  _id: ObjectId;
  title: string;
  owner_id: ObjectId;
  shared_with: ObjectId[];
  archived: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface CreateListRequest {
  title: string;
}

export interface UpdateListRequest {
  title?: string;
}

export interface ListStats {
  total: number;
  checked: number;
  unchecked: number;
}

export interface SharedUser {
  id: ObjectId;
  email: string;
  username: string | null;
}

export interface ShareRequest {
  email: string;
}

export interface ShareResponse {
  list_id: ObjectId;
  shared_with: ObjectId[];
}

export interface InviteResponse {
  invite_token: string;
  expires_at: ISODateString;
}

export interface ActivityEntry {
  list_id: ObjectId;
  user_id: ObjectId;
  user_email: string;
  action:
    | "item_added"
    | "item_checked"
    | "item_unchecked"
    | "item_deleted"
    | "items_cleared"
    | "items_bulk_added"
    | "item_moved_in"
    | "item_moved_out"
    | "list_shared"
    | "list_unshared"
    | "joined_via_invite"
    | "collaborator_left";
  meta: Record<string, unknown>;
  created_at: ISODateString;
}

// ── Items ─────────────────────────────────────────────────────────────────────

export interface Item {
  _id: ObjectId;
  name: string;
  quantity: number;
  unit: string | null;
  note: string | null;
  is_checked: boolean;
  list_id: ObjectId;
  position: number | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface CreateItemRequest {
  name: string;
  quantity: number;
  unit?: string;
  note?: string;
  is_checked?: boolean;
}

export interface BulkCreateItemsRequest {
  items: CreateItemRequest[];
}

export interface UpdateItemRequest {
  name?: string;
  quantity?: number;
  unit?: string;
  note?: string;
  is_checked?: boolean;
}

export interface ReorderItemsRequest {
  order: ObjectId[];
}

export interface MoveItemRequest {
  target_list_id: ObjectId;
}

// ── Errors ────────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | ValidationError[];
}

export interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input: unknown;
  ctx?: Record<string, unknown>;
}
```

---

## Health Check

`GET /health` — no auth required. Returns `503` if the database is unreachable.

```json
{ "status": "ok", "db": "connected" }
```
