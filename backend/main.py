import os
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List
from metadata_extractor import extract_schema_metadata
from vector_indexer import upsert_metadata_embeddings, semantic_search
from sql_generator import generate_sql_from_context
from executor import execute_sql
from utils import sanitize_identifier
from db import init_db, SessionLocal
from models import User, QueryHistory
from auth import authenticate_user, create_access_token, get_current_user, get_db, get_password_hash, require_role, blacklist_token
from connectors.factory import get_connector
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
init_db()
app = FastAPI(title='AI Metadata-to-SQL Generator')
class ConnectIn(BaseModel):
    conn_str: str
class ExtractIn(BaseModel):
    conn_str: str
    schema: str = 'public'
    db_type: str = 'postgresql'
class QueryIn(BaseModel):
    conn_str: str
    schema: str = 'public'
    question: str
    top_k: int = 6
    db_type: str = 'postgresql'
class ExecIn(BaseModel):
    conn_str: str
    sql: str
@app.post('/auth/token')
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail='Incorrect username or password')
    access_token = create_access_token(data={'sub': user.username})
    return {'access_token': access_token, 'token_type': 'bearer', 'role': user.role}
@app.post('/auth/create_user')
def create_user(username: str, password: str, role: str = 'analyst', current_user: User = Depends(require_role('admin')), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail='User exists')
    hashed = get_password_hash(password)
    u = User(username=username, hashed_password=hashed, role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {'ok': True, 'username': u.username, 'role': u.role}
@app.post('/auth/logout')
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_header = request.headers.get('authorization')
    if not auth_header:
        raise HTTPException(status_code=400, detail='Missing Authorization header')
    parts = auth_header.split()
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail='Invalid Authorization header')
    token = parts[1]
    try:
        import jwt
        payload = jwt.decode(token, os.environ.get('APP_SECRET_KEY', 'change_this_secret'), algorithms=['HS256'])
        exp = payload.get('exp')
        expires_at = None
        if exp:
            from datetime import datetime
            expires_at = datetime.utcfromtimestamp(exp)
    except Exception:
        expires_at = None
    blacklist_token(db, token, expires_at)
    return {'ok': True, 'detail': 'Logged out'}
@app.post('/connect')
def connect(payload: ConnectIn, current_user: User = Depends(get_current_user)):
    try:
        from sqlalchemy import create_engine
        engine = create_engine(payload.conn_str)
        with engine.connect() as conn:
            conn.execute('SELECT 1')
        return {'ok': True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post('/extract_metadata')
def extract_metadata(payload: ExtractIn, current_user: User = Depends(get_current_user)):
    try:
        try:
            connector = get_connector(payload.db_type, payload.conn_str, payload.schema)
        except Exception as ce:
            raise HTTPException(status_code=400, detail=str(ce))
        connector.connect()
        entries = connector.extract_metadata()
        upsert_metadata_embeddings(payload.schema, entries)
        return {'ok': True, 'count': len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post('/generate_sql')
def generate_sql(payload: QueryIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        results = semantic_search(payload.schema, payload.question, k=payload.top_k)
        sql = generate_sql_from_context(results, payload.question)
        q = QueryHistory(question=payload.question, sql=sql, schema=payload.schema, user_id=current_user.id)
        db.add(q)
        db.commit()
        db.refresh(q)
        return {'sql': sql, 'context': results, 'history_id': q.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post('/execute_sql')
def exec_sql(payload: ExecIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        df, sql_ran = execute_sql(payload.conn_str, payload.sql, limit=1000)
        csv = df.to_csv(index=False)
        return {'sql': sql_ran, 'rows': df.shape[0], 'columns': df.columns.tolist(), 'data': df.to_dict(orient='records'), 'csv': csv}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get('/history')
def history(all: bool = False, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if all:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail='Insufficient privileges to view all history')
        items = db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).all()
    else:
        items = db.query(QueryHistory).filter(QueryHistory.user_id == current_user.id).order_by(QueryHistory.created_at.desc()).all()
    out = [{'id': i.id, 'question': i.question, 'sql': i.sql, 'schema': i.schema, 'user_id': i.user_id, 'created_at': i.created_at.isoformat()} for i in items]
    return {'history': out}
