import time
from fastapi import Request
from app.models.base import SessionLocal
from app.models.vault import AIRequestLog

# WHAT: A custom function to log every AI call
async def log_ai_requests(request: Request, call_next):
    start_time = time.time()
    
    # WHY: We wrap this in a try/except so even if logging fails, 
    # the user still gets a response.
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"🔥 Route Crash: {e}")
        # If the route itself crashes, we still want to finish the middleware
        from fastapi.responses import JSONResponse
        response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    process_time = time.time() - start_time

    # Only log to DB if it's NOT a massive binary file (optional)
    # This keeps your 'ai_logs' table clean.
    db = SessionLocal()
    try:
        log_entry = AIRequestLog(
            endpoint=request.url.path,
            latency=round(process_time, 4),
            status_code=response.status_code
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"❌ DB Logging Error: {e}")
    finally:
        db.close()

    response.headers["X-Process-Time"] = str(process_time)
    return response