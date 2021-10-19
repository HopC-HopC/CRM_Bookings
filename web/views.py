from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import calendar
from datetime import datetime


views = Blueprint('views',__name__)





# access function to autogenerate bookings for demos.

@views.route('/autogen')
def autogen():
    from .autogen import AutoGen
    AutoGen()
    return redirect(url_for('views.my_account'))


# access function to delete all bookings, for testing, demos, errors.

@views.route('/delbook')
def delbook():
    from .autogen import ClearBookings
    ClearBookings()
    return redirect(url_for('views.my_account'))


@views.route('/notes', methods=['GET','POST'])
@login_required
def notes():
    if request.method == 'POST':
        new_note = request.form.get('note')
        if len(new_note) < 1:
            flash('No note entered', category='error')
        elif len(new_note) < 5:
            flash('Note too short', category='error')
        else:
            from .models import Note
            from . import db
            note = Note(data=new_note, owner=current_user.id)
            # current_user.notes.append(note)
            db.session.add(note)
            db.session.commit()
            flash(f'Thanks {current_user.username}, your note has been added', category='success')
    return render_template("home.html", user=current_user)

@views.route('/note/remove/<note_id>', methods=['GET','POST'])
@login_required
def note_remove(note_id):
    try:  
        if int(note_id) >= 0 and (current_user.id in [i.owner for i in current_user.notes] or current_user.role=='admin'):
            from .models import Note
            note_to_delete = Note.query.filter_by(id=int(note_id)).first()
            if note_to_delete:
                from . import db
                db.session.delete(note_to_delete)
                db.session.commit()
                flash(f'Note has been removed successfully.', category='success')
        else: 
            flash(f'You do not have permission to access that function.', category='error')
    except ValueError:
        flash('Error removing message.', category='error')
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_home'))

    else:
        return redirect(url_for('views.customer_home'))

@views.route('/index')
def index():
    return redirect(url_for('views.customer_home'))

@views.route('/')
@views.route('/home', methods=['GET','POST'])
@login_required
def customer_home():
    if current_user.role == 'user':
        pass
    else:
        return redirect(url_for('views.my_account'))
    if request.method == 'POST':
        new_note = request.form.get('note')
        if len(new_note) < 1:
            flash('No note entered', category='error')
        elif len(new_note) < 5:
            flash('Note too short', category='error')
        else:
            from .models import Note
            from . import db
            note = Note(data=new_note, owner=current_user.id)
            # current_user.notes.append(note)
            db.session.add(note)
            db.session.commit()
            flash(f'Thanks {current_user.username}, your note has been added', category='success')
  
    import datetime
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day
    current_hour = datetime.datetime.now().hour
    iso_week = datetime.date(current_year, current_month, current_day).isocalendar()[1]
    iso_year = datetime.date(current_year, current_month, current_day).isocalendar()[0]
    for_date_monday = f'{iso_year}-W{iso_week}'
    monday = datetime.datetime.strptime(for_date_monday + '-1', '%G-W%V-%u')
    friday = monday + datetime.timedelta(days=6)

    friday_date = f'{friday.day}/{friday.month}/{friday.year} 12:00'
    # friday_date = datetime.datetime.strptime(friday_date, "%d/%m/%Y %H:%M")
    if datetime.datetime.strptime(f'{current_day}/{current_month}/{current_year} {current_hour}:01', "%d/%m/%Y %H:%M") > datetime.datetime.strptime(f'{friday_date}', "%d/%m/%Y %H:%M"):
        iso_week += 1
    dog_dict= {
        'Dog': '',
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0,
        'Sunday': 0,
        }
    for_date_monday = f'{iso_year}-W{iso_week}'
    monday = datetime.datetime.strptime(for_date_monday + '-1', '%G-W%V-%u')
    tuesday = monday + datetime.timedelta(days=1)
    wednesday =  monday + datetime.timedelta(days=2)
    thursday = monday + datetime.timedelta(days=3)
    friday = monday + datetime.timedelta(days=4)
    saturday = monday + datetime.timedelta(days=5)
    sunday = monday + datetime.timedelta(days=6)
    iso_year=thursday.year
    iso_month=thursday.month
    months_list = ['January','February','March','April','May','June','July','August','September','October','November','December']
    week_dates = [f'{monday.day}/{monday.month}/{str(monday.year)[2:]}',f'{tuesday.day}/{tuesday.month}/{str(tuesday.year)[2:]}',f'{wednesday.day}/{wednesday.month}/{str(wednesday.year)[2:]}',f'{thursday.day}/{thursday.month}/{str(thursday.year)[2:]}',f'{friday.day}/{friday.month}/{str(friday.year)[2:]}',f'{saturday.day}/{saturday.month}/{str(saturday.year)[2:]}',f'{sunday.day}/{sunday.month}/{str(sunday.year)[2:]}']

    week_dict = []
    for dog in current_user.dogs:
        dict_ = dog_dict.copy()
        dict_['Dog'] = dog.name
        for bookings in dog.attendance:
            if bookings.iso_week == iso_week and bookings.iso_year == iso_year:
                if bookings.day == monday.day:
                    dict_['Monday'] = monday.day
                elif bookings.day == tuesday.day:
                    dict_['Tuesday'] = tuesday.day
                elif bookings.day == wednesday.day:
                    dict_['Wednesday'] = wednesday.day
                elif bookings.day == thursday.day:
                    dict_['Thursday'] = thursday.day
                elif bookings.day == friday.day:
                    dict_['Friday'] = friday.day
                dict_['Saturday'] = 0
                dict_['Sunday'] = 0 
        week_dict.append(dict_.copy())
        dict_.clear()
    return render_template("user_home.html", user=current_user, week=week_dict, week_dates=week_dates, iso_week=iso_week, iso_year = iso_year, iso_month=months_list[iso_month - 1])


