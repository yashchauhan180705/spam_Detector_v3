"""
Home Blueprint - Handles the landing page and project overview.
"""
from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    """Render the home page with project overview."""
    return render_template('home.html')


