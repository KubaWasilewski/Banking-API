import uvicorn
import hashlib
import datetime
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from uuid import uuid4
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, create_engine
from models import *
from schemas import *


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
TOKEN_EXPIRY = 3600


app = FastAPI()


# check if user in db and if password hash matches
def authenticate_user(email: str, password: str):
    with Session(engine) as sess:
        query = select(Person).where(Person.email == email)
        query_result = sess.scalars(query).first()
        if query_result == None:
            return False
        else:
            if hashlib.sha256(password.encode()).hexdigest() == query_result.hashed_password_hex:
                return True
            else:
                return False


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
def red_all_users(_=Depends(verify_token)):
    user_list = []
    with Session(engine) as sess:
        query = select(Person)
        query_result = sess.scalars(query)
        for u in query_result:
            user_list.append(u)

    return user_list


@app.post("/register/", response_model=Person_scheme)
def register_user(person_register: Person_register):
    hashed_pass = hashlib.sha256(person_register.password.encode()).hexdigest()
    created_at = datetime.datetime.now(datetime.timezone.utc).date()
    person = Person(id=uuid4(), name=person_register.name, surname=person_register.surname,
                    email=person_register.email, hashed_password_hex=hashed_pass, created_at=created_at)
    person_scheme = Person_scheme.model_validate(person)
    with Session(engine) as sess:
        sess.add(person)
        try:
            sess.commit()
        except IntegrityError:
            sess.rollback()
            raise HTTPException(
                status_code=409, detail="email address already registered")

    return person_scheme


@app.post("/login/", response_model=Token_scheme)
def login_user(person_login: Person_login):
    user_auth = authenticate_user(person_login.email, person_login.password)
    if not user_auth:
        raise HTTPException(status_code=401, detail="invalid credentials")
    else:
        with Session(engine) as sess:
            query = select(Person).where(Person.email == person_login.email)
            query_result = sess.scalars(query).first()
            person_id = str(query_result.id)
            access_token = create_access_token(data={"sub": person_id})

        access_token = Token_scheme(
            access_token=access_token, token_type="Bearer")
        return access_token


@app.post("/register-account", response_model=Account_scheme)
def register_accoumt(account_register: Account_register, person_id: UUID = Depends(verify_token)):
    created_at = datetime.datetime.now(datetime.timezone.utc).date()
    account = Account(id=uuid4(), owner_id=person_id, name=account_register.name,
                      description=account_register.description, balance=0.0, created_at=created_at)
    account_scheme = Account_scheme.model_validate(account)
    with Session(engine) as sess:
        sess.add(account)
        sess.commit()

    return account_scheme


@app.get("/get-accounts/", response_model=List[Account_scheme])
def read_all_account(person_id: UUID = Depends(verify_token)):
    account_list = []
    with Session(engine) as sess:
        query = select(Account).where(Account.owner_id == person_id)
        query_result = sess.scalars(query)
        for a in query_result:
            account_list.append(a)

    return account_list


@app.put("/update-account")
def update_account():
    pass


@app.delete("/delete-account/")
def delete_account():
    pass


if __name__ == "__main__":
    engine = create_engine(
        "postgresql://postgres:dbpass@localhost:5432/postgres")
    uvicorn.run(app, host="127.0.0.1", port=8000)
    print("exit")
