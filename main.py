#import libraries
import psycopg2
from fastapi import FastAPI
from uuid import UUID, uuid4
import hashlib
from datetime import datetime

def db_setup():
    #connect to local db server 
    conn = psycopg2.connect(host = "localhost", dbname = "postgres", user = "postgres", password = "dbpass", port = 5432)
    cur = conn.cursor()    

    #create tables
    cur.execute("""CREATE TABLE IF NOT EXISTS person (
                id UUID PRIMARY KEY, 
                name VARCHAR(128) NOT NULL, 
                surname VARCHAR(128) NOT NULL, 
                email VARCHAR(128) NOT NULL,
                hashedPassword_hex VARCHAR(64) NOT NULL,
                createdAt DATE NOT NULL 
                );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS account (
                id UUID PRIMARY KEY,
                ownerId UUID NOT NULL, 
                name VARCHAR(128) NOT NULL, 
                description VARCHAR(512),
                balance NUMERIC(12, 2) NOT NULL,
                createdAt DATE NOT NULL,
                CONSTRAINT fk_person FOREIGN KEY (ownerId)
                REFERENCES person(id)
                );""")

    conn.commit()

    return conn, cur

#execute code if file name main
if __name__ == "__main__":
    print("start")
    conn, cur = db_setup()
    cur.close()
    conn.close()
    print("exit")