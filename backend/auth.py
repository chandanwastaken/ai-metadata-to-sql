from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
from db import SessionLocal
from models import User, TokenBlacklist
from typing import Optional
SECRET_KEY = os.environ.get('APP_SECRET_KEY', 'change_this_secret')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))  # default 60 minutes
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire, 'sub': data.get('sub')})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def is_token_blacklisted(db: Session, token: str) -> bool:
    t = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    return t is not None
def blacklist_token(db: Session, token: str, expires_at: datetime = None):
    existing = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    if existing:
        return existing
    tb = TokenBlacklist(token=token, expires_at=expires_at)
    db.add(tb)
    db.commit()
    return tb
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if is_token_blacklisted(db, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token has been revoked')
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
def require_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail='Insufficient privileges')
        return current_user
    return role_checker
