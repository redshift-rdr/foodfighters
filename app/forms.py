from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, DateField, HiddenField, FloatField, SelectField, FloatField
from wtforms.validators import DataRequired, Optional

class AddProfile(FlaskForm):
    name = StringField('Profile Name', validators=[DataRequired()])
    submit = SubmitField('Add')

class AddRecurringRecordForm(FlaskForm):
    uuid = HiddenField('uuid')
    type = SelectField('Type', choices=[('expense', 'expense'), ('income', 'income')])
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    amount = FloatField('Amount', validators=[DataRequired()])
    recurring_dom = IntegerField('Repeat DOM')
    addthismonth = BooleanField('Add to this month')
    payment_method = SelectField('Payment Method', choices=[('Automatic', 'automatic'), ('Manual', 'Manual')])
    submit = SubmitField('Submit')

class AddRecordForm(FlaskForm):
    uuid = HiddenField('uuid')
    type = SelectField('Type', choices=[('expense', 'expense'), ('income', 'income')])
    recurring = BooleanField('Recurring')
    addthismonth = BooleanField('Add to this month')
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    amount = FloatField('Amount', validators=[DataRequired()])
    recurring_dom = IntegerField('Repeat DOM')
    payment_method = SelectField('Payment Method', choices=[('automatic', 'Automatic'), ('manual', 'Manual')])
    paid = BooleanField('Paid')
    submit = SubmitField('Submit')