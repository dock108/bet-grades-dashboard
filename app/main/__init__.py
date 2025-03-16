from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import main_routes  # noqa: F401 