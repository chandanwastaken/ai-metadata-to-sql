import os
from getpass import getpass
from db import init_db, SessionLocal
from models import User
from auth import get_password_hash
def create_initial_admin():
    init_db()
    db = SessionLocal()
    username = input("Enter admin username: ").strip()
    password = getpass("Enter admin password (hidden): ").strip()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"User '{username}' already exists.")
        return
    hashed_pw = get_password_hash(password)
    admin = User(username=username, hashed_password=hashed_pw, role='admin')
    db.add(admin)
    db.commit()
    print(f"Admin user '{username}' created successfully.")
if __name__ == "__main__":
    create_initial_admin()
