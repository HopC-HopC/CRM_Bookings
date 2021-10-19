from .functions import GetAllDogs
import datetime
from random import choice, randint
from . import db


""" 

These functions are only for testing and demonstration purposes. 

AutoGen creates random bookings for all dogs in the database.

ClearBookings removes all bookings. Past and present.

These functions are accessed via /autogen and /delbook, at the 
time of writing located in views.py.

"""


def AutoGen():
    for dog in GetAllDogs():
        tick = 0
        today = datetime.datetime.now()
        today -= datetime.timedelta(days=9)
        while tick < 50:
            tick += 1
            today += datetime.timedelta(days=choice([1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3]))
            dog.AddAttendance(
                day=today.day,
                month=today.month,
                year=today.year,
                assignment=randint(0, 3),
                booking_type=randint(1, 4),
            )
    # return True


def ClearBookings():
    from .functions import GetAllBookings

    for booking in GetAllBookings():
        db.session.delete(booking)
        db.session.commit()