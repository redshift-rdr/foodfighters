from base64 import decode
from lib2to3 import pytree
import profile
from unicodedata import category
from flask import render_template, flash, redirect, request, url_for, session, make_response, jsonify
from app import app, db
from app.models import Profile, DiaryEntry, Meal, FoodEntry, Food, NutritionRecord
from app.forms import LoginForm, RegisterForm, addMealForm, ChangePasswordForm, ManualFoodForm
from datetime import date, timedelta
from app.utils import get_barcode_from_imagedata, search_barcode, recommended_nutrition
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import asc

## utility functions
def get_model(model_name : str):
    model_map = {
        'Profile': Profile,
        'DiaryEntry': DiaryEntry,
        'Meal': Meal,
        'FoodEntry': FoodEntry,
        'Food': Food,
        'NutritionRecord': NutritionRecord
    }

    try:
        return model_map[model_name]
    except KeyError:
        return None
    
def lookup_barcode(barcode):
    return db.session.query(Food).filter_by(barcode=barcode).one_or_none()


def add_off_data_as_food(data):
    """
        TODO: redo this - 
    """
    #try:
    product_name = data['product']['product_name']
    brand = data['product']['brands']
    barcode = data['code']
    size = data['product'].get('serving_quantity', 1)

    nutrient_data = data['product']['nutriments']
    nutrition_records = {
        "calories": nutrient_data.get('energy-kcal_100g', 0),
        "carbohydrates": nutrient_data.get('carbohydrates_100g', 0),
        "fat": nutrient_data.get('fat_100g', 0),
        "sugar": nutrient_data.get('sugars_100g', 0),
        "salt": nutrient_data.get('salt_100g', 0),
        "protein": nutrient_data.get('proteins_100g', 0),
        "fibre": nutrient_data.get('fiber_100g', 0)
    }

    if not all(nutrition_records.values()):
        flash('Some nutrition records could not be found, please review added food')

    food = Food(name=product_name, barcode=barcode, serving_size=size, brand=brand)
    nrs = []
    for k, v in nutrition_records.items():
        nrs.append(NutritionRecord(name=k, per_100=round(v, 2), amount=round(v/100*int(food.serving_size), 2), food=food))

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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    change_password_form = ChangePasswordForm()

    if change_password_form.validate_on_submit():
        if current_user.check_password(change_password_form.current_password.data):
            current_user.set_password(change_password_form.new_password.data)
            flash('Password changed successfully', 'success')
        else:
            flash('Incorrect current password', 'danger')

    return render_template('profile.html', profile=current_user, form=change_password_form)

