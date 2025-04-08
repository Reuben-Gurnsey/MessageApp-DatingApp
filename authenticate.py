from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from models import User, Message, Friend
from werkzeug.security import generate_password_hash, check_password_hash
from app import data_b
from flask_login import login_user, login_required, logout_user, current_user
authenticate = Blueprint('authenticate', __name__)



@authenticate.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Welcome back! Login Successful.', category='success')
                login_user(user, remember=True)
                return redirect(url_for("view.home"))
            else:
                flash('Wrong password, please try again.', category='error')
        else:
            flash('Email is not registered.', category='error')
    
    
    return render_template("login.html", user=current_user)
@authenticate.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('authenticate.login'))
    

@authenticate.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email exists already.')
        return redirect(url_for("authenticate.sign_up"))

    if request.method == "POST":
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1= request.form.get('password1')
        password2= request.form.get('password2')
        if password1 != password2:
            flash("Passwords do not match", category="Error")
            return redirect(url_for("authenticate.sign_up"))

        elif len(password1) <6:
            flash("Password needs to be greater than 6 characters", category="Error")
            return redirect(url_for("authenticate.sign_up"))
        elif len(email)<4:
            flash("Email needs to be greater than 3 characters", category="Error")
            return redirect(url_for("authenticate.sign_up"))
        elif len(first_name) <2:
            flash("First name needs to be greater than 2 characters", category="Error")
            return redirect(url_for("authenticate.sign_up"))
        else:
            new_user = User(email=email, first_name=first_name, password = generate_password_hash(password1, method='sha256'))
            data_b.session.add(new_user)
            data_b.session.commit()
            login_user(new_user, remember=True)
            flash("Account successfully created!", category="Success")
            return redirect(url_for("view.home"))
    
    return render_template("signup.html", user=current_user)


def get_friendship_id(current_user_id, friend_user_id):
    # Query to get the id of the friend row where the current user is the initiator
    from sqlalchemy import or_
    friend_relationship = data_b.session.query(Friend.id).filter(or_(
            (Friend.user_id == current_user_id) & (Friend.friend_id == friend_user_id),
            (Friend.user_id == friend_user_id) & (Friend.friend_id == current_user_id))).first()

    if friend_relationship:
        return friend_relationship.id
    return
    




def get_friends():
   #friends = User.query.join(Friend, User.id == Friend.friend_id).filter(Friend.user_id == current_user.id).all()
   #friends = User.session.query(Friend.friend_id).filter(Friend.user_id == current_user.id).union(data_b.session.query(Friend.user_id).filter(Friend.friend_id == current_user.id))
   #friends = User.query.join(Friend, User.id == Friend.friend_id).filter(Friend.user_id == current_user.id)
    friends_initiator = data_b.session.query(User).join(Friend, User.id == Friend.friend_id).filter(Friend.user_id == current_user.id)
    friends_recipient = data_b.session.query(User).join(Friend, User.id == Friend.user_id).filter(Friend.friend_id == current_user.id)

    #This queries the a USER id object
    friends = friends_initiator.union(friends_recipient).all()
    return friends

def get_friend_obj(friend):
    #friend_id = Friend.query.filter(Friend.friend_id == friend_id).first()
    #friend_id2 = Friend.query.filter(Friend.user_id == friend_id).first()
    friend_obj = User.query.get(friend)
    return friend_obj

def get_user_id():
    return current_user.id

@authenticate.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    friends = get_friends()
    return render_template("profile.html", user=current_user, friends=friends)
    



