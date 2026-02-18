from sqlalchemy import Column, Integer, String
from database import Base
import json

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    userid = Column(String, unique=True)
    username = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    currentlvl = Column(Integer)
    currentxp = Column(Integer)

class Quest(Base):
    __tablename__ = "quest"

    id = Column(Integer, primary_key=True)
    questid = Column(Integer)
    questname = Column(String)
    questdescription = -Column(String)
    requirements = Column(String)
    howtodoit = Column(String)