from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("postgresql://postgres:RIVOJmz777@localhost/delivery_db", echo=True)

Base = declarative_base()  # modellarni hosil qilish uchun
session = sessionmaker(bind=engine) # crud operatsiyalarni bajarish uchun