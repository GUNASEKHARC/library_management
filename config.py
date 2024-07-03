# config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://grady:admin@localhost:5432/library_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
