from __future__ import annotations
import os,time,asyncio
from collections import defaultdict,deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,requests_per_minute:int|None=None):
        super().__init__(app)
        self.limit=requests_per_minute or int(os.getenv("GEOTECT_RATE_LIMIT_PER_MINUTE","600"))
        self.redis_url=os.getenv("REDIS_URL","").strip()
        self.local=defaultdict(deque);self.lock=asyncio.Lock();self._redis=None

    async def _redis_client(self):
        if not self.redis_url:return None
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis=redis.from_url(self.redis_url,decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis=None
        return self._redis

    async def dispatch(self,request,call_next):
        if self.limit<=0:return await call_next(request)
        key=request.client.host if request.client else "unknown"
        now=int(time.time());minute=now//60
        client=await self._redis_client()
        remaining=self.limit
        if client:
            rk=f"geotect:ratelimit:{key}:{minute}"
            try:
                value=await client.incr(rk)
                if value==1:await client.expire(rk,90)
                remaining=max(self.limit-value,0)
                if value>self.limit:
                    return JSONResponse({"detail":"Rate limit exceeded"},status_code=429,headers={"Retry-After":"60","X-RateLimit-Limit":str(self.limit),"X-RateLimit-Remaining":"0"})
            except Exception:
                client=None
        if not client:
            cut=time.monotonic()-60
            async with self.lock:
                q=self.local[key]
                while q and q[0]<cut:q.popleft()
                if len(q)>=self.limit:return JSONResponse({"detail":"Rate limit exceeded"},status_code=429,headers={"Retry-After":"60"})
                q.append(time.monotonic());remaining=max(self.limit-len(q),0)
        response=await call_next(request)
        response.headers["X-RateLimit-Limit"]=str(self.limit)
        response.headers["X-RateLimit-Remaining"]=str(remaining)
        response.headers["X-RateLimit-Mode"]="redis" if client else "local-fallback"
        return response
