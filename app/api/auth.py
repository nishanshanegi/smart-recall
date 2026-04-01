from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.models.base import SessionLocal
from app.models.vault import User
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.models.vault import VaultItem, VaultChunk
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login") #Expect a Bearer token in Authorization header

def get_db(): #Creates DB session
    db = SessionLocal()
    try:
        yield db #gives it to route
    finally:     #After request → automatically closes
        db.close()

# --- THE GUARDIAN FUNCTION ---
# WHY: This is the function other routes call to check "Who is this?"
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):   #token → automatically extracted from header ...db → automatically injected
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/signup")
def signup(username: str, password: str, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(username=username, hashed_password=hash_password(password))
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/demo-login")
def demo_login(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == "hr_guest").first()
    if not user:
        user = User(username="hr_guest", hashed_password=hash_password("guest123"))
        db.add(user)
        db.commit()
        db.refresh(user)

    # --- AUTO-SEEDING LOGIC ---
    # Check if this guest already has items
    count = db.query(VaultItem).filter(VaultItem.owner_id == user.id).count()
    
    if count == 0:
        print("Seeding Guest Vault with sample data...")
        # 1. Add a Sample Note
        sample_note = VaultItem(
            content_type="text",
            title="Medical Meeting",
            extracted_content="Scheduled on 17 July 2026",
            owner_id=user.id
        )
        db.add(sample_note)
        
        # 2. Add another Note
        meeting_note = VaultItem(
            content_type="text",
            title="Meeting Notes: Project Alpha",
            extracted_content="Action Items: 1. Update UI 2. Fix Backend Bugs 3. Deploy to AWS.",
            owner_id=user.id
        )
        db.add(meeting_note)
        
        db.commit()
        # Note: For the AI search to work, the Worker must process these!
        # Since we added them manually to the DB, we should trigger SQS tasks here
        from app.services.sqs import sqs_service
        sqs_service.send_task(sample_note.id, "text")
        sqs_service.send_task(meeting_note.id, "text")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    # WHAT: Returns the logged-in user's details
    # WHY: So the frontend knows who is currently using the app
    return {"username": current_user.username, "id": current_user.id}