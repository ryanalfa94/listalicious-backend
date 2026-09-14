# Frontend integration notes

Bugs, gaps, and gotchas found while building the frontend against this backend, logged here as they're found so they can be tackled later without digging back through chat history. Newest entries at the top of each section. Cross-reference: the frontend's own `REDESIGN_PROGRESS.md` tracks the UI side of this work.

## Bugs

### `POST /auth/change-password` is registered twice, and one copy is dead code

`backend/app/routes/auth.py` and `backend/app/routes/account.py` **both** declare `router = APIRouter(prefix="/auth", ...)` and **both** define `POST /change-password` — so both end up mounted at the exact same path, `POST /v1/auth/change-password`.

`main.py` includes them in this order:

```python
app.include_router(auth.router,           prefix=V1)   # line 211 — wins
...
app.include_router(account_routes.router,  prefix=V1)   # line 215 — shadowed, dead
```

FastAPI/Starlette resolves routes in registration order, so `auth.py`'s handler always wins and `account.py`'s is unreachable. This matters because `account.py`'s version is the more complete one — it has an optional `confirm_new_password` field and clearer validation (`_validate_new_password_rules`), while `auth.py`'s is the simpler one that actually runs.

**Fix options:**
- Delete/rename one of the two handlers so there's only one `/auth/change-password`, or
- Give `account.py`'s router a distinct prefix/path if it's meant to be a separate v2-style endpoint, or
- If `auth.py`'s version is intentionally the canonical one, delete `account.py`'s dead handler to avoid confusion.

Found: 2026-09-14, while auditing all routes to find backend features the frontend wasn't using yet. Not fixed — this is a backend-repo decision, left for you to make.

## Known gaps (endpoints that exist but nothing in the frontend calls yet)

Not bugs — just backend surface area with no UI built against it yet. Frontend team is working through these one at a time, each on its own branch (see `REDESIGN_PROGRESS.md` in the frontend repo for current status):

- `PUT /lists/{id}`, `DELETE /lists/{id}` — rename/delete a list (in progress as of 2026-09-14)
- `DELETE /lists/{id}/leave` — a collaborator leaving a shared list
- `POST /verify/forgot-password`, `POST /verify/reset-password` — no password-recovery UI exists at all yet
- `POST /items/bulk` — no "add several items at once" UI
- `PATCH /lists/{id}/archive`, `/unarchive`, `POST /lists/{id}/duplicate`
- `GET /users/search` — Share screen only accepts an exact email match today
- `PATCH /items/reorder`, `PATCH /items/{id}/move`
- `PATCH /auth/me` — no username-editing UI
- `GET /auth/sessions`, `DELETE /auth/sessions/{jti}` — only "log out everywhere" (`logout-all`) is wired up, no per-device list/revoke
- `POST /account/change-password` (dead code per the bug above) / `auth.py`'s live version — no change-password UI on either
- `DELETE /account/delete-account` — no account-deletion UI
- `GET /admin/users`, `PATCH /admin/users/{id}/status` — full admin user-management API, no UI planned against it (likely out of scope for the phone app)

## Design gaps (things the frontend had to scope down or fake because the backend has no data for them)

Carried over from `REDESIGN_PROGRESS.md`'s "Known blockers" section — repeated here since this file is meant to be the backend-side todo list:

- **No realtime/presence.** No websocket/polling presence signal exists, so "shopping right now" / "last active" UI, and any live-collaborator indicator, is either omitted or relabeled to something honest.
- **No `aisle` field on items.** Items can't be grouped by aisle; the Add/edit item UI has no aisle picker.
- **Activity is per-list only** (`GET /lists/{id}/activity`), no global/cross-list feed endpoint. The frontend fetches per-list and merges client-side, which is fine for a handful of lists but won't scale to dozens.
- **No invite-preview endpoint.** A `GET` for invite-token metadata (who invited you, which list) before accepting would let the Join screen show a real "Maya invited you to Groceries" headline instead of just an invite code.
- **No way to resolve a list owner's identity for non-owners.** `GET /lists/{id}` returns `owner_id` but there's no "get user by id" endpoint, so a non-owner's Share screen view can't show who owns the list.
- **`Item`'s `id` field serializes inconsistently.** `GET /lists/{id}/items` manually calls `.model_dump()` (no alias) and returns `id`; `POST`/`PUT`/`PATCH .../check` return the Pydantic model directly, which serializes via `response_model_by_alias` (default `true`) and returns `_id` — same resource, two different shapes depending on which route touched it. The frontend works around this with a `normalizeItem()` helper in `listApi.ts`, but the real fix belongs here (make all `Item`-returning routes serialize the same way).
- **Dev-mode email isn't real delivery.** With no `SENDGRID_API_KEY` set, verification/change-email/reset-password links get logged to the backend console instead of emailed. Fine for testing, not shippable — needs a real `SENDGRID_API_KEY` + from-address decision before going live.
