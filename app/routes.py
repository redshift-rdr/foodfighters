from base64 import decode
from lib2to3 import pytree
import profile
from unicodedata import category
from flask import render_template, flash, redirect, request, url_for, session, make_response, jsonify
from app import app, db
from app.models import *
from app.forms import LoginForm, RegisterForm, addMealForm
from datetime import date, timedelta
from app.utils import get_barcode_from_imagedata, search_barcode
from flask_login import current_user, login_user, logout_user, login_required

def add_off_data_as_food(data):
    """
        TODO: redo this - 
    """
    #try:
    product_name = data['product']['product_name']
    brand = data['product']['brands']
    barcode = data['code']
    size = data['product']['serving_quantity']

    nutrient_data = data['product']['nutriments']
    nutrition_records = {
        "calories": nutrient_data['energy-kcal_serving'],
        "fat": nutrient_data['fat_serving'],
        "sugar": nutrient_data['sugars_serving'],
        "salt": nutrient_data['salt_serving'],
        "protein": nutrient_data['proteins_serving'],
        "fibre": nutrient_data['fiber_serving']
    }
    

    food = Food(name=product_name, barcode=barcode, brand=brand)
    nrs = []
    for k, v in nutrition_records.items():
        nrs.append(NutritionRecord(name=k, amount=v, food=food))

    db.session.add(food)
    db.session.add_all(nrs)
    db.session.commit()
    # except Exception as e:
    #     print(f'Error: {e}')
    #     return None

    return food.id

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

@app.route('/addmeal/<meal_id>', methods=['GET', 'POST'])
@app.route('/addmeal/<meal_id>/<query>', methods=['GET', 'POST'])
@login_required
def addmeal(meal_id, query=''):
    meal = db.session.query(Meal).filter_by(id=meal_id).one_or_none()

    query = f'%{query}%'
    foods = db.session.query(Food).filter(Food.name.like(query)).all()

    if not meal:
        return redirect(url_for('index'))
    
    return render_template('addmeal.html', meal=meal, foods=foods)

@app.route('/addfood/<meal_id>/<food_id>', methods=['GET','POST'])
@login_required
def addfood(meal_id, food_id):
    meal = db.session.query(Meal).filter_by(id=meal_id).one_or_none()
    food = db.session.query(Food).filter_by(id=food_id).one_or_none()

    if not meal or not food:
        return redirect(url_for('index'))
    
    food_entry = FoodEntry(meal=meal, food=food, quantity=1)
    db.session.add(food_entry)
    db.session.commit()

    return redirect(url_for('diary'))

@app.route('/scan/<meal_id>')
@login_required
def scan(meal_id):
    return render_template('scan.html', meal_id=meal_id)

@app.route('/scan_barcode', methods=['POST'])
@login_required
def upload():
    data = request.data

    barcode = get_barcode_from_imagedata(data)
    if not barcode:
        return 'no barcode found', 400

    return barcode.data.decode(), 200

@app.route('/barcode/search/<meal_id>/<barcode>', methods=['GET','POST'])
@login_required
def barcode_search(meal_id, barcode):
    fooddata = search_barcode(barcode)

    if not fooddata:
        flash('Could not find food on Open Food Facts')
        return redirect(url_for('addmeal', meal_id=meal_id))
    
    food_id = add_off_data_as_food(fooddata)
    if not food_id:
        flash('There was an error adding the food')
        return redirect(url_for('addmeal', meal_id=meal_id))

    return redirect(url_for('addfood', meal_id=meal_id, food_id=food_id))