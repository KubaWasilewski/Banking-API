import uvicorn
from typing import List
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
from models import Person, Account
from schemas import Person_scheme, Account_scheme



app = FastAPI()

@app.get("/getAll/", response_model = List[Person_scheme])
def red_all_users():
    user_list = []
    with Session(engine) as sess:
        stmt = select(Person)
        res = sess.scalars(stmt)
        for u in res:
            user_list.append(u)
    return user_list


if __name__ == "__main__":
    engine = create_engine("postgresql://postgres:dbpass@localhost:5432/postgres")

    uvicorn.run(app, host = "127.0.0.1", port=8000)
    print("exit")