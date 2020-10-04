from flask import Flask, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
import random
import time

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class config_prod():
    DEBUG = False

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

app = Flask(__name__)
app.config.from_object(config_prod)
db = SQLAlchemy()
db.init_app(app)

@app.before_first_request
def initialize_database():
    db.create_all()

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

class User(db.Model):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, unique=True)
    secret = Column(String, primary_key=True, unique=True)
    data = Column(String)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)


def make_id():
    return str(hashlib.md5((str(int(time.time())) + str(random.getrandbits(80))).encode('utf-8')).hexdigest())

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/new")
@app.route("/new/")
def new():
    return render_template("new.html")

@app.route("/vault")
@app.route("/vault/")
def vault():
    return render_template("vault.html")

@app.route("/api/create", methods=["POST"])
def create():
    try:
        user_id = make_id()
        user_secret = make_id() + make_id()
        db.session.add(User(id=user_id, secret=user_secret))
        db.session.commit()
        return {"status": "success", "message": "Successfully created new vault", "id": user_id, "secret": user_secret}
    except:
        return {"status": "fail", "message": "Failed to create new vault"}

@app.route("/api/save/<string:secretyes>", methods=["POST"])
def save(secretyes):
    result = User.query.filter_by(secret=secretyes).first()
    if result is None:
        return {"status": "fail", "message": "Invalid vault secret"}
    result.data = request.data.decode("utf-8")
    db.session.commit()
    return {"status": "success", "message": "Successfully saved vault"}


@app.route("/api/open/<string:secretyes>")
def open(secretyes):
    result = User.query.filter_by(secret=secretyes).first()
    if result is None:
        return {"status": "fail", "message": "Invalid vault secret"}

    return {"status": "success", "message": "Successfully retrieved vault", "data": result.data}

app.run()