@views.route('/my_account', methods=['GET','POST'])
@login_required
def my_account():
    if request.method == 'POST':
        from . import db
        first_name = request.form.get('first_name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        address_1 = request.form.get('address_1')
        post_code = request.form.get('post_code')
        phone = request.form.get('phone')
        if first_name and first_name is not current_user.first_name:
            current_user.first_name = first_name
        if surname and surname is not current_user.surname:
            current_user.surname = surname
        if email and email is not current_user.email:
            current_user.email = email
        if address_1 and address_1 is not current_user.address_1:
            current_user.address_1 = address_1
        if post_code and post_code is not current_user.post_code:
            current_user.post_code = post_code
        if phone and phone is not current_user.phone:
            current_user.phone = phone
        db.session.commit()
    return render_template("account.html", user=current_user)


@views.route('/add_my_dogs', methods=['GET','POST'])
@login_required
def add_my_dogs():
    if request.method == 'POST':
        dog_name = request.form.get('dog_name')
        dog_age = request.form.get('dog_age')
        dog_breed = request.form.get('dog_breed')
        dog_gender = request.form.get('dog_gender')
        if not dog_name:
            flash('No name entered', category='error')
        elif not dog_age:
            flash('No age entered', category='error')
        elif not dog_breed:
            flash('No breed entered', category='error')
        elif not dog_gender:
            flash('No gender entered', category='error')
        else:
            from .models import Dog
            from . import db
            new_dog = Dog(name=dog_name, age=dog_age, breed=dog_breed, gender=dog_gender, owner=current_user)
            db.session.add(new_dog)
            db.session.commit()
            flash(f'{new_dog.name} added successfully.', category='success')
            return redirect(url_for('views.my_dogs'))
    return render_template('my_dogs_add.html', user=current_user)


@views.route('/my_dogs', methods=['GET','POST'])
@login_required
def my_dogs():
    x = 0
    try:
        for dog in current_user.dogs:
            x+=1
    except:
        x = 0
    if x == 0:
        return redirect(url_for('views.add_my_dogs'))
    else:
        return render_template('my_dogs.html', user=current_user)

@views.route('/bookings', methods=['GET','POST'])
@views.route('/bookings/<month_>', methods=['GET','POST'])
@login_required
def bookings(month_=datetime.now().month):
    from . import db
    from .models import Attendance
    # monday_list = db.session.query(Attendance).all()

    if request.method == 'POST':
        dates= []
        dates = (request.form.getlist('checkbox'))
        if len(dates) > 0:
            message_ = f'Thanks {current_user.username}! '
        else:
            return redirect(url_for('views.bookings'))
        dog_amount = 1
        for dog in current_user.dogs:
            if dog_amount > 1:
                message_ = message_ + f', {dog.name}'
            else: 
                message_ = message_ + f'{dog.name}'
            dog_amount += 1
        message_ = message_ + ' booked in for '
        for date in dates:
            if date == dates[-1]:
                message_ = message_ + f'and {date}/{month_}. '
            else:
                message_ = message_ + f'{date}/{month_}, '
            for dog in current_user.dogs:
                dog.AddAttendance(date,month_,datetime.now().year)
        
        flash(message_, category='success')


    try:
        if int(month_) > 12 or int(month_) < 1:
            if int(month_) == 13:
                month_ = 1
            elif int(month_) == 0:
                month_ = 12
            else:
                month_=datetime.now().month
    except ValueError:
        month_=datetime.now().month
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    month = calendar.TextCalendar(calendar.MONDAY)
    month_days = []
    current_date = [datetime.now().day,datetime.now().month,datetime.now().year]
    current_attendance = []
    for dog in current_user.dogs:
        for a in dog.attendance:
            if int(a.month) == int(month_):
                current_attendance.append(a.day)
    
    ''' 
        Generating days of month and comparing against days booked, returning days booked with
        additional character to be parsed by jinja
    '''
    
    year_ = datetime.now().year
    today = datetime.now()
    current_attendance = set(current_attendance)
    weekends = [6,7,13,14,20,21,27,28,34,35]
    count = 0
    for day in month.itermonthdays(year_,int(month_)):
        count += 1
        if day > 0:
            day_to_add = f'{day}'
            calendar_date = f'{day}/{month_}/{year_} 12:00'
            calendar_date = datetime.strptime(calendar_date, "%d/%m/%Y %H:%M")
            if day in current_attendance:
                day_to_add = day_to_add + 'a'    #   indicates day booked already
            if today > calendar_date:
                day_to_add = day_to_add +'l'   #   indicate day is in the past
            elif count in weekends:
                day_to_add = day_to_add +'l'   #   indicate day is weekend
            month_days.append(f'{day_to_add}')
        else:
            month_days.append(day)
        # if day < current_day:
        #   month_days.append(f'{day}l')    #   indicate day is in the past
    return render_template('calendar.html', user=current_user, calendar=month_days, month_num=int(month_),month_name=(months[int(month_) - 1]).strip(), year=datetime.now().year, current_date=current_date)



@views.route('/bookings/cancel/<month_>/<day_>', methods=['GET','POST'])
@login_required
def booking_cancel(month_, day_):
    if int(month_) > 0 and int(day_) > 0:
        from .models import Attendance
        from . import db
        for dog in current_user.dogs:
            day = Attendance.query.filter_by(dog=dog.id, month=int(month_), day=int(day_), year=datetime.now().year).first()
            if day:
                db.session.delete(day)
                db.session.commit()
                flash(f'Booking for {dog.name} on {day_}/{month_} cancelled', category='error')
    else:
        pass
    return redirect(url_for('views.bookings') + f'/{month_}')

