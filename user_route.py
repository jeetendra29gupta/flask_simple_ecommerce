from flask import Blueprint, render_template

from models import Session, Product

user_router = Blueprint('user', __name__)


@user_router.route('/')
def index():
    with Session() as session_db:
        rows = session_db.query(Product).all()
    return render_template('index.html', rows=rows)
