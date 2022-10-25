from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, DateField, HiddenField, FloatField, SelectField, FloatField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, ValidationError
from app.models import Profile
from password_strength import PasswordStats

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

    def validate_password(self, password):
        password_stat = PasswordStats(password.data)

        if password_stat.strength() < 0.66:
            raise ValidationError('Please use a more complex password')
        
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')