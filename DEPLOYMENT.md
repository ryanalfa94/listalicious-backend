# Deployment Guide

This document covers production deployment considerations for the Listalicious backend.

## Environment variables

The backend depends on the following configuration values:

- `MONGO_URI` – MongoDB connection URI
- `MONGO_DB_NAME` – Database name
- `JWT_SECRET` – Secret for JWT signing
- `ALLOWED_ORIGINS` – Comma-separated allowed CORS origins
- `APP_URL` – Base URL for email links and redirect generation
- `SENDGRID_API_KEY` – Optional for email delivery
- `EMAIL_FROM` – Verified sender address for emails
- `ENV` – `dev` or `prod`

## Production checklist

- Set `ENV=prod`
- Use a secure `JWT_SECRET`
- Set `ALLOWED_ORIGINS` to your production frontend domain(s)
- Use a production-ready MongoDB service or cluster
- Do not commit `.env` or credentials to source control
- Ensure `EMAIL_FROM` is verified with SendGrid or your email provider

## Deployment options

### Docker Compose

For a simple production-like deployment, use Docker Compose:

```bash
docker compose build
docker compose up -d
```

### Cloud providers

This app can be deployed to services like Render, Railway, or any container-based host.

When deploying to cloud providers, make sure to:

- Configure environment variables in the provider dashboard
- Use a managed MongoDB instance
- Enable HTTPS for production traffic
- Set `ALLOWED_ORIGINS` to the live origin(s)

## Health checks

The app exposes:

- `GET /health` — liveness and database connectivity
- `GET /ready` — readiness check for startup completion

Configure your platform to use these endpoints for health probes.

## Logs and monitoring

- Collect container stdout/stderr logs
- Monitor MongoDB connectivity and response times
- Track failed auth or suspicious behavior if using the auth flows

## Recommended improvements

- Add structured logging or a log forwarder
- Add metrics or observability tooling
- Add a release/deployment checklist for your target platform
