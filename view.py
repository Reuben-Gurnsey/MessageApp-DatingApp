from flask import Blueprint, render_template, request, flash, jsonify, session
from flask_login import login_required, current_user
from models import Post, Message, User, Friend
from app import data_b, socketio
import json
from flask_socketio import SocketIO, send, emit
view = Blueprint('view', __name__)

@view.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        post = request.form.get('post')
        if len(post) <1:
            flash('post too short', category='error')
        else:
            new_post = Post(data=post, user_id=current_user.id)
            data_b.session.add(new_post)
            data_b.session.commit()
            flash('Post created.', category='success')
    return render_template("home.html", user=current_user)

@view.route('/delete-post', methods=['POST'])
def delete_post():
    post = json.loads(request.data)
    postId = post['post']
    post = Post.query.get(postId)
    if post.user_id == current_user.id:
        data_b.session.delete(post)
        data_b.session.commit()
    return jsonify({})



