from flask import current_app
from configs import db, app
from flask_login import UserMixin
import uuid
from sqlalchemy import Enum



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    status = db.Column(db.String(10), nullable=True)


class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    userid = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=True)


class Purchased(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    phoneid = db.Column(db.Integer, nullable=False)







