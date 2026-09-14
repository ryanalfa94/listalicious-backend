# Frontend integration notes

Bugs, gaps, and gotchas found while building the frontend against this backend, logged here as they're found so they can be tackled later without digging back through chat history. Newest entries at the top of each section. Cross-reference: the frontend's own `REDESIGN_PROGRESS.md` tracks the UI side of this work.

(Note: this file has been rewritten from scratch a couple of times after landing on a branch that didn't have my earlier local-only commits to it — those commits never got pushed, so they didn't survive your merges. Rewriting the full content each time now instead of relying on git history for it.)

## Bugs

### `APP_URL` is still `http://localhost:3000` — every real email link is currently dead for a real user

**Found 2026-09-14, right after real email delivery (Brevo) went live — worth fixing before sending any more real emails to real people.**

`backend/app/services/mailer.py`: `APP_URL = os.getenv("APP_URL", "http://localhost:3000")`, and your `.env` has it explicitly set to that same value (not just the fallback). Every verification/reset/email-change link built from it —

```python
link = f"{APP_URL.rstrip('/')}/verify-email?token={token}"
```

— currently reads `http://localhost:3000/verify-email?token=...`. For anyone opening that email on a machine that isn't yours, `localhost:3000` resolves to *their own* computer — nothing is listening there, so the link is simply dead. Two separate problems bundled into one value:

1. **It needs to point at wherever the frontend actually is.** For local dev-machine-to-dev-machine testing that's `http://localhost:8090` (the frontend's actual Expo web port — note **not** 3000, so even same-machine local testing is currently broken too). For anything sent to a real inbox, it needs to be the real deployed frontend origin, or a mobile deep link scheme (e.g. `listalicious://verify-email?token=...`) if that's how the shipped app expects to be opened from an email.
2. **This is now live** — real emails are going out with this broken link today. Not an emergency (the frontend's screens all have a "paste the link or token" fallback that still works regardless of whether the link itself resolves), but every real recipient hits a dead page unless they know to copy the token out manually.

**Not fixed by me** — env var + a per-environment decision on the real frontend origin / deep link scheme, your call.

### Fixed: `POST /auth/change-password` was registered twice, one copy dead code

Was: `backend/app/routes/auth.py` and `backend/app/routes/account.py` both declared `POST /auth/change-password` at the identical path, and `account.py`'s (more complete) version was silently shadowed and unreachable since `auth.py`'s router was included first in `main.py`. Fixed in commit `ebc2303`: the duplicate was deleted, its one extra check ported into the surviving handler.

### Fixed: `GET /auth/sessions` always returned `[]` on a non-UTC server

Was: `_record_session` stored `expires_at` via a naive `datetime.fromtimestamp()` (no `tz=timezone.utc`), so on this dev machine (UTC-6/7 depending on DST) every session's stored expiry landed hours in the past, and the `>now()` filter in `GET /auth/sessions` excluded everything. Fixed in your `hotfixes` branch — verified directly against the `sessions` collection and via the frontend's session-list UI, which now populates correctly.

### Fixed: revoking a session could be silently undone by the frontend's own token refresh

Was: `DELETE /auth/sessions/{jti}` only blacklisted that access token's JTI; the paired refresh token wasn't tracked or checked by `/auth/refresh` at all, so a revoked device could quietly mint itself a new access token on its next silent refresh. Fixed in the same `hotfixes` branch — sessions now also record the paired refresh token's JTI/expiry, both get blacklisted on revoke, `/auth/refresh` checks `revoked_tokens` too, and the same fix was extended to single-device logout. Verified end-to-end: corrupted a second device's access token to force a refresh attempt after its session was revoked, and the refresh itself now correctly fails.

### Fixed: `DELETE /account/delete-account` required no password

Was: any valid access token could hard-delete the account and cascade its data with zero re-authentication, unlike change-password/change-email which both require the current password. Fixed in `hotfixes` — now requires `{password}` in the body, verified against the current password hash. The frontend's typed "DELETE" confirmation was always just a UI-only guard against a stray tap, not a security boundary on its own — this closes the actual gap. (Frontend was updated the same day to send the password now that the contract changed.)

## Known gaps (endpoints that exist but nothing in the frontend calls yet)

All four backend gaps from `feature/backend-gaps` are now wired up on the frontend (`share-owner-identity`, `join-invite-preview`, `global-activity-feed`, `item-aisle-field` branches — see `REDESIGN_PROGRESS.md` for details): `GET /users/{id}`, `GET /lists/join/{token}` preview, `GET /lists/activity`, and the `aisle` field on items.

Still open:

- `PATCH /auth/me` (username) — done, frontend wired up (`username-edit` branch).
- `GET /auth/sessions` / `DELETE /auth/sessions/{jti}` — done (`sessions-list` branch), now that the timezone + revocation bugs above are fixed.
- `GET /admin/users`, `PATCH /admin/users/{id}/status` — full admin user-management API, no UI planned against it (likely out of scope for the phone app).

Genuinely nothing else known to be unused at this point — every non-admin endpoint has a frontend flow against it.

## Design gaps (things the frontend had to scope down or fake because the backend has no data for them)

- **No realtime/presence.** Still the only real "known blocker" left. No websocket/polling presence signal exists, so "shopping right now" / "last active" UI, and any live-collaborator indicator, is either omitted or relabeled to something honest. This is the biggest remaining product gap — the app's own tagline is "watch it empty in real time," so this is arguably closer to core value than anything else on this list.
- **`Item`'s `id` field serializes inconsistently.** `GET /lists/{id}/items` manually calls `.model_dump()` (no alias) and returns `id`; `POST`/`PUT`/`PATCH .../check` return the Pydantic model directly, which serializes via `response_model_by_alias` (default `true`) and returns `_id` — same resource, two different shapes depending on which route touched it. The frontend works around this with a `normalizeItem()` helper in `listApi.ts`, but the real fix belongs here (make all `Item`-returning routes serialize the same way).
- **Dev-mode email fallback.** No longer the blocker it was — real delivery via Brevo is live (see the `APP_URL` bug above for the one loose end). Sender is currently a personal Gmail address verified in Brevo; before shipping, move to a domain-verified sender (e.g. `no-reply@listalicious.app`) for deliverability (avoids spam-folder issues) — your own note, repeating it here so it's tracked in one place.

## Heads-up: Brevo free tier is 300 emails/day

Real email sends now happen on every registration, forgot-password, and email-change request — including from automated testing. Worth keeping in mind before running a large batch of signup/reset tests in a single day; you'll get rate-limited by Brevo's cap, not by the backend itself.
