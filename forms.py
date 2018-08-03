from flask_wtf import Form 
from wtforms import StringField, PasswordField, BooleanField, IntegerField, RadioField, HiddenField, validators
from wtforms.validators import InputRequired, Email, Length
from wtforms.fields.html5 import DateField


class LoginForm(Form):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=20)])
    remember = BooleanField('remember me')

class RegisterForm(Form):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=6, max=20)])
    password2 = PasswordField('confirm password', [validators.EqualTo('password')])
    first_name = StringField('first name', validators=[InputRequired(), Length(max=25)])
    last_name = StringField('last name', validators=[InputRequired(), Length(max=25)])
    birthday = DateField('birthday', format='%Y-%m-%d', validators=[InputRequired()])
    gender = RadioField('gender', choices=[('male', 'male'), ('female','female')], validators = [InputRequired()])
    

class HWForm(Form):
    foot = IntegerField('ft', [validators.InputRequired(), validators.NumberRange(min=2, max=7)])
    inches = IntegerField('in', [validators.InputRequired(), validators.NumberRange(min=0, max=11)])
    weight =IntegerField('weight in lbs',[validators.InputRequired(), validators.NumberRange(min=40, max=800)])
    date = HiddenField()

class WeightForm(Form):
    weight =IntegerField('weight in lbs',[validators.InputRequired(), validators.NumberRange(min=40, max=800)])
    date = DateField(format='%Y-%m-%d')