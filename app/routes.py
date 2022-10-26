from base64 import decode
from lib2to3 import pytree
from flask import render_template, flash, redirect, request, url_for, session, make_response
from app import app, db
from app.models import *
from app.forms import LoginForm, RegisterForm
from datetime import datetime, timedelta
from app.utils import get_barcode_from_imagedata
from flask_login import current_user, login_user, logout_user, login_required
import requests

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Profile.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=True)
        return redirect(url_for('index'))

    return render_template('login.html', form=form, nonav=True)

@app.route('/register')
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = Profile(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        login_user(user, remember=True)
        return redirect(url_for('index'))

    return render_template('register.html', form=form, nonav=True)

@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@app.route('/scan_barcode', methods=['POST'])
@login_required
def upload():
    data = request.data

    barcode = get_barcode_from_imagedata(data)
    if not barcode:
        return 'no barcode was detected', 400

    return redirect(url_for('search_barcode', barcode=barcode.data.decode()))

@app.route('/barcode/search/<barcode>')
@login_required
def search_barcode(barcode):
    url = f'https://off:off@world.openfoodfacts.net/api/v2/product/{barcode}'

    try:
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        return f'there was an error: {e}'

    return render_template('scanned.html', barcode=barcode, data=data)