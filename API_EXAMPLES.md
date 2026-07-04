# API Examples

This guide shows a few example requests for the main Listalicious backend flows.

## 1. Register a user

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password1",
    "username": "user"
  }'
```

## 2. Log in

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=user@example.com" \
  --data-urlencode "password=Password1"
```

## 3. Create a grocery list

```bash
curl -X POST http://127.0.0.1:8000/v1/lists \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Weekly groceries"}'
```

## 4. Add an item to a list

```bash
curl -X POST http://127.0.0.1:8000/v1/lists/<list_id>/items \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Milk",
    "quantity": 2,
    "unit": "liters"
  }'
```

## 5. Share a list

```bash
curl -X POST http://127.0.0.1:8000/v1/share \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"list_id":"<list_id>","email":"friend@example.com"}'
```

## 6. Check health and readiness

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/metrics
```
