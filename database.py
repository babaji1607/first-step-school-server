from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends, FastAPI, HTTPException, Query
from typing import Annotated
# from Utilities.settings import settings


# make sure to set the database URL in your .env file
# DATABASE_URL=sqlite:///./database.db

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
# this is dependency to be injected
