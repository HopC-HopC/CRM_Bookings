from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
import datetime
import calendar

from googlemaps import Client as GoogleMaps

API_KEY = "AIzaSyDbYrFwu-5Nftk1f2xc_lBZkMFSR98YGps"

gmaps = GoogleMaps(key=API_KEY)

admin = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role == "admin":
            return f(*args, **kwargs)
        else:
            flash("You need to be an admin to view this page.", category="error")
            return redirect(url_for("views.index"))

    return wrap


@admin.route("/admin")
@login_required
@admin_required
def admin_home():
    from .models import Note, User

    notes = Note.query.all()
    note_list = []
    for note in notes:
        customer = User.query.filter_by(id=note.owner).first()
        note.owner_name = f"{customer.first_name} {customer.surname}"
        note_list.append(note)
    most_recent_notes = []
    while len(note_list) > 0 and len(most_recent_notes) < 12:
        most_recent_notes.append(note_list.pop(-1))
    return render_template(
        "admin_home.html", user=current_user, notes=most_recent_notes
    )


@admin.route("/view_bookings")
@login_required
@admin_required
def view_bookings():
    return render_template("view_bookings.html", user=current_user)


@admin.route("/admin_customers")
@login_required
@admin_required
def admin_customers():
    from .models import User

    customer_list = User.query.all()
    return render_template(
        "admin_customers.html", user=current_user, customer_list=customer_list
    )


@admin.route("/admin_dogs")
@login_required
@admin_required
def admin_dogs():
    from .models import Dog

    dog_list = Dog.query.all()
    return render_template("admin_dogs.html", user=current_user, dog_list=dog_list)


