# -*- coding: UTF-8 -*-
#!/usr/bin/env python
import os
from app.models import Graph
from app import create_app
from flask_socketio import SocketIO, emit
from flask import json

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """send server generated events to clients."""
    while True:
        socketio.sleep(2)
        graph = Graph.query.order_by(Graph.id.desc()).first()
        graph.generate_change(1)
        socketio.emit('bg', {'data': json.dumps(graph.serialize)}, namespace='/test')


@socketio.on('ping', namespace='/test')
def ping_pong():
    graph = Graph.query.order_by(Graph.id.desc()).first()
    graph.generate_change(1)
    emit('pong', {'data': json.dumps(graph.serialize)})


if __name__ == '__main__':
    socketio.run(app)
