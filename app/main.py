from fastapi import FastAPI
from app.models.base import init_db #imported db setup funtion
from app.api import ingest, query #importing business logics routers
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import log_ai_requests # Import your new function
from starlette.middleware.base import BaseHTTPMiddleware
from app.api import ingest, query, auth

app = FastAPI(
    title="DumpAI: The Intelligent Data Vault",
    description="A high-performance RAG backend for unstructured data ingestion.",
    version="1.0.0"
) #Creating an instance of the FastAPI class.  what Uvicorn (the server) looks for
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://dump-ai-ui.vercel.app",  # <--- REPLACE with your real Vercel URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow all (for dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_ai_requests)

@app.on_event("startup") #decorater that tells "Run this function when server starts"
def on_startup():
    init_db()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])

@app.get("/")
def read_root():
    return {"status": "healthy"}