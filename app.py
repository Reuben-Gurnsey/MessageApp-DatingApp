from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import os
app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.data_b'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app)
data_b = SQLAlchemy()
rooms = {}
data_b.init_app(app)

from view import view
from authenticate import authenticate
app.register_blueprint(view)
app.register_blueprint(authenticate)

# Initialize and configure LoginManager
login_manager = LoginManager()
login_manager.login_view = 'authenticate.login'
login_manager.init_app(app)

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

@app.route("/chats", methods=["POST", "GET"])
def chats():
    session.clear()
    from models import User
    #users = User.query.all()
    users = get_potential_friends()
    
    if request.method == "POST":
        name = current_user.first_name 
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        room = code
        if not name:
            return render_template("chats.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("chats.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("chats.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("chatroom", user=current_user, users=users))

    return render_template("chats.html", user=current_user, users=users)

def get_room(room_code):
    from models import Chat
    return Chat.query.filter_by(code=room_code).first()
    
    


@app.route("/friendsList", methods=["POST", "GET"])
def friendsList():
    session.clear()
    from models import User, Chat, Friend
    from authenticate import get_friends, get_friendship_id, get_friend_obj
    friends = get_friends()
    if request.method == "POST":
        name = current_user.first_name 
        room = request.form.get("friend_ID")
        
        friend_id = get_friendship_id(current_user.id, room)
        #check if socket is in use. If True, join socket, If False, create new room connection.
        if friend_id not in rooms:
            rooms[friend_id] = {"members": 0, "messages": []}
            retrieve_messages(friend_id)
            #check if chat exists in Database, otherwise crate new Chat.
            if not get_room(friend_id):
                #new_chat = Chat(code=room)
                print(friend_id)
                new_chat = Chat(code=friend_id)
                #new_chat = Chat(code=Friend.id)
                data_b.session.add(new_chat)
                data_b.session.commit()
        
        
        #join room socket
        session["room"] = friend_id
        session["name"] = name
        #retrieve_messages(room)
        return redirect(url_for("chatroom", user=current_user, friends=friends, friend_name=room))

    return render_template("friendsList.html", user=current_user, friends=friends)


@app.route("/add_friend", methods=["POST"])
def add_friend():
    from models import User, Friend
    if not current_user.id:
        flash('You must be logged in to add a friend.', 'error')
        return redirect(url_for('chats'))

    friend_id = request.form.get("friend_id")
    if friend_id:
        #logic to ensure that the friend being added is not already in the current user's friend list
        if not Friend.query.filter_by(user_id=current_user.id, friend_id=friend_id).first():
            new_friend = Friend(user_id=current_user.id, friend_id=friend_id)
            data_b.session.add(new_friend)
            data_b.session.commit()
            flash('Friend added successfully!', 'success')
        else:
            flash('This user is already your friend.', 'warning')
    else:
        flash('Invalid friend ID.', 'error')

    return redirect(url_for('chats'))

@app.route("/remove_friend", methods=["POST"])
def remove_friend():
    from models import Friend, User
    friend_id = request.form.get("friend_id")
    if current_user.id == Friend.user_id or current_user.id == friend_id:
        User.query.filter(User.id == friend_id).delete()
        data_b.session.commit()
        flash('Friend removed', 'success')
    else:
        flash('Unable to remove friend.', 'error')
    flash('Friend removed', 'success')
    Friend.query.filter(Friend.id == friend_id).delete()
    data_b.session.commit()
    return redirect(url_for('chats'))

@app.route("/potential_friends", methods=["POST"])
def get_potential_friends():
    from models import User, Friend
    
    friend_ids_subquery = data_b.session.query(Friend.friend_id).filter(Friend.user_id == current_user.id).union(data_b.session.query(Friend.user_id).filter(Friend.friend_id == current_user.id))
    #friend_ids_subquery = data_b.session.query(Friend.friend_id).filter(Friend.user_id == current_user.id)
    non_friends = User.query.filter(User.id != current_user.id,~User.id.in_(friend_ids_subquery)).all()

    
    
    return non_friends
  

#@authenticate.route('/potential_friend', methods=['GET', 'POST'])
#def profile_page():
#   from models import User, Friend
#    #friends = Friend.query.filter_by(user_id=current_user.id).all()
#    #friends = User.query.filter(User.id == Friend.friend_id).all()
#    users = User.query.join(Friend, User.id == Friend.friend_id).filter(Friend.user_id == current_user.id).all()
#    return render_template("profile.html", user=current_user, users=friends)
    



@app.route("/chatroom")
def chatroom():
    from models import User
    from authenticate import get_friend_obj
    room = session.get("room")
    friend_id = request.args.get("friend_name")
    friend_obj = get_friend_obj(friend_id)
    #friend_id = session.get(friend_id)
    #friend_obj = get_friend_obj(friend_name)
    #friend_name = friend_id.first_name
    print(friend_obj.first_name)
    
    #friend_obj = User.query.filter_by(id=)
    #/////////FIX THIS, Change to friend_obj needs to query the chat room, and get the members ids that arent the current_user, then get that object and get the first_name from User table, then return that string.
    #friend_obj = User.query.filter_by(id=room).first()
    #friend_name = friend_obj.first_name
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("chats"))

    return render_template("chatroom.html", code=room, messages=rooms[room]["messages"], user=current_user, friend_name=friend_obj.first_name)

def store_message(msg, room):
    import json
    from models import Message, Chat
    json_data = json.dumps(msg)
    new_message = Message(content=json_data, user_id=current_user.id, chat_id=room)
    data_b.session.add(new_message)
    data_b.session.commit()

@socketio.on("history")
def retrieve_messages(chat_id):
    import json
    from sqlalchemy import desc
    from models import Message, Chat
    session.clear()
    last_10_rows = data_b.session.query(Message).filter_by(chat_id=chat_id).order_by(desc(Message.id)).limit(10).all()
    if last_10_rows:
        for i in last_10_rows:
            data = json.loads(i.content)
            print(data)
            socketio.send(data, to=chat_id)
            rooms[chat_id]["messages"].append(data)
    return

@socketio.on("message")
def message(data):
    from models import Message
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    
    store_message(content, room)
 
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    print("Connected")
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

login_manager = LoginManager()
login_manager.login_view = 'authenticate.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_database(app):
    if not os.path.exists(os.path.join('gymapp', 'database.data_b')):
        with app.app_context():
            data_b.create_all()
        print("Database created")

create_database(app)

if __name__ == "__main__":
    socketio.run(app, debug=True)