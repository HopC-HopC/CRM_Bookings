from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand, migrate

from flask_login import UserMixin

from sqlalchemy.sql import func

import datetime

app = Flask(__name__)

db_name = "data.db"

app.config["SECRET_KEY"] = "all your base are belong to us"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_name}"
db = SQLAlchemy(app)


migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command("db", MigrateCommand)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    owner = db.Column(db.Integer, db.ForeignKey("user.id"))


class AdminNotes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    admin = db.Column(db.Integer, db.ForeignKey("user.id"))
    customer = db.relationship("User")


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    notes = db.relationship("Note")
    dogs = db.relationship("Dog")
    address_1 = db.Column(db.String(150), unique=True)
    post_code = db.Column(db.String(15))
    phone = db.Column(db.String(15))
    first_name = db.Column(db.String(25))
    surname = db.Column(db.String(25))
    role = db.Column(db.String(20), default="user")

    def __init__(self, email, username, password, role="user"):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        if self.id == 1:
            self.role == "admin"
        else:
            self.role = role


class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    owner = db.relationship("User")
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    breed = db.Column(db.String(100))
    gender = db.Column(db.String(50))
    age = db.Column(db.Integer)
    attendance = db.relationship("Attendance")

    def AddAttendance(self, day, month, year, assignment=0, booking_type=1):
        attend = Attendance(
            dog=self.id,
            day=int(day),
            month=int(month),
            year=int(year),
            date=f"{day}-{month}-{year}",
            assigned_to=assignment,
            booking_type=booking_type,
        )
        attend.week_number()
        db.session.add(attend)
        db.session.commit()


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dog = db.Column(db.Integer, db.ForeignKey("dog.id"))
    day = db.Column(db.Integer)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)
    date = db.Column(db.String(20))
    iso_week = db.Column(db.Integer)
    iso_year = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    booking_type = db.Column(db.Integer)

    def week_number(self):
        self.iso_week = datetime.date(self.year, self.month, self.day).isocalendar()[1]
        self.iso_year = datetime.date(self.year, self.month, self.day).isocalendar()[0]
        db.session.commit()


if __name__ == "__main__":
    manager.run()