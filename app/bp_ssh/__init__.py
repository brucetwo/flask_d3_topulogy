from flask import Blueprint

bp_ssh = Blueprint('ssh', __name__)

from . import views
