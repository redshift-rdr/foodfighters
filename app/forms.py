from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, DateField, HiddenField, FloatField, SelectField, FloatField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, ValidationError
from app.models import Profile
from wtforms.widgets import NumberInput

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Profile.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = Profile.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change')

    def validate_new_password(self, password):
        password_stat = PasswordStats(password.data)

        if password_stat.strength() < 0.66:
            raise ValidationError('Thats a bad password. Choose a better one')

class ManualFoodForm(FlaskForm):
    # food 
    name = StringField('Name', validators=[DataRequired()])
    brand = StringField('Brand')
    barcode = StringField('Barcode', validators=[DataRequired()])
    serving_size = IntegerField('Serving Size (g)', validators=[DataRequired()])

    # nutrition records
    calories = FloatField('Calories (per 100g)')
    fat = FloatField('Fat (per 100g)')
    sugar = FloatField('Sugar (per 100g)')
    salt = FloatField('Salt (per 100g)')
    protein = FloatField('Protein (per 100g)')
    fibre = FloatField('Fibre (per 100g)')

    submit = SubmitField('Add')
        
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class addMealForm(FlaskForm):
    category = StringField('Category (breakfast, lunch etc)')
    submit = SubmitField('Add')