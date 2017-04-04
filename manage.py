#!/usr/bin/env python
import os
import paramiko
from app.models import Graph, Node, Link
from app import create_app, db
from app.models import User, Role, Permission, Post
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def background_thread():
    """send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(2)
        Graph.generate_fake(1)
        Node.generate_fake(15)
        Link.generate_fake(24)
        graph = Graph.query.order_by(Graph.timestamp.desc()).first().to_json();
        print(graph)
        socketio.emit('my_response', {'graph': graph}, namespace='/test')

def collect_date():
    total_pattern = "^(\d+) job step\(s\) in queue, (\d+) waiting, (\d+) pending, (\d+) running, (\d+) held, (\d+) preempted"
    total_prog = re.compile(total_pattern)
    total_prog_result = total_prog.match(result_lines[-2])
    llq_summary = dict()
    llq_summary['in_queue'] = total_prog_result.group(1)
    llq_summary['waiting'] = total_prog_result.group(2)
    llq_summary['pending'] = total_prog_result.group(3)
    llq_summary['running'] = total_prog_result.group(4)
    llq_summary['held'] = total_prog_result.group(6)
    llq_summary['preempted'] = total_prog_result.group(5)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission,
                Post=Post)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def run():
    """Run in socketIO mode."""
    socketio.run(app,
                 host='127.0.0.1',
                 port=5000)


if __name__ == '__main__':
    manager.run()
