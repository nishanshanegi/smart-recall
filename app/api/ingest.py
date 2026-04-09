from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.vault import VaultItem, User # Add User here
from app.schemas.vault import IngestRequest
from app.services.sqs import sqs_service 
from app.services.s3 import s3_service 
from app.api.auth import get_current_user # <--- IMPORT THE GUARD
import uuid
from sqlalchemy import func, cast, Date, extract
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ingest")
# 1. Save record to Postgres (Status is implicitly 'pending')
async def ingest_data(
    request: IngestRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- PROTECT ROUTE
):
    # WHAT: We add 'owner_id' to the item
    # WHY: This creates the "Privacy Link" in the database.
    new_item = VaultItem(
        content_type=request.content_type,
        title=request.title,
        extracted_content=request.content,
        owner_id=current_user.id # <--- SET THE OWNER
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    try:
        sqs_service.send_task(new_item.id, new_item.content_type)
    except Exception as e:
        print(f"Failed to send to SQS: {e}")

    return {
        "status": "queued", 
        "owner": current_user.username,
        "id": new_item.id, 
        "message": "Processing started for your private vault"
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- PROTECT ROUTE
):
    file_ext = file.filename.split(".")[-1]
    s3_key = f"uploads/{uuid.uuid4()}.{file_ext}"

    content = await file.read()
    s3_service.upload_file(content, s3_key, file.content_type)

    # WHAT: Link the uploaded file to the current user
    new_item = VaultItem(
        content_type=file.content_type,
        title=file.filename,
        s3_key=s3_key,
        extracted_content=None,
        owner_id=current_user.id # <--- SET THE OWNER
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    sqs_service.send_task(new_item.id, file.content_type)

    return {
        "status": "uploaded", 
        "owner": current_user.username,
        "id": new_item.id, 
        "s3_key": s3_key
    }


@router.get("/items")
async def get_user_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # WHAT: Fetch all items owned by this user, newest first
    items = db.query(VaultItem).filter(VaultItem.owner_id == current_user.id).order_by(VaultItem.created_at.desc()).all()
    
    return [
        {
            "id": item.id,
            "title": item.title,
            "content_type": item.content_type,
            "created_at": item.created_at,
            "is_processed": True if item.extracted_content else False
        } for item in items
    ]

@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    item = db.query(VaultItem).filter(VaultItem.id == item_id, VaultItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # This automatically deletes related chunks too because of our 'relationship'
    db.delete(item)
    db.commit()
    return {"message": "Deleted successfully"}

@router.get("/activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # WHAT: Fetch only the 3 most recent items
    # WHY: We want the dashboard to stay clean, showing only "What's happening now"
    items = db.query(VaultItem).filter(VaultItem.owner_id == current_user.id).order_by(VaultItem.created_at.desc()).limit(3).all()
    
    return [
        {
            "id": item.id,
            "title": item.title,
            "status": "ready" if item.extracted_content else "processing",
            "time": item.created_at
        } for item in items
    ]

@router.get("/activity-calendar")
def get_calendar_stats(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()
    # WHAT: Fetch all activity for the current month
    # WHY: To show dots under the days in the UI
    history = db.query(
        cast(VaultItem.created_at, Date).label("day"),
        func.count(VaultItem.id).label("count")
    ).filter(
        VaultItem.owner_id == current_user.id,
        extract('month', VaultItem.created_at) == now.month,
        extract('year', VaultItem.created_at) == now.year
    ).group_by(cast(VaultItem.created_at, Date)).all()

    return {str(h.day): h.count for h in history}