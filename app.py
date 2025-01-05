from configs import app, db
from flask_login import LoginManager
from models import User
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
