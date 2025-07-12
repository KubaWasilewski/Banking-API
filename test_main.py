import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from main import app, get_db
from typing import List
from models import *
from schemas import *


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
TOKEN_EXPIRY = 10


client = TestClient(app)
test_engine = create_engine(
    "postgresql://postgres:dbpass@localhost:5432/postgres_test"
)
TestSessionLocal = sessionmaker(test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_setup():
    db = override_get_db()
    db = next(db)
    db.add(Person(id="afc3c38f-c304-4ed5-a028-aa17547fe7e9", name="John", surname="Cena", email="johncena@gmail.com",
           hashed_password_hex="4a3a14d1869822748bbff6148d679caef5e4cb4100dc23a1a1cdf190d53fca46", created_at=datetime.date(2025, 7, 12)))
    db.add(Person(id="3a3b6a76-6273-446e-9b69-556a301bd001", name="Max", surname="Patison", email="maxpatison@gmail.com",
           hashed_password_hex="4a3a14d1869822748bbff6148d679caef5e4cb4100dc23a1a1cdf190d53fca46", created_at=datetime.date(2022, 4, 11)))
    db.commit()
    db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(test_engine)
    db_setup()
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def get_token():
    data = {"sub": "afc3c38f-c304-4ed5-a028-aa17547fe7e9"}
    to_encode = data.copy()
    expire = datetime.datetime.now(
        datetime.timezone.utc) + datetime.timedelta(seconds=TOKEN_EXPIRY)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


data_reigster_user = {
    "name": "Test",
    "surname": "User",
    "email": "testuser@gmail.com",
    "password": "password"
}
data_register_existing_user = {
    "name": "xxx",
    "surname": "xxx",
    "email": "johncena@gmail.com",
    "password": "xxx"
}
data_login = {
    "email": "johncena@gmail.com",
    "password": "cenapass"
}
data_login_invalid = {
    "email": "johncena@gmail.com",
    "password": "password"
}
headers = {
    "Authorization": ""
}
token = None
token_type = None


# test register endpoint with valid data
def test_valid_register():
    response = client.post("/register/", json=data_reigster_user)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test"
    assert data["surname"] == "User"
    assert data["email"] == "testuser@gmail.com"
    assert data["created_at"] == str(
        datetime.datetime.now(datetime.timezone.utc).date())


# test register endpoint with existing user
def test_register_existing_user():
    response = client.post("/register/", json=data_register_existing_user)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "email address already registered"


# test login endpoint with valid data
def test_login_valid():
    response = client.post("/login/", json=data_login)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "Bearer"
    assert data["access_token"]



# test login endpoint with invalid data
def test_login_invalid():
    response = client.post("/login/", json=data_login_invalid)
    assert response.status_code == 401


# test get users endpoint and it's return type
def test_get_users(get_token):
    headers["Authorization"] = "Bearer " + get_token
    response = client.get("/get-users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 1
    validated_data = [Person_scheme(**item) for item in data]
    assert len(validated_data) == len(data)
