from app import data_b
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import date
today=date.today()
class User(data_b.Model, UserMixin):
    id = data_b.Column(data_b.Integer, primary_key=True)
    email = data_b.Column(data_b.String(100), unique=True)
    password = data_b.Column(data_b.String(100))
    first_name = data_b.Column(data_b.String(100))
    posts = data_b.relationship("Post")
    #friends = data_b.relationship('Friend', backref='user', lazy=True)
    friends = data_b.relationship('Friend', foreign_keys='Friend.user_id', backref='user', lazy=True)
    friends_of = data_b.relationship('Friend', foreign_keys='Friend.friend_id', backref='friend', lazy=True)
    messages = data_b.relationship('Message', backref='user', lazy=True)



class Post(data_b.Model):
    id = data_b.Column(data_b.Integer, primary_key=True)
    data = data_b.Column(data_b.String(15000))
    date = data_b.Column(data_b.DateTime(timezone=True), default=today)
    user_id = data_b.Column(data_b.Integer, data_b.ForeignKey('user.id'))

class Friend(data_b.Model):
    id = data_b.Column(data_b.Integer, primary_key=True)
    user_id = data_b.Column(data_b.Integer, data_b.ForeignKey('user.id'), nullable=False)
    friend_id = data_b.Column(data_b.Integer, data_b.ForeignKey('user.id'), nullable=False)
    
class Message(data_b.Model):
    id = data_b.Column(data_b.Integer, primary_key=True)
    content = data_b.Column(data_b.String(500), nullable=False)
    user_id = data_b.Column(data_b.Integer, data_b.ForeignKey('user.id'), nullable=False)
    chat_id = data_b.Column(data_b.Integer, data_b.ForeignKey('chat.id'), nullable=False)

class Chat(data_b.Model):
    id = data_b.Column(data_b.Integer, primary_key=True)
    code = data_b.Column(data_b.String(10), unique=True, nullable=False)
    messages = data_b.relationship('Message', backref='chat', lazy=True)
    
#code = data_b.Column(data_b.String(10), unique=True, nullable=False)