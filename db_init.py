from unicodedata import category
from app import app, db
from app.models import *
from datetime import date

ryan = Profile(username='ryan', email='ryan@wickedwickwarriors.com')
ryan.set_password('password')

diary_entry = DiaryEntry(day=date.today(), profile=ryan)
meal = Meal(category='lunch', diaryentry=diary_entry)
food_entry = FoodEntry(quantity=2, meal=meal)
bread = Food(name='Bread', barcode='1234', foodentry=food_entry)
food_entry2 = FoodEntry(quantity=1, meal=meal)
margarine = Food(name='Margarine', barcode='12345',foodentry=food_entry2)

b_cal = NutritionRecord(name='calories', amount=95.0, food=bread)
m_cal = NutritionRecord(name='calories', amount=40.0, food=margarine)

db.session.add_all([ryan, diary_entry, meal, food_entry, bread, food_entry2, margarine, b_cal, m_cal])
db.session.commit()