from __future__ import annotations
import os,time,asyncio
from collections import defaultdict,deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,requests_per_minute:int|None=None):
        super().__init__(app)
        self.limit=requests_per_minute or int(os.getenv("GEOTECT_RATE_LIMIT_PER_MINUTE","600"))
        self.windows=defaultdict(deque);self.lock=asyncio.Lock()
    async def dispatch(self,request,call_next):
        if self.limit<=0:return await call_next(request)
        key=request.client.host if request.client else "unknown";now=time.monotonic();cut=now-60
        async with self.lock:
            q=self.windows[key]
            while q and q[0]<cut:q.popleft()
            if len(q)>=self.limit:
                return JSONResponse({"detail":"Rate limit exceeded"},status_code=429,headers={"Retry-After":"60"})
            q.append(now)
        response=await call_next(request)
        response.headers["X-RateLimit-Limit"]=str(self.limit)
        return response
