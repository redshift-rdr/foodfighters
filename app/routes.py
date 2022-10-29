from base64 import decode
from lib2to3 import pytree
import profile
from unicodedata import category
from flask import render_template, flash, redirect, request, url_for, session, make_response
from app import app, db
from app.models import *
from app.forms import LoginForm, RegisterForm, addMealForm
from datetime import date, timedelta
from app.utils import get_barcode_from_imagedata
from flask_login import current_user, login_user, logout_user, login_required
import requests

@app.route('/')
@app.route('/index')
@login_required
def index():
    return redirect(url_for('diary'))
    #return render_template('index.html')

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

@app.route('/diary', defaults={'indate':''}, methods=['GET', 'POST'])
@app.route('/diary/<indate>', methods=['GET', 'POST'])
@login_required
def diary(indate : str):
    """
        args:
            date - str, optional - needs to be a string date in ISO format e.g. '2022-10-29'
    """
    if not indate:
        date_select = date.today()
    else:
        date_select = date.fromisoformat(indate)

    diary_entry = db.session.query(DiaryEntry).filter_by(day=date_select).one_or_none()
    if not diary_entry:
        diary_entry = DiaryEntry(day=date_select, profile=current_user)
        db.session.add(diary_entry)
        db.session.commit()

    form = addMealForm()
    if form.validate_on_submit():
        add_meal = Meal(category=form.category.data, diaryentry=diary_entry)
        db.session.add(add_meal)
        db.session.commit()

    return render_template('diary.html', diary_entry=diary_entry, form=form)

@app.route('/addfood/<meal_id>')
@login_required
def addfood(meal_id):
    meal = db.session.query(Meal).filter_by(id=meal_id).one_or_none()

    if not meal:
        return redirect(url_for('index'))
    
    return render_template('addfood.html', meal=meal)

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