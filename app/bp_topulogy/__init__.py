from flask import Blueprint

topulogy = Blueprint('topulogy', __name__)

from . import views, errors
from ..models import Permission


@topulogy.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
