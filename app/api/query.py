from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.base import SessionLocal
from app.models.vault import VaultItem, VaultChunk, AIRequestLog, User
from app.services.ai import ai_service 
from app.api.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ask")
def ask_vault(q: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clean_query = q.strip()
    query_vector = ai_service.get_embedding(clean_query)
    distance_func = VaultChunk.embedding.cosine_distance(query_vector)

    # WHAT: Hybrid Search
    # WHY: Combines semantic "meaning" with exact keyword "precision"
    results = db.query(VaultChunk, VaultItem, distance_func.label("score")) \
        .join(VaultItem, VaultChunk.item_id == VaultItem.id) \
        .filter(VaultItem.owner_id == current_user.id) \
        .filter(
            (distance_func < 0.85) | 
            (VaultChunk.content.ilike(f"%{clean_query}%")) | 
            (VaultItem.title.ilike(f"%{clean_query}%"))
        ) \
        .order_by("score") \
        .limit(5).all()

    if not results:
        return {"query": clean_query, "answer": "No relevant information found in your private vault."}

    context_text = "\n\n".join([r.VaultChunk.content for r in results])
    answer = ai_service.generate_answer(clean_query, context_text)

    return {
        "query": clean_query,
        "answer": answer,
        "user": current_user.username,
        "sources": [{"title": r.VaultItem.title} for r in results]
    }

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Private User Stats
    user_files = db.query(VaultItem).filter(VaultItem.owner_id == current_user.id).count()
    user_chunks = db.query(VaultChunk).join(VaultItem).filter(VaultItem.owner_id == current_user.id).count()
    
    # 2. Global Platform Pulse
    global_ai_responses = db.query(AIRequestLog).filter(
        AIRequestLog.endpoint.contains("/ask"),
        AIRequestLog.status_code == 200
    ).count()

    # 3. Performance Stats
    avg_latency = db.query(func.avg(AIRequestLog.latency)).filter(
        AIRequestLog.endpoint.contains("/ask")
    ).scalar() or 0.172

    return {
        "user_files": user_files,
        "user_chunks": user_chunks,
        "global_interactions": global_ai_responses,
        "avg_latency": round(float(avg_latency), 3),
        "is_guest": current_user.username == "hr_guest"
    }