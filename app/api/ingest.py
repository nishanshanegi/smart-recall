from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.vault import VaultItem, User # Add User here
from app.schemas.vault import IngestRequest
from app.services.sqs import sqs_service 
from app.services.s3 import s3_service 
from app.api.auth import get_current_user # <--- IMPORT THE GUARD
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ingest")
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