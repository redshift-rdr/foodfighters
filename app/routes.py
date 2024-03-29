from base64 import decode
from lib2to3 import pytree
import profile
from unicodedata import category
from flask import render_template, flash, redirect, request, url_for, session, make_response, jsonify
from app import app, db
from app.models import Profile, DiaryEntry, Meal, FoodEntry, Food, NutritionRecord
from app.forms import LoginForm, RegisterForm, addMealForm, ChangePasswordForm, ManualFoodForm
from datetime import date, timedelta
from app.utils import get_barcode_from_imagedata, search_barcode, recommended_nutrition, generate_random_colour,search_off_by_product_name
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import asc

#######################
## utility functions ##
#######################
def get_model(model_name : str) -> db.Model:
    """ Map model names to Models

        Args:
            model_name: The name of the model to be returned

        Returns:
            A SQLAlchemy model, or None
    """
    model_map = {
        'Profile': Profile,
        'DiaryEntry': DiaryEntry,
        'Meal': Meal,
        'FoodEntry': FoodEntry,
        'Food': Food,
        'NutritionRecord': NutritionRecord
    }

    return model_map.get(model_name, None)
    
def lookup_barcode(barcode : str) -> db.Model:
    """ Gets a Food object using a barcode lookup

        Args:
            barcode: The barcode string used to lookup the Food object. 

        Returns:
            A models.Food object, or None
    """
    return db.session.query(Food).filter_by(barcode=barcode).one_or_none()

def add_off_data_as_food(data : dict) -> str:
    """  Creates a new Food object, using data provided by Open Food Facts (OFF) (https://world.openfoodfacts.org/)

        Args:
            data: A dict taken from a OFF API call

        Returns:
            A str representing a UUID, identifying the Food object created
    """

    # grab product details
    try:
        product_name = data['product']['product_name']
        brand = data['product']['brands']
        barcode = data['code']
        size = data['product'].get('serving_quantity', 1)

        # grab nutrient data 
        nutrient_data = data['product']['nutriments']
    except KeyError:
        # if a KeyError is encountered that means OFF did not have the product
        # in its database
        return None
    
    nutrition_records = {
        "calories": nutrient_data.get('energy-kcal_100g', 0),
        "carbohydrates": nutrient_data.get('carbohydrates_100g', 0),
        "fat": nutrient_data.get('fat_100g', 0),
        "sugar": nutrient_data.get('sugars_100g', 0),
        "salt": nutrient_data.get('salt_100g', 0),
        "protein": nutrient_data.get('proteins_100g', 0),
        "fibre": nutrient_data.get('fiber_100g', 0)
    }

    # warn the user if not call nurtrient data is avaiable from OFF
    if not all(nutrition_records.values()):
        flash('Some nutrition records could not be found, please review added food')

    # create a Food object from retrieved data, including NutrientRecords
    food = Food(name=product_name, barcode=barcode, serving_size=size, brand=brand)
    nrs = []
    for k, v in nutrition_records.items():
        nrs.append(NutritionRecord(name=k, per_100=round(v, 2), amount=round(v/100*int(food.serving_size), 2), food=food))

    # add the Food object to the database
    db.session.add(food)
    db.session.add_all(nrs)
    db.session.commit()

    return food.id

##############
### routes ###
##############
@app.route('/')
@app.route('/index')
@login_required
def index():
    """ the / route, redirect to /diary
    """
    return redirect(url_for('diary'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """ The profile page, used to review and change profile information
    """
    change_password_form = ChangePasswordForm()

    # change the password
    if change_password_form.validate_on_submit():
        if current_user.check_password(change_password_form.current_password.data):
            current_user.set_password(change_password_form.new_password.data)
            flash('Password changed successfully', 'success')
        else:
            flash('Incorrect current password', 'danger')

    return render_template('profile.html', profile=current_user, form=change_password_form)

@app.route('/chart')
@login_required
def chart():
    """ Display a bar chart of selected nutrient over time

        Args (GET):
            start_date:     The date from which the data should be shown
            end_date:       The end date for the data to be shown
            nutrient_name:  The name of the nutrient values to be shown
    """
    # grab the GET arguments
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    nutrient_name = request.args.get('nutrient_name', 'calories')

    # make sure the nutrient name is within allowed values
    if nutrient_name not in recommended_nutrition.keys():
        nutrient_name = 'calories'

    # grab the diary entries between the selected dates
    diary_entries = db.session.query(DiaryEntry).filter(DiaryEntry.day.between(start_date, end_date)).order_by(asc(DiaryEntry.day)).all()

    # create the bar chart data, to be used by chart.js
    labels = [
        de.day.strftime('%a %-d %b') for de in diary_entries
    ]

    values = [
        de.nutrition().get(nutrient_name, 0) for de in diary_entries
    ]

    colors = [
        generate_random_colour() for _ in diary_entries
    ]
    
    return render_template('chart.html', labels=labels, values=values, colors=colors, start_date=start_date, end_date=end_date, nutrient_name=nutrient_name)

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
        Args:
            indate: needs to be a string date in ISO format e.g. '2022-10-29'
                    if not indate value is provided it will default to today
    """
    if not indate:
        date_select = date.today()
    else:
        try:
            date_select = date.fromisoformat(indate)
        except ValueError:
            date_select = date.today()

    # grab the diary entry for selected date, if it doesn't exist create it
    diary_entry = db.session.query(DiaryEntry).filter_by(day=date_select).one_or_none()
    if not diary_entry:
        diary_entry = DiaryEntry(day=date_select, profile=current_user)

        # add the default meals from the users profile
        default_meals = current_user.get_default_meals()
        for meal in default_meals:
            db.session.add(Meal(category=meal, diaryentry=diary_entry))
        db.session.add(diary_entry)
        db.session.commit()

    # handle the Meal form being submitted
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

    db_foods = db.session.query(Food).filter(Food.name.like(f'%{query}%')).limit(5).all()
    off_foods = search_off_by_product_name(query)

    if not meal:
        flash('That meal ID doesnt exist!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('addmeal.html', meal=meal, db_foods=db_foods, off_foods=off_foods)

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
            flash('Unable to find that barcode, please add manually', 'danger')
            return redirect(url_for('manual_addfood', barcode=barcode, meal_id=meal_id))
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