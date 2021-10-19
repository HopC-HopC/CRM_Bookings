from .models import User, Dog, Note, Attendance


def GetUser(user_id):
    return User.query.filter_by(id=user_id).first()


def GetDog(dog_id):
    return Dog.query.filter_by(id=dog_id).first()


def GetNote(note_id):
    return Note.query.filter_by(id=note_id).first()


def GetBooking(booking_id):
    return Attendance.query.filter_by(id=booking_id).first()


def GetAllUsers():
    return User.query.all()


def GetAllDogs():
    return Dog.query.all()


def GetAllNotes():
    return Note.query.all()


def GetAllBookings():
    return Attendance.query.all()
