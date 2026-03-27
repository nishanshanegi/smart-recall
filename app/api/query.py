from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.base import SessionLocal
from app.models.vault import VaultItem, VaultChunk, AIRequestLog, User
from app.services.ai import ai_service 
from app.api.auth import get_current_user # <--- IMPORT THE GUARD

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ask")
def ask_vault(
    q: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- NOW PROTECTED
):
    clean_query = q.strip()
    query_vector = ai_service.get_embedding(clean_query)
    distance_func = VaultChunk.embedding.cosine_distance(query_vector)

    # HYBRID SEARCH + USER FILTER
    # WHY: We joined VaultItem so we can filter by 'owner_id'
    results = db.query(VaultChunk, VaultItem, distance_func.label("score")) \
        .join(VaultItem, VaultChunk.item_id == VaultItem.id) \
        .filter(VaultItem.owner_id == current_user.id) \
        .filter((distance_func < 0.9) | (VaultChunk.content.ilike(f"%{clean_query}%"))) \
        .order_by("score") \
        .limit(5).all()

    if not results:
        return {"query": clean_query, "answer": "Nothing found in your private vault."}

    context_text = "\n\n".join([r.VaultChunk.content for r in results])
    answer = ai_service.generate_answer(clean_query, context_text)

    return {
        "query": clean_query,
        "answer": answer,
        "user": current_user.username,
        "sources": [{"title": r.VaultItem.title} for r in results]
    }

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- PROTECTED
):
    avg_latency = db.query(func.avg(AIRequestLog.latency)).scalar()
    total_requests = db.query(AIRequestLog).count()
    
    return {
        "admin": current_user.username,
        "total_ai_calls": total_requests,
        "average_latency_seconds": round(avg_latency, 3) if avg_latency else 0
    }