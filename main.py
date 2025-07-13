import uvicorn
import hashlib
import datetime
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from uuid import uuid4
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, create_engine
from models import *
from schemas import *


# JWT constants
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
TOKEN_EXPIRY = 3600


engine = create_engine(
    "postgresql://postgres:dbpass@localhost:5432/postgres"
)
SessionLocal = sessionmaker(engine)


app = FastAPI()


# generate Session with database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# check if user in db and if password hash matches
def authenticate_user(db: Session, email: str, password: str):
    query = select(Person).where(Person.email == email)
    query_result = db.scalars(query).first()
    if query_result == None:
        return query_result
    else:
        if hashlib.sha256(password.encode()).hexdigest() == query_result.hashed_password_hex:
            return query_result
        else:
            return None


# create JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(
        datetime.timezone.utc) + datetime.timedelta(seconds=TOKEN_EXPIRY)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# extract jwt token of type Bearer from Authorization header
def extract_token(request: Request):
    auth = request.headers.get("Authorization")
    if auth is None:
        raise HTTPException(
            status_code=401, detail="Missing Authorization header")
    parts = auth.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    return token


# verify if JWT token is valid and not expired
def verify_token(token: str = Depends(extract_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        person_id = payload.get("sub")
        if person_id is None:
            raise HTTPException(
                status_code=401, detail="invalid JWT token, person_id missing from sub")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid JWT token")

    return person_id


@app.get("/get-users/", response_model=List[Person_scheme])
def red_all_users(db: Session = Depends(get_db), _=Depends(verify_token)):
    query = select(Person)
    query_result = db.scalars(query)

    return query_result


@app.post("/register/", response_model=Person_scheme)
def register_user(person_register: Person_register, db: Session = Depends(get_db)):
    hashed_pass = hashlib.sha256(person_register.password.encode()).hexdigest()
    created_at = datetime.datetime.now(datetime.timezone.utc).date()
    person = Person(id=uuid4(), name=person_register.name, surname=person_register.surname,
                    email=person_register.email, hashed_password_hex=hashed_pass, created_at=created_at)
    db.add(person)
    try:
        db.commit()
        db.refresh(person)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="email address already registered")

    return person


@app.post("/login/", response_model=Token_scheme)
def login_user(person_login: Person_login, db: Session = Depends(get_db)):
    query_result = authenticate_user(
        db, person_login.email, person_login.password)
    if query_result == None:
        raise HTTPException(status_code=401, detail="invalid credentials")
    else:
        person_id = str(query_result.id)
        access_token = create_access_token(data={"sub": person_id})
        access_token = Token_scheme(
            access_token=access_token, token_type="Bearer")

        return access_token


@app.post("/register-account/", response_model=Account_scheme)
def register_accoumt(account_register: Account_register, db: Session = Depends(get_db), person_id: str = Depends(verify_token)):
    created_at = datetime.datetime.now(datetime.timezone.utc).date()
    account = Account(id=uuid4(), owner_id=person_id, name=account_register.name,
                      description=account_register.description, balance=0.0, created_at=created_at)

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@app.get("/get-accounts/", response_model=List[Account_scheme])
def read_all_account(db: Session = Depends(get_db), person_id: str = Depends(verify_token)):
    query = select(Account).where(Account.owner_id == person_id)
    query_result = db.scalars(query)

    return query_result


@app.put("/update-account/{account_id}/", response_model=Account_scheme)
def update_account(account_id: UUID, account: Account_update, db: Session = Depends(get_db), person_id: str = Depends(verify_token)):
    query = select(Account).where(Account.id == account_id)
    query_result = db.scalars(query).first()
    if query_result == None:
        raise HTTPException(
            status_code=404, detail="account with given id does not exist")
    elif str(query_result.owner_id) != person_id:
        raise HTTPException(
            status_code=401, detail="you do not have access to that account")

    query_result.balance = account.balance
    db.commit()
    db.refresh(query_result)

    return query_result


@app.delete("/delete-account/{account_id}/", response_model=Account_scheme)
def delete_account(account_id: UUID, db: Session = Depends(get_db), person_id: str = Depends(verify_token)):
    query = select(Account).where(Account.id == account_id)
    query_result = db.scalars(query).first()
    if query_result == None:
        raise HTTPException(
            status_code=404, detail="account with given id does not exist")
    elif str(query_result.owner_id) != person_id:
        raise HTTPException(
            status_code=401, detail="you do not have access to that account")

    db.delete(query_result)
    db.commit()

    return query_result


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    print("exit")
