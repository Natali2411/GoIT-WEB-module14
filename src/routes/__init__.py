from fastapi_limiter.depends import RateLimiter

from src.conf.config import settings

rate_limiter = RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60)
