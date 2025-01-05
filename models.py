from flask import current_app
from configs import db, app
from flask_login import UserMixin
import uuid



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(256), nullable=False)

class Phone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    userid = db.Column(db.Integer, nullable=False)
    isdeleted = db.Column(db.Boolean, nullable=True)

class Purchased(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    phoneid = db.Column(db.Integer, nullable=False)




with app.app_context():
    db.create_all()