@app.route('/chart')
def chart():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    diary_entries = db.session.query(DiaryEntry).filter(DiaryEntry.day.between(start_date, end_date)).order_by(asc(DiaryEntry.day)).all()

    labels = [
        de.day.strftime('%a %-d %b') for de in diary_entries
    ]

    values = [
        de.nutrition().get('calories', 0) for de in diary_entries
    ]

    colors = [
        "#F7464A", "#46BFBD"
        ]
    
    return render_template('chart.html', labels=labels, values=values, colors=colors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Profile.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=True)
        return redirect(url_for('index'))

    return render_template('login.html', form=form, nonav=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = Profile(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        for k,v in recommended_nutrition.items():
            user.nutrition_goals.append(NutritionRecord(name=k, amount=v))

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
        default_meals = current_user.get_default_meals()
        for meal in default_meals:
            db.session.add(Meal(category=meal, diaryentry=diary_entry))
        db.session.add(diary_entry)
        db.session.commit()

    form = addMealForm()
    if form.validate_on_submit():
        add_meal = Meal(category=form.category.data, diaryentry=diary_entry)
        db.session.add(add_meal)
        db.session.commit()

    return render_template('diary.html', diary_entry=diary_entry, form=form)

@app.route('/meal/remove_food/<foodentry_id>', methods=['GET'])
@login_required
def remove_food(foodentry_id):
    diary_date = request.args.get('diary_date')
    foodentry = db.session.query(FoodEntry).filter_by(id=foodentry_id).delete()
    db.session.commit()

    return redirect(url_for('diary', indate=diary_date))

@app.route('/diary/nutrition/<indate>', methods=['GET', 'POST'])
@login_required
def diary_nutrition(indate : str):
    if not indate:
        date_select = date.today()
    else:
        date_select = date.fromisoformat(indate)

    diary_entry = db.session.query(DiaryEntry).filter_by(day=date_select).one_or_none()
    if not diary_entry:
        flash('There is no diary entry for that date!', 'danger')
        return redirect(url_for('diary', indate=indate))

    return render_template('nutrition.html', diary_entry=diary_entry)

@app.route('/addmeal/<meal_id>', methods=['GET', 'POST'])
@app.route('/addmeal/<meal_id>/<query>', methods=['GET', 'POST'])
@login_required
def addmeal(meal_id, query=''):
    meal = db.session.query(Meal).filter_by(id=meal_id).one_or_none()

    query = f'%{query}%'
    foods = db.session.query(Food).filter(Food.name.like(query)).limit(5).all()

    if not meal:
        flash('That meal ID doesnt exist!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('addmeal.html', meal=meal, foods=foods)

@app.route('/addfood/<meal_id>/<food_id>', methods=['GET','POST'])
@login_required
def addfood(meal_id, food_id):
    meal = db.session.query(Meal).filter_by(id=meal_id).one_or_none()
    food = db.session.query(Food).filter_by(id=food_id).one_or_none()
    diary_date = request.args.get('diary_date', default='')

    if not meal or not food:
        flash('That meal ID or food ID doesnt exist!')
        return redirect(url_for('index'))
    
    food_entry = FoodEntry(meal=meal, food=food, quantity=1)
    db.session.add(food_entry)
    db.session.commit()

    return redirect(url_for('diary', indate=diary_date))

@app.route('/food/manual', defaults={'barcode':''}, methods=['GET', 'POST'])
@app.route('/food/manual/<barcode>', methods=['GET', 'POST'])
def manual_addfood(barcode):
    form = ManualFoodForm()
    form.barcode.data = barcode
    meal_id = request.args.get('meal_id', default='')
    
    if form.validate_on_submit():
        food = Food(name=form.name.data, brand=form.brand.data, barcode=form.barcode.data, serving_size=form.serving_size.data)

        calories = NutritionRecord(name='calories', per_100=form.calories.data, food=food)
        calories.update()

        fat = NutritionRecord(name='fat', per_100=form.fat.data, food=food)
        fat.update()

        sugar = NutritionRecord(name='sugar', per_100=form.sugar.data, food=food)
        sugar.update()

        salt = NutritionRecord(name='salt', per_100=form.salt.data, food=food)
        salt.update()

        protein = NutritionRecord(name='protein', per_100=form.protein.data, food=food)
        protein.update()

        fibre = NutritionRecord(name='fibre', per_100=form.fibre.data, food=food)
        fibre.update()

        db.session.add_all([food, calories, fat, sugar, salt, protein, fibre])
        db.session.commit()

        return redirect(url_for('addmeal', meal_id=meal_id, query=food.name))

    return render_template('addfood.html', form=form)

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
    food = lookup_barcode(barcode)

    if not food:
        fooddata = search_barcode(barcode)

        if not fooddata:
            flash('Could not find food on Open Food Facts', 'danger')
            return redirect(url_for('addmeal', meal_id=meal_id))
        
        food_id = add_off_data_as_food(fooddata)
        if not food_id:
            flash('There was an error adding the food', 'danger')
            return redirect(url_for('addmeal', meal_id=meal_id))
    else:
        food_id = food.id

    return redirect(url_for('addfood', meal_id=meal_id, food_id=food_id))

@app.route('/food/edit/<food_id>', methods=['GET', 'POST'])
@login_required
def edit_food(food_id):
    indate = request.args.get('indate', '')
    food = db.session.query(Food).filter_by(id=food_id).one_or_none()

    if not food:
        flash('Food not found', 'danger')
        return redirect(url_for('index'))
    
    return render_template('editfood.html', food=food, indate=indate)

@app.route('/meal/<uuid>/remove', methods=['GET'])
@login_required
def remove_meal(uuid):
    diary_date = request.args.get('diary_date', default='')
    meal = db.session.query(Meal).filter_by(id=uuid).one_or_none()

    if not meal:
        flash('That meal ID doesnt exist', 'danger')

    for entry in meal.foodentries:
        db.session.query(FoodEntry).filter_by(id=entry.id).delete()

    db.session.query(Meal).filter_by(id=uuid).delete()
    db.session.commit()

    return redirect(url_for('diary', indate=diary_date))
    

## API routes
# get all instances in model
@app.route('/api/<model>')
def get_all(model):
    model = get_model(model)

    items = db.session.query(model).all()
    json_items = [item.as_dict() for item in items]

    return jsonify(json_items)

# get a specific instance of model
@app.route('/api/<model>/<uuid>')
def get_one(model, uuid):
    model = get_model(model)

    item = db.session.query(model).filter_by(id=uuid).first()
    if not item:
        return jsonify({})

    return jsonify(item.as_dict())

# add an new instance of a model
@app.route('/api/<model>/add', methods=['POST'])
def add(model):
    model = get_model(model)
    data = request.get_json()

    try:
        model_instance = model(**data)
    except Exception as e:
        return jsonify({'error': f'{e}'})

    db.session.add(model_instance)
    db.session.commit()

    return jsonify(model_instance.as_dict())

# update an instance of a model
@app.route('/api/<model>/<uuid>/update', methods=['POST'])
def update(model, uuid):
    model = get_model(model)
    data = request.get_json()

    print(data)

    model_instance = db.session.query(model).filter_by(id=uuid).first()
    if not model_instance:
        return jsonify({"error": "could not find a model with that uuid"}),400

    try:
        for k,v in data.items():
            if hasattr(model_instance, k):
                # hack for date fields
                if k in ['day']:
                    setattr(model_instance, k, date.fromisoformat(v))
                else:
                    setattr(model_instance, k, v)

        db.session.add(model_instance)
        db.session.commit()
    except Exception as e:
        return jsonify({"error" : f"{e}"}),400

    return jsonify(model_instance.as_dict())

# delete an instance of a model
@app.route('/api/<model>/<uuid>/remove', methods=['POST'])
def remove(model, uuid):
    model = get_model(model)
    data = request.get_json()

    try:
        db.session.query(model).filter_by(id=uuid).delete()
        db.session.commit()
    except Exception as e:
        return jsonify({"error" : f"{e}"}), 400

    return jsonify({"status": "success", "message": "model deleted successfully"})

# create a relationship between models
@app.route('/api/<model>/<uuid>/link', methods=['POST'])
def link(model, uuid):
    model = get_model(model)
    data = request.get_json()

    link_model = get_model(data["model"])

    to_link = db.session.query(link_model).filter_by(id=data["uuid"]).first()
    model_instance = db.session.query(model).filter_by(id=uuid).first()

    setattr(model_instance, data["linked_attribute"], to_link)

    db.session.add_all([to_link, model_instance])
    db.session.commit()

    return jsonify(model_instance.as_dict())

@app.route('/api/update_food_size/<food_id>', methods=['POST'])
def api_update_servingsize(food_id):
    food = db.session.query(Food).filter_by(id=food_id).one_or_none()
    data = request.get_json()

    if not food:
        return 'none found', 400
    
    food.serving_size = data["serving_size"]

    for nut_record in food.nutrition_records:
        nut_record.update()
        db.session.add(nut_record)

    db.session.add(food)
    db.session.commit()

    return jsonify({"status": "success"})

@app.route('/api/update_nutrition/<record_id>', methods=['POST'])
def api_update_nutritionrecord(record_id):
    record = db.session.query(NutritionRecord).filter_by(id=record_id).one_or_none()
    data = request.get_json()

    if not record:
        return 'record not found', 400
    
    record.per_100 = float(data["per_100"])
    record.update()

    db.session.add(record)
    db.session.commit()

    return jsonify({"status": "success"})