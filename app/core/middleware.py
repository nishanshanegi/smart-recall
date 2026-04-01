import time
from fastapi import Request
from app.models.base import SessionLocal
from app.models.vault import AIRequestLog

async def log_ai_requests(request: Request, call_next):
    # 1. Start the timer
    start_time = time.time()
    
    # 2. Let the request finish
    response = await call_next(request)
    
    # 3. Calculate time
    process_time = time.time() - start_time

    # --- THE SELECTIVE FILTER ---
    # WHY: We only want to log "Value-Added" AI interactions.
    # We ignore /stats, /health, /me, and /login because they are "Background Noise".
    ai_endpoints = ["/ask", "/ingest", "/upload"]
    
    # WHAT: Check if the current URL matches one of our AI routes
    should_log = any(endpoint in request.url.path for endpoint in ai_endpoints)

    if should_log:
        db = SessionLocal()
        try:
            log_entry = AIRequestLog(
                endpoint=request.url.path,
                latency=round(process_time, 4),
                status_code=response.status_code
            )
            db.add(log_entry)
            db.commit()
            print(f"📊 AI Log Created: {request.url.path}")
        except Exception as e:
            print(f"❌ Logging Error: {e}")
        finally:
            db.close()

    # Still add the header to everything for debugging
    response.headers["X-Process-Time"] = str(process_time)
    
    return response