from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel, Field # NEW: For validation

from app.models.base import SessionLocal
from app.models.vault import User, VaultItem
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.services.sqs import sqs_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- VALIDATION SCHEMAS ---
class UserCreate(BaseModel):
    # WHY: min_length ensures the database isn't filled with 1-letter junk
    username: str = Field(..., min_length=5, description="Username must be at least 5 characters")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

# --- THE GUARDIAN FUNCTION ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(
        username=user_data.username, 
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Manual validation for login form
    if len(form_data.username) < 5 or len(form_data.password) < 8:
        raise HTTPException(status_code=400, detail="Invalid username or password length")

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "id": current_user.id}

@router.get("/demo-login")
def demo_login(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == "hr_guest").first()
    if not user:
        user = User(username="hr_guest", hashed_password=hash_password("guest123456")) # Valid length
        db.add(user)
        db.commit()
        db.refresh(user)

    count = db.query(VaultItem).filter(VaultItem.owner_id == user.id).count()
    if count == 0:
        print("🌱 Seeding Guest Vault...")
        sample_note = VaultItem(
            content_type="text", title="Medical Meeting",
            extracted_content="Scheduled on 17 July 2026", owner_id=user.id
        )
        db.add(sample_note)
        db.commit()
        sqs_service.send_task(sample_note.id, "text")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}