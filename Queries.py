from Model1 import *
from sqlalchemy.orm import sessionmaker

# Initializing for pushing
Session = sessionmaker(bind=engine)
session = Session()


def add_to_db(obj):
    session.add(obj)
    session.commit()
