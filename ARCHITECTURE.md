# Architecture Overview

This backend is organized as a layered FastAPI application backed by MongoDB.

## High-level flow

1. Requests enter the FastAPI app in [backend/app/main.py](backend/app/main.py).
2. The app applies middleware for security headers, request IDs, request logging, and rate limiting.
3. Routes in [backend/app/routes](backend/app/routes) handle auth, lists, items, sharing, account, and verification flows.
4. Services in [backend/app/services](backend/app/services) contain the business logic for auth, JWTs, mail, activity, and access control.
5. MongoDB is accessed through the async Motor client in [backend/app/database/database.py](backend/app/database/database.py).

## Main components

### API layer

- `main.py` wires the app, middleware, health routes, and router registration.
- Route modules expose the REST endpoints for the client.

### Service layer

- Auth and JWT logic live in the auth-related services.
- Guards enforce ownership and verification rules.
- Mailer handles email delivery for verification and password reset.
- Activity service writes list activity events.

### Data layer

- MongoDB stores users, lists, items, invites, sessions, verification tokens, and activity logs.
- Indexes are created at startup via `init_indexes()`.

## Request lifecycle

- A request gets a request ID and timing metadata.
- The app logs the request and records basic metrics.
- Route logic validates access and uses service functions to operate on MongoDB.
- Responses are returned with standard headers and JSON payloads.

## Design notes

- The backend favors a simple, modular structure for fast development and easy iteration.
- Auth is token-based with JWTs and session revocation support.
- Email verification and password-reset flows are separated from core auth logic.
- The app is designed to run either locally or in Docker Compose.

## Suggested next steps

- Add structured logging export or OpenTelemetry tracing.
- Add WebSocket support for live shared-list updates.
- Add role-based sharing for more advanced collaboration.