@admin.route("/owner/<int:owner_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_owner(owner_id):
    from .models import User, AdminNotes, Dog

    if request.method == "POST":
        from .models import User
        from . import db

        owner = User.query.filter_by(id=int(owner_id)).first()

        if "owner_details" in request.form:
            first_name = request.form.get("first_name")
            surname = request.form.get("surname")
            email = request.form.get("email")
            address_1 = request.form.get("address_1")
            post_code = request.form.get("post_code")
            phone = request.form.get("phone")
            role = request.form.get("role")
            if first_name and first_name is not owner.first_name:
                owner.first_name = first_name
            if surname and surname is not owner.surname:
                owner.surname = surname
            if email and email is not owner.email:
                owner.email = email
            if address_1 and address_1 is not owner.address_1:
                owner.address_1 = address_1
            if post_code and post_code is not owner.post_code:
                owner.post_code = post_code
            if phone and phone is not owner.phone:
                owner.phone = phone
            owner.role = role
            db.session.commit()
        elif "admin_note" in request.form:
            new_note = request.form.get("note")
            if len(new_note) < 1:
                flash("No note entered", category="error")
            elif len(new_note) < 5:
                flash("Note too short", category="error")
            else:
                note = AdminNotes(data=new_note, admin=current_user.id, customer=owner)
                db.session.add(note)
                db.session.commit()
                flash(
                    f"Thanks {current_user.username}, your note has been added",
                    category="success",
                )
    owner = User.query.filter_by(id=owner_id).first()
    admin_notes = AdminNotes.query.filter_by(customer=owner).all()
    dogs = Dog.query.filter_by(owner_id=owner.id).all()
    """ Google Map """
    # Geocoding: getting coordinates from address text
    geocode_result = gmaps.geocode(
        f"{owner.address_1}, {owner.post_code}, United Kingdom"
    )
    coordinates = []
    try:
        coordinates.append(geocode_result[0]["geometry"]["location"]["lat"])
        coordinates.append(geocode_result[0]["geometry"]["location"]["lng"])
    except IndexError:
        pass
    return render_template(
        "admin_owner.html",
        user=current_user,
        owner=owner,
        admin_notes=admin_notes,
        coordinates=coordinates,
        dogs=dogs,
        api_key=API_KEY,
    )


@admin.route("/admin_today")
@admin.route("/admin_today/<int:month>/<int:day>")
@login_required
@admin_required
def admin_today(month=datetime.datetime.now().month, day=datetime.datetime.now().day):
    from .models import Attendance, Dog, User

    """

    Lookup booking for the day
    Grab dog name
    Lookup Owner
    Grab owner address + postcode, geocode each and add to list

    """
    if month == datetime.datetime.now().month and day == datetime.datetime.now().day:
        today = datetime.datetime.now()

        if today > datetime.datetime.strptime(
            f"{today.day}/{today.month}/{today.year} 15:00", "%d/%m/%Y %H:%M"
        ):
            today = today + datetime.timedelta(days=1)
            today = datetime.datetime.strptime(
                f"{today.day}/{today.month}/{today.year} 09:00", "%d/%m/%Y %H:%M"
            )
        if today.strftime("%A") == "Saturday":
            today = today + datetime.timedelta(days=2)
            today = datetime.datetime.strptime(
                f"{today.day}/{today.month}/{today.year} 09:00", "%d/%m/%Y %H:%M"
            )
        if today.strftime("%A") == "Sunday":
            today = today + datetime.timedelta(days=1)
            today = datetime.datetime.strptime(
                f"{today.day}/{today.month}/{today.year} 09:00", "%d/%m/%Y %H:%M"
            )
    else:
        today = datetime.datetime.strptime(
            f"{day}/{month}/{datetime.datetime.now().year} 09:00", "%d/%m/%Y %H:%M"
        )
    today_dogs = []
    today_owners = []
    today_bookings = Attendance.query.filter_by(
        day=today.day, month=today.month, year=today.year
    ).all()
    label = 1

    today_ = f'{today.strftime("%A")}, {today.day}/{today.month}/{today.year}'
    for booking in today_bookings:
        dog = Dog.query.filter_by(id=booking.dog).first()  # dog.id
        owner = User.query.filter_by(id=dog.owner_id).first()
        today_dogs.append(
            [
                dog,
                booking.assigned_to,
                booking.id,
                {
                    "ADDRESS": owner.address_1,
                    "POSTCODE": owner.post_code,
                    "COUNTRY": "United Kingdom",
                    "LABEL": str(label),
                    "DOGNAME": dog.name,
                    "OWNERNAME": f"{owner.first_name} {owner.surname}",
                },
            ]
        )
        today_owners.append(owner)
        label += 1
        today_ = f'{today.strftime("%A")}, {today.day}/{today.month}/{today.year}'
    next_day = today + datetime.timedelta(1)
    previous_day = today - datetime.timedelta(1)
    return render_template(
        "admin_today.html",
        dog_names=today_dogs,
        user=current_user,
        today=today_,
        next_day=[next_day.month, next_day.day],
        previous_day=[previous_day.month, previous_day.day],
    )


@admin.route("/assign_dog", methods=["POST"])
@admin_required
def booking_assign():
    if request.method == "POST" and request.form["staff"]:
        from .functions import GetBooking

        booking = GetBooking(int(request.form["booking_id"]))
        print(f"Booking ID: {booking.dog}")
        print(f"Was assigned to: {booking.assigned_to}")
        booking.assigned_to = request.form["staff_id"]
        from . import db

        db.session.commit()
        print(f"Now assigned to: {booking.assigned_to}")
    return "success"


@admin.route("/admin_note/remove/<int:owner_id>/<int:note_id>", methods=["GET", "POST"])
@login_required
def note_remove(note_id, owner_id):
    try:
        if int(note_id) >= 0 and current_user.role == "admin":
            from .models import AdminNotes

            note_to_delete = AdminNotes.query.filter_by(id=int(note_id)).first()
            if note_to_delete:
                from . import db

                db.session.delete(note_to_delete)
                db.session.commit()
                flash(f"Note has been removed successfully.", category="success")
        else:
            flash(
                f"You do not have permission to access that function.", category="error"
            )
    except ValueError:
        flash("Error removing message.", category="error")
    return redirect(f"/owner/{owner_id}")


@admin.route("/admin_dog_calendar/<int:owner_id>", methods=["GET", "POST"])
@admin.route("/admin_dog_calendar/<int:owner_id>/<int:month_>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_dog_calendar(owner_id, month_=datetime.datetime.now().month):
    from .models import User

    owner = User.query.filter_by(id=int(owner_id)).first()
    if request.method == "POST":
        dates = []
        dates = request.form.getlist("checkbox")
        if len(dates) > 0:
            message_ = f"Thanks {owner.username}! "
        else:
            return redirect(f"/admin_dog_calendar/{owner_id}/{month_}")
        dog_amount = 1
        for dog in owner.dogs:
            if dog_amount > 1:
                message_ = message_ + f", {dog.name}"
            else:
                message_ = message_ + f"{dog.name}"
            dog_amount += 1
        message_ = message_ + " booked in for "
        for date in dates:
            if date == dates[-1]:
                message_ = message_ + f"and {date}/{month_}. "
            else:
                message_ = message_ + f"{date}/{month_}, "
            for dog in owner.dogs:
                dog.AddAttendance(date, month_, datetime.datetime.now().year)
        flash(message_, category="success")
    try:
        if int(month_) > 12 or int(month_) < 1:
            if int(month_) == 13:
                month_ = 1
            elif int(month_) == 0:
                month_ = 12
            else:
                month_ = datetime.datetime.now().month
    except ValueError:
        month_ = datetime.datetime.now().month
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    month = calendar.TextCalendar(calendar.MONDAY)
    month_days = []
    current_date = [
        datetime.datetime.now().day,
        datetime.datetime.now().month,
        datetime.datetime.now().year,
    ]
    current_attendance = []
    for dog in owner.dogs:
        for a in dog.attendance:
            if int(a.month) == int(month_):
                current_attendance.append(a.day)

    """ 
        Generating days of month and comparing against days booked, returning days booked with
        additional character to be parsed by jinja
    """
    year_ = datetime.datetime.now().year
    today = datetime.datetime.now()
    current_attendance = set(current_attendance)
    weekends = [6, 7, 13, 14, 20, 21, 27, 28, 34, 35]
    count = 0
    for day in month.itermonthdays(year_, int(month_)):
        count += 1
        if day > 0:
            day_to_add = f"{day}"
            calendar_date = f"{day}/{month_}/{year_} 12:00"
            calendar_date = datetime.datetime.strptime(calendar_date, "%d/%m/%Y %H:%M")
            if day in current_attendance:
                day_to_add = day_to_add + "a"  #   indicates day booked already
            if today > calendar_date:
                day_to_add = day_to_add + "l"  #   indicate day is in the past
            elif count in weekends:
                day_to_add = day_to_add + "l"  #   indicate day is weekend
            month_days.append(f"{day_to_add}")
        else:
            month_days.append(day)
    from .models import Dog

    owner_dogs = Dog.query.filter_by(owner_id=owner.id).all()
    if len(owner_dogs) > 0:
        dogs_string = ""
        while len(owner_dogs) > 1:
            dogs_string = dogs_string + f"{owner_dogs[0].name}"
            owner_dogs.pop(0)
            if len(owner_dogs) > 1:
                dogs_string += ", "
            else:
                dogs_string += " & "
    dogs_string += f"{owner_dogs[0].name}"

    return render_template(
        "admin_dog_calendar.html",
        user=current_user,
        owner=owner,
        calendar=month_days,
        month_num=int(month_),
        month_name=(months[int(month_) - 1]).strip(),
        year=datetime.datetime.now().year,
        current_date=current_date,
        dogs=dogs_string,
    )


@admin.route(
    "/admin_dog_calendar/cancel/<int:owner_id>/<int:month_>/<int:day_>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def booking_cancel(month_, day_, owner_id):
    if int(month_) > 0 and int(day_) > 0 and int(owner_id) > 0:
        from .models import User, Attendance
        from . import db

        owner = User.query.filter_by(id=int(owner_id)).first()
        # print(f'canceling session for {owner.username} on {day_}/{month_}')
        for dog in owner.dogs:
            # print(dog.name + '\n')
            # for a in dog.attendance:

            day = Attendance.query.filter_by(
                dog=dog.id,
                month=int(month_),
                day=int(day_),
                year=datetime.datetime.now().year,
            ).first()
            if day:
                db.session.delete(day)
                db.session.commit()
                flash(
                    f"Booking for {dog.name} on {day_}/{month_} cancelled",
                    category="error",
                )
    else:
        pass
    owner_id = owner_id
    month_ = month_
    return redirect("/admin_dog_calendar/" + f"{owner_id}" + f"/{month_}")


@admin.route("/admin_dogs/<int:dog_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_dogs_view(dog_id):
    from .models import Dog

    if request.method == "POST":
        from . import db

        dog = Dog.query.filter_by(id=int(dog_id)).first()
        name = request.form.get("name")
        breed = request.form.get("breed")
        age = request.form.get("age")
        gender = request.form.get("gender")
        if name and name is not dog.name:
            dog.name = name
        if breed and breed is not dog.breed:
            dog.breed = breed
        if age and age is not dog.age:
            dog.age = age
        if gender and gender is not dog.gender:
            dog.gender = gender
        db.session.commit()
    dog = Dog.query.filter_by(id=dog_id).first()
    return render_template("admin_dogs_view.html", user=current_user, dog=dog)


@admin.route(
    "/admin_view_bookings/<int:iso_week>/<int:iso_year>", methods=["GET", "POST"]
)
@admin.route("/admin_view_bookings/<int:iso_week>", methods=["GET", "POST"])
@admin.route("/admin_view_bookings", methods=["GET", "POST"])
@login_required
@admin_required
def admin_view_week(
    iso_week=datetime.date(
        datetime.datetime.now().year,
        datetime.datetime.now().month,
        datetime.datetime.now().day,
    ).isocalendar()[1],
    iso_year=datetime.datetime.now().year,
):
    from .models import Dog, Attendance
    from . import db

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day
    if not iso_week:
        iso_week = datetime.date(
            current_year, current_month, current_day
        ).isocalendar()[1]
    if not iso_year:
        iso_year = datetime.date(
            current_year, current_month, current_day
        ).isocalendar()[0]
    iso_week = int(iso_week)
    iso_year = int(iso_year)
    if iso_week == 53:
        iso_week = 1
        iso_year += 1
    elif iso_week == 0:
        iso_week = 52
        iso_year -= 1
    for_date_monday = f"{iso_year}-W{iso_week}"
    monday = datetime.datetime.strptime(for_date_monday + "-1", "%G-W%V-%u")
    tuesday = monday + datetime.timedelta(days=1)
    wednesday = monday + datetime.timedelta(days=2)
    thursday = monday + datetime.timedelta(days=3)
    friday = monday + datetime.timedelta(days=4)
    saturday = monday + datetime.timedelta(days=5)
    sunday = monday + datetime.timedelta(days=6)
    iso_month = thursday.month
    from . import db

    dog_list = db.session.query(Dog).all()
    week_dict = []
    # monday_list = db.session.query(Attendance).all()
    iso_week = int(iso_week)
    iso_year = int(iso_year)
    week_dates = [
        (
            f"{monday.day}/{monday.month}/{str(monday.year)[2:]}",
            monday.day,
            monday.month,
        ),
        (
            f"{tuesday.day}/{tuesday.month}/{str(tuesday.year)[2:]}",
            tuesday.day,
            tuesday.month,
        ),
        (
            f"{wednesday.day}/{wednesday.month}/{str(wednesday.year)[2:]}",
            wednesday.day,
            wednesday.month,
        ),
        (
            f"{thursday.day}/{thursday.month}/{str(thursday.year)[2:]}",
            thursday.day,
            thursday.month,
        ),
        (
            f"{friday.day}/{friday.month}/{str(friday.year)[2:]}",
            friday.day,
            friday.month,
        ),
        (
            f"{saturday.day}/{saturday.month}/{str(saturday.year)[2:]}",
            saturday.day,
            saturday.month,
        ),
        (
            f"{sunday.day}/{sunday.month}/{str(sunday.year)[2:]}",
            sunday.day,
            sunday.month,
        ),
    ]
    months_list = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    dog_dict = {
        "Dog": "",
        "Monday": 0,
        "Tuesday": 0,
        "Wednesday": 0,
        "Thursday": 0,
        "Friday": 0,
        "Saturday": 0,
        "Sunday": 0,
    }
    for dog in dog_list:
        dict_ = dog_dict.copy()
        dict_["Dog"] = [dog.name, dog.id]
        for a in dog.attendance:
            if a.iso_year == iso_year and a.iso_week == iso_week:
                if a.day == monday.day:
                    dict_["Monday"] = monday.day
                elif a.day == tuesday.day:
                    dict_["Tuesday"] = tuesday.day
                elif a.day == wednesday.day:
                    dict_["Wednesday"] = wednesday.day
                elif a.day == thursday.day:
                    dict_["Thursday"] = thursday.day
                elif a.day == friday.day:
                    dict_["Friday"] = friday.day
                dict_["Saturday"] = 0
                dict_[
                    "Sunday"
                ] = 0  #  append 2 exrra 0's for saturday  and sunday as no need to check them for this app
        if (
            dict_["Monday"] == 0
            and dict_["Tuesday"] == 0
            and dict_["Wednesday"] == 0
            and dict_["Thursday"] == 0
            and dict_["Friday"] == 0
        ):
            dict_.clear()
        else:
            week_dict.append(dict_.copy())
            dict_.clear()
    return render_template(
        "admin_view_week.html",
        user=current_user,
        week=week_dict,
        week_dates=week_dates,
        iso_week=iso_week,
        iso_year=iso_year,
        month_num=iso_month,
        iso_month=months_list[iso_month - 1],
    )


@admin.route("/admin_spreadsheet", methods=["GET"])
@admin.route("/admin_spreadsheet/<int:month_>", methods=["GET"])
@login_required
@admin_required
def admin_spreadsheet(month_=datetime.datetime.now().month):
    from .models import User, Attendance

    try:
        if int(month_) > 12 or int(month_) < 1:
            if int(month_) == 13:
                month_ = 1
            elif int(month_) == 0:
                month_ = 12
            else:
                month_ = datetime.datetime.now().month
    except ValueError:
        month_ = datetime.datetime.now().month
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    month = calendar.TextCalendar(calendar.MONDAY)
    current_date = [
        datetime.datetime.now().day,
        datetime.datetime.now().month,
        datetime.datetime.now().year,
    ]
    current_attendance = []
    all_attendance = dict()
    owners = User.query.all()
    year_ = datetime.datetime.now().year
    month_dates = [day for day in month.itermonthdays(year_, int(month_)) if day > 0]
    month_day_date = [
        (
            day,
            datetime.datetime.strptime(
                f"{day}/{month_}/{datetime.datetime.now().year} 12:00", "%d/%m/%Y %H:%M"
            ).strftime("%A"),
        )
        for day in month_dates
    ]
    for owner in owners:
        for dog in owner.dogs:
            attendance = Attendance.query.filter_by(
                month=month_, year=year_, dog=dog.id
            ).all()
            current_attendance = []
            for a in attendance:
                """ add booking type (full, half, walk, visit) when possible """
                current_attendance.append((a.day, a.id, dog.id, a.booking_type))

            current_attendance = set(current_attendance)
            current_attendance = list(current_attendance)
            current_attendance.sort(key=lambda tup: tup[1])

            """
            Creating a list of bookings, for each day of the month. bookings contains tuple of (0,0) for days of month where there is no booking.
            """

            current_attendance = {each[0]: each for each in current_attendance}
            result = [
                current_attendance.get(day, (0, 0, dog.id, 0)) for day in month_dates
            ]

            for i, r in enumerate(result):
                r = list(r)
                r.append(i + 1)
                result[i] = r

            """
            all_attendance contains all data required for the spreadsheet.
            """

            all_attendance[f"{dog.id}"] = {
                "DOGID": dog.id,
                "DOGNAME": dog.name,
                "OWNERID": owner.id,
                "ATTENDANCE": result,
            }
    """ 
        Generating days of month and comparing against days booked, returning days booked with
        additional character to be parsed by jinja
    """
    # today = datetime.datetime.now()
    # weekends = [6, 7, 13, 14, 20, 21, 27, 28, 34, 35]
    # month_date_cal = month.itermonthdays(year_, int(month_))

    # count = 0

    # for key in all_attendance.keys():
    #     month_days = []
    #     for day in month.itermonthdays(year_, int(month_)):
    #         count += 1
    #         if day > 0:
    #             day_to_add = f"{day}"
    #             calendar_date = f"{day}/{month_}/{year_} 12:00"
    #             calendar_date = datetime.datetime.strptime(
    #                 calendar_date, "%d/%m/%Y %H:%M"
    #             )
    #             for x in all_attendance[key]["ATTENDANCE"]:
    #                 if day in x[0]:
    #                     day_to_add = day_to_add + "a"  #   indicates day booked already
    #                 if today > calendar_date:
    #                     day_to_add = day_to_add + "l"  #   indicate day is in the past
    #                 elif count in weekends:
    #                     day_to_add = day_to_add + "w"  #   indicate day is weekend
    #                 month_days.append(f"{day_to_add}")
    #         else:
    #             month_days.append(day)
    #     all_attendance[key]["ATTENDANCE"] = month_days

    return render_template(
        "admin_spreadsheet.html",
        user=current_user,
        all_data=all_attendance,
        month_num=int(month_),
        month_name=(months[int(month_) - 1]).strip(),
        year=datetime.datetime.now().year,
        current_date=current_date,
        month_dates=month_day_date,
    )


@admin.route("/admin_spreadsheet_change", methods=["POST"])
@admin_required
def spreadsheet_change():
    if request.method == "POST":
        booking_id = int(request.form["id"])
        dog_id = int(request.form["dog"])
        day = int(request.form["day"])
        month = int(request.form["month"])
        change = int(request.form["change"])
        if booking_id != 0 and change == 0:
            from .functions import GetBooking

            booking = GetBooking(booking_id)
            from . import db

            db.session.delete(booking)
            db.session.commit()
            print("Booking ", booking.id, " deleted")
            return {"booking_id": 0}
        #  booking = GetBooking(int(request.form["booking_id"]))
        elif change > 0 and change <= 4:
            from .functions import GetDog, GetBooking
            from .models import Attendance

            if booking_id == 0:
                dog = GetDog(dog_id)
                dog.AddAttendance(
                    day=day,
                    month=month,
                    year=datetime.datetime.now().year,
                    assignment=0,
                    booking_type=change,
                )
                booking = Attendance.query.filter_by(
                    dog=dog_id, day=day, month=month, year=datetime.datetime.now().year
                ).first()
                print(
                    change,
                    " Booking ",
                    booking.id,
                    " added for ",
                    dog.name,
                    " ",
                    booking.booking_type,
                )
                booking = Attendance.query.filter_by(
                    dog=dog_id, day=day, month=month, year=datetime.datetime.now().year
                ).first()
                try:
                    return {"booking_id": booking.id}
                except:
                    return {"Error"}
            elif booking_id > 0:
                booking = GetBooking(booking_id)
                booking.booking_type = change
                from . import db

                db.session.commit()
                return {"booking_id": booking.id}

        return "Great Success"
    else:
        return None