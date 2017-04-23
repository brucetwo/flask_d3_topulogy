# coding=utf-8
from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, jsonify, json
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from datetime import datetime
from werkzeug import security
from . import topulogy
from .forms import PostForm
from .. import db, files
from ..models import Permission, Role, User, Post, Graph, Node
from ..decorators import admin_required


@topulogy.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@topulogy.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@topulogy.route('/', methods=['GET', 'POST'])
@login_required
def index():
    show_force = False
    graph = None
    # graph = Graph.query.first_or_404()
    # show_force = bool(request.cookies.get('show_force', ''))
    return render_template('index.html', graph=graph, show_force=show_force)


@topulogy.route('/output/<int:id>', methods=['GET', 'POST'])
@login_required
def output(id):
    node = Node.query.get_or_404(id)
    return render_template('output.html', node=node)


@topulogy.route('/gain/<int:id>', methods=['GET', 'POST'])
@login_required
def gain(id):
    node = Node.query.get_or_404(id)
    node.change_output()
    y = int(node.output)
    x = datetime.now()
    data=json.dumps({'x':x,'y':y})
    return data


@topulogy.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'codefile' in request.files:
        filename = files.save(request.files['codefile'])
        return redirect(url_for('.show', name=filename))
    return render_template('dispatch/dispatch.html', output='...')


@topulogy.route('/codefile/<name>')
def show(name):
    if name is None:
        abort(404)
    url = files.url(name)
    file_object = open(url)
    try:
        output = file_object.read()
    finally:
        file_object.close()
    return render_template('dispatch/dispatch.html', output=output)


@topulogy.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@topulogy.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('dispatch/post.html', post=post)


@topulogy.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)
