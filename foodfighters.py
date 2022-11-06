from app import app, db
from app.models import Profile, DiaryEntry, Meal, FoodEntry, Food, NutritionRecord

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Profile': Profile, 'DiaryEntry': DiaryEntry, 'Meal': Meal, 'FoodEntry': FoodEntry, 'Food': Food, 'NutritionRecord': NutritionRecord}