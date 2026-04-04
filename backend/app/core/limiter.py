from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance — imported by main.py (to register with app)
# and by individual routes (to apply per-endpoint limits).
# Default: 200 requests/minute per IP across all endpoints.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
