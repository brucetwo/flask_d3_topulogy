# -*- coding: UTF-8 -*-
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach, paramiko
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from random import seed, randint
import forgery_py


class Permission:
    # FOLLOW = 0x01
    # COMMENT = 0x02
    # WRITE_ARTICLES = 0x04
    # MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            # 'User': (Permission.FOLLOW |
            #          Permission.COMMENT |
            #          Permission.WRITE_ARTICLES, True),
            # 'Moderator': (Permission.FOLLOW |
            #               Permission.COMMENT |
            #               Permission.WRITE_ARTICLES |
            #               Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, True)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Graph(db.Model):
    __tablename__ = 'graphs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    nodes = db.relationship('Node', backref='graph', lazy='dynamic')
    links = db.relationship('Link', backref='graph', lazy='dynamic')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'timestamp': [self.timestamp.strftime("%Y-%m-%d"), self.timestamp.strftime("%H:%M:%S")],
            'nodes': self.serialize_nodes,
            'links': self.serialize_links
        }

    @property
    def serialize_nodes(self):
        return [item.serialize for item in self.nodes]

    @property
    def serialize_links(self):
        return [item.serialize for item in self.links]

    @staticmethod
    def generate_fake(count=1):
        seed()
        for i in range(count):
            graph = Graph(timestamp=forgery_py.date.date(True))
            db.session.add(graph)
            db.session.commit()
        Node.generate_fake(5)
        Link.generate_fake(8)

    def generate_change(self, count):
        seed()
        node_count = Node.query.filter_by(graph=self).count()
        link_count = Link.query.filter_by(graph=self).count()
        for i in range(count):
            self.nodes[randint(0, node_count - 1)].change_state()
        # Node.generate_fake(1)
        # Link.generate_fake(1)
        # Node.delete_fake(1)
        # Link.delete_fake(1)


class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    target_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    type = db.Column(db.String(20))
    graph_id = db.Column(db.Integer, db.ForeignKey('graphs.id'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'source': self.source_id,
            'target': self.target_id,
            'type': self.id
        }

    @staticmethod
    def generate_fake(count=3):
        seed()
        graph = Graph.query.order_by(Graph.id.desc()).first()
        node_count = Node.query.filter_by(graph=graph).count()
        for i in range(count):
            source = Node.query.filter_by(graph=graph).offset(randint(0, node_count - 1)).first()
            target = Node.query.filter_by(graph=graph).offset(randint(0, node_count - 1)).first()
            if (source != target):
                link = Link(source=source,
                            target=target,
                            graph=graph
                            )
                db.session.add(link)
                db.session.commit()

    @staticmethod
    def delete_fake(count=1):
        seed()
        graph = Graph.query.order_by(Graph.id.desc()).first()
        link_count = Link.query.filter_by(graph=graph).count()
        if (link_count > 1):
            for i in range(count):
                link = Link.query.filter_by(graph=graph).offset(randint(0, link_count - 1)).first()
                link.graph = None
                db.session.delete(link)
                db.session.commit()


class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.Integer, primary_key=True)

    state = db.Column(db.Integer, default=0)
    pos_x = db.Column(db.Float)
    pos_y = db.Column(db.Float)
    type = db.Column(db.String(20), default='HOST')
    output = db.Column(db.Text())
    alias = db.Column(db.String(64), index=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('graphs.id'))
    sources = db.relationship('Link',
                              foreign_keys=[Link.target_id],
                              backref=db.backref('target', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    targets = db.relationship('Link',
                              foreign_keys=[Link.source_id],
                              backref=db.backref('source', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'type': self.type,
            'state': self.state,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'output': self.output,
            'alias': self.alias,
            'graph_id': self.graph_id
        }

    @staticmethod
    def generate_fake(count=3):
        seed()
        graph = Graph.query.order_by(Graph.id.desc()).first()
        for i in range(count):
            n = Node(state=randint(0, 3),
                     pos_x=randint(0, 1000),
                     pos_y=randint(0, 1000),
                     output=forgery_py.address.street_address(),
                     alias=forgery_py.name.full_name(),
                     graph=graph
                     )
            db.session.add(n)
            db.session.commit()

    @staticmethod
    def delete_fake(count=1):
        seed()
        graph = Graph.query.order_by(Graph.id.desc()).first()
        nodes = Graph.query.all()
        node_count = Node.query.filter_by(graph=graph).count()
        if (node_count > 1):
            for i in range(count):
                node = Node.query.filter_by(graph=graph).offset(randint(0, node_count - 1)).first()
                for n in nodes:
                    if (node.is_linked_by(n) or node.is_linking(n)):
                        node.unlink(n)
                        n.unlink(node)
                node.graph = None
                db.session.delete(node)
                db.session.commit()

    def change_state(self):
        seed()
        self.state = randint(0, 3)
        db.session.add(self)
        db.session.commit()

    def link(self, node):
        if not self.is_linking(node):
            link = Link(source=self, target=node)
            db.session.add(link)

    def unlink(self, node):
        link = self.targets.filter_by(target_id=node.id).first()
        if link:
            db.session.delete(link)

    def is_linking(self, node):
        return self.targets.filter_by(
            target_id=node.id).first() is not None

    def is_linked_by(self, node):
        return self.sources.filter_by(
            source_id=node.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.alias


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
                # if self.email is not None and self.avatar_hash is None:
                #     self.avatar_hash = hashlib.md5(
                #         self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


class Ssh(db.Model):
    __tablename__ = 'sshs'
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String)
    port = db.Column(db.Integer)
    username = db.Column(db.String)
    password = db.Column(db.String)
    command = db.Column(db.String)
    regexSshs = db.relationship('RegexSsh', backref='ssh', lazy='dynamic')

    @staticmethod
    def execq(hostname, port, username, password, command):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, port, username, password)
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.readlines())
            if stdout.readlines():
                return stdout.readlines()
        except paramiko.SSHException as e:
            print(e)
            return
        ssh.close()

class RegexSsh(db.Model):
    # pattern,state,type,output,alias,pos_x,pos_y
    __tablename__ = 'regexSshs'
    id = db.Column(db.Integer, primary_key=True)
    ssh_id = db.Column(db.Integer, db.ForeignKey('sshs.id'))
    pattern = db.Column(db.String)
    g_state = db.Column(db.Integer)
    g_pos_x = db.Column(db.Integer)
    g_pos_y = db.Column(db.Integer)
    g_type = db.Column(db.Integer)
    g_output = db.Column(db.Integer)
    g_alias = db.Column(db.Integer)

    @staticmethod
    def matches(readLines, g_alias, g_state, g_pos_x, g_pos_y, g_type, g_output):
        pass


db.event.listen(Post.body, 'set', Post.on_changed_body)
