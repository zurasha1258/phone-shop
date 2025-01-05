<<<<<<< HEAD
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class Configs:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

app = Flask(__name__)
app.config.from_object(Configs)
db = SQLAlchemy(app)
=======
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class Configs:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

app = Flask(__name__)
app.config.from_object(Configs)
db = SQLAlchemy(app)
>>>>>>> 1b01b77 (gitignoe added)
