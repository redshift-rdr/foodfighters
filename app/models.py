import uuid
from app import db, login
from flask_login import UserMixin
from app.utils import add_nutrition_data
from datetime import datetime, timedelta
from sqlalchemy.orm import backref, validates
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash

def generate_uuid():
    return str(uuid.uuid4())

@login.user_loader
def load_user(id):
    return Profile.query.get(id)

class Profile(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(32), index=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(96), index=True, nullable=False)

    diaryentries = db.relationship('DiaryEntry', back_populates='profile')

    def __repr__(self):
        return f'<Profile: {self.username}>'
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class DiaryEntry(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    day = db.Column(db.Date, nullable=False)

    # relationships
    meals = db.relationship('Meal', back_populates='diaryentry')

    profile_id = db.Column(db.String(36), db.ForeignKey('profile.id'))
    profile = db.relationship('Profile', back_populates='diaryentries')

    def __repr__(self):
        return f'<DiaryEntry: {self.day}>'

    def nutrition(self):
        return add_nutrition_data(self.meals)

class Meal(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    category = db.Column(db.String(32))

    # relationships
    foodentries = db.relationship('FoodEntry', back_populates='meal')

    diaryentry_id = db.Column(db.String(36), db.ForeignKey('diary_entry.id'))
    diaryentry = db.relationship('DiaryEntry', back_populates='meals')

    def __repr__(self):
        return f'<Meal: {self.id}>'
    
    def nutrition(self):
        return add_nutrition_data(self.foodentries)

class FoodEntry(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    quantity = db.Column(db.Integer, nullable=False)

    # relationships
    food = db.relationship('Food', back_populates='foodentry', uselist=False)

    meal_id = db.Column(db.String(36), db.ForeignKey('meal.id'))
    meal = db.relationship('Meal', back_populates='foodentries')

    def __repr__(self):
        return f'<FoodEntry: {self.id}>'

    @validates('quantity')
    def validate_quantity(self, key, amount):
        assert amount > 0
        return amount
    
    def nutrition(self):
        nutrition_info = self.food.nutrition()

        for record in nutrition_info.keys():
            nutrition_info[record] *= self.quantity
        
        return nutrition_info
    
class Food(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(32), index=True, nullable=False)
    barcode = db.Column(db.String(32), index=True, nullable=False)
    brand = db.Column(db.String(32))

    # relationships
    nutrition_records = db.relationship('NutritionRecord', back_populates='food')

    foodentry_id = db.Column(db.String(36), db.ForeignKey('food_entry.id'))
    foodentry = db.relationship('FoodEntry', back_populates='food')

    def __repr__(self):
        return f'<Food: {self.name}>'

    def nutrition(self):
        nutrition_info = {}

        for record in self.nutrition_records:
            nutrition_info[record.name] = record.amount

        return nutrition_info

class NutritionRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float)

    food_id = db.Column(db.String(36), db.ForeignKey('food.id'))
    food = db.relationship('Food', back_populates='nutrition_records')

    def __repr__(self):
        return f'<NutritionRecord: {self.name}-{self.id}>'
