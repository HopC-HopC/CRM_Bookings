from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import password_strength

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        from .models import User

        account = User.query.filter_by(username=username).first()
        if account:
            if check_password_hash(account.password, password):
                flash(f"Successful Log In - {account.username}", category="success")
                login_user(account, remember=True)
                if account.role == "user":
                    return redirect(url_for("views.customer_home"))
                elif account.role == "admin":
                    return redirect(url_for("admin.admin_view_week"))
            else:
                flash("Incorrect Password", category="error")
        else:
            flash(f"No user named {username}!", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        from .models import User
        from . import db

        # flash('Creating Account', category='blah')
        username = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        phone = request.form.get("phone")
        address_1 = request.form.get("address")
        post_code = request.form.get("post_code")

        usercheck = User.query.filter_by(username=username).first()
        emailcheck = User.query.filter_by(email=email).first()

        pass_validation = PasswordValidation(password1)
        pass_dupe = False

        if usercheck:
            flash("Username already taken.", category="error")
            username = ""
        elif emailcheck:
            flash("Email already registered.", category="error")
            email = ""
        elif password1 != password2:
            flash("Passwords do not match.", category="error")
            pass_dupe = True
        elif not pass_validation:
            flash(
                "Your password is too weak; please use an uppercase character, number and special character (!, ?, _, -, etc) at minimum!",
                category="error",
            )
        check = (
            len(username) > 2
            and len(email) > 5
            and pass_validation == True
            and pass_dupe == False
        )
        if check == True:
            flash("Account creation success!", category="success")

            account = User(
                username=username,
                email=email,
                password=generate_password_hash(password1, method="sha256"),
            )

            if first_name is not None and len(first_name) > 2:
                account.first_name = first_name
            if surname is not None and len(surname) > 2:
                account.surname = surname
            if phone is not None and len(phone) > 2:
                account.phone = phone
            if address_1 is not None and len(address_1) > 2:
                account.address_1 = address_1
            if post_code is not None and len(post_code) > 2:
                account.post_code = post_code

            db.session.add(account)
            db.session.commit()
            flash(
                f"Username: {account.username}, Email: {account.email}",
                category="success",
            )
            flash(
                'Please confirm your account details (name and contact information) on your "My Account" page.',
                category="success",
            )
            login_user(account, remember=True)
            return redirect(url_for("views.add_my_dogs"))
        else:
            flash("Account creation error!", category="error")

    return render_template("signup.html", user=current_user)


def PasswordValidation(password: str) -> bool:
    policy = password_strength.PasswordPolicy.from_names(
        length=8, uppercase=1, numbers=1, special=1, nonletters=2
    )
    if len(policy.test(password)) > 0:
        #   if password is too weak, len will be > 0
        #   policy.test() returns a list of failures
        #   based on the configuration above.
        return False
    else:
        return True