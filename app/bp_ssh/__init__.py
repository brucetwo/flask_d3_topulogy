from flask import Blueprint

bp_ssh = Blueprint('bp_ssh', __name__)

from . import views
