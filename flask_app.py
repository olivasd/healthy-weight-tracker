from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from wtforms import StringField, PasswordField, BooleanField, IntegerField, RadioField, HiddenField, validators
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms.fields.html5 import DateField
from datetime import datetime, timedelta
from forms import LoginForm, RegisterForm, HWForm, WeightForm
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = ''

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(20))
    email = db.Column(db.String(30), unique=True)
    first_name = db.Column(db.String(25))
    last_name = db.Column(db.String(25))
    birthday = db.Column(db.DateTime)
    height = db.Column(db.Integer)
    gender = db.Column(db.String(6))
    initialHW = db.Column(db.Boolean, default=False)
    userWeights = db.relationship('UserWeights', backref='user', lazy=True)
    
class UserWeights(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Integer)
    date = db.Column(db.DateTime)

class Functions():
    def bmi(self):
        wt = UserWeights.query.filter(UserWeights.user_id == current_user.id).order_by(UserWeights.date.desc()).first().weight
        ht = current_user.height
        cur_bmi = float(wt) / (float(ht) * float(ht)) * 703    
        return round(cur_bmi, 1)

    def bmr(self):
        wt = float(UserWeights.query.filter(UserWeights.user_id == current_user.id).order_by(UserWeights.date.desc()).first().weight)
        ht = float(current_user.height)
        age = datetime.now().year - current_user.birthday.year - ((datetime.now().month, datetime.now().day) < (current_user.birthday.month, current_user.birthday.day))
        if current_user.gender == 'male':
            bmr = 66.47 + (6.24 * wt) + (12.7 * ht) - (6.755 * age)
        else:
            bmr = 655.1 + ( 4.35 * wt) + (4.7 * ht) - (4.7 * age)
        return int(bmr)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                if user.initialHW == False:
                    return redirect(url_for('hw'))
                return redirect(url_for('index'))

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, 
                        email=form.email.data, 
                        password=hashed_password,
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        birthday=form.birthday.data,
                        gender=form.gender.data,)
        if User.query.filter(User.username == form.username.data).first() != None:
            return '<h1>' + form.username.data + ' already exists</h1><br><a href="/register">Go Back</a>'
        if User.query.filter(User.email == form.email.data).first() != None:
            return '<h1>' + form.email.data + ' already exists</h1><br><a href="/register">Go Back</a>'
        db.session.add(new_user)
        db.session.commit()
        send_email(new_user)
        login_user(new_user)

        return redirect(url_for('hw'))
    
    return render_template('register.html', form=form)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.initialHW == 0:
        return redirect(url_for('hw')) 

    form = WeightForm()
    func = Functions()
    today = datetime.now()     
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)   
    has_weight = UserWeights.query.filter_by(user_id=current_user.id, date=today).first()
    
    if form.validate_on_submit():
        if  has_weight != None:
            has_weight.weight = form.weight.data
            db.session.commit()
            flash("Weight has been update for today")
            compare_weight(form.weight.data)
        else:
            new_wt = UserWeights(user_id = current_user.id,
                                weight = form.weight.data,
                                date = today)
            db.session.add(new_wt)
            db.session.commit()
            flash("Weight has been recorded") 
            compare_weight(form.weight.data)
    return render_template("index.html", name=current_user, form=form, fun=func)

@app.route('/hw', methods=['GET', 'POST'])
@login_required
def hw():    
    form = HWForm()
    user = User.query.filter(User.id == current_user.id).first()  
    day = datetime.now()  
    if form.validate_on_submit():
        ht = form.foot.data * 12 + form.inches.data
        user.height = ht
        user.initialHW = True
        new_ht = UserWeights(user_id = user.id,
                            weight = form.weight.data,
                            date = day.replace(hour=0, minute=0, second=0, microsecond=0))
        db.session.add(new_ht)
        db.session.commit()
        return redirect(url_for('index'))    
    return render_template("hw.html", form=form)

@app.route('/eer', methods=['GET', 'POST'])
@login_required
def eer():
    try:
        activity = request.form['active']
        eer = calc_eer(activity)
        return render_template('eer.html', data=int(eer))
    except:
        return '<h1>Please Select an Activity Level<br><br><a href="/">Return</a></h1>'

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chart', methods=['GET', 'POST'])
@login_required
def chart():
   
    cur_date = datetime.utcnow()
    time = request.form['time']
    wt = ''
    if time == '13':
        wt = UserWeights.query.filter(UserWeights.user_id == current_user.id).order_by(UserWeights.date.asc()).all()
    else:
        wt = UserWeights.query.filter(UserWeights.date > cur_date - timedelta(days=30 * int(time))).filter(UserWeights.user_id == current_user.id).order_by(UserWeights.date.asc()).all()
    day = []
    weighs = []
    max_weight = 0
    min_weight = 1000
    for w in wt:
        day.append(datetime.date(w.date))
        weighs.append(w.weight)
        if max_weight < w.weight:
            max_weight = w.weight
        if min_weight > w.weight:
            min_weight = w.weight
    return render_template('chart.html', day=day, weighs=weighs, max=max_weight, min=min_weight, time=time)

def calc_eer(activity):
    calc = Functions()
    if activity == 'sedentary':
        return calc.bmr()
    elif activity == 'lowActive':
        if current_user.gender == 'male':
            return calc.bmr() * 1.11
        else:
            return  calc.bmr() * 1.12
    elif activity == 'active':
        if current_user.gender == 'male':
            return calc.bmr() * 1.25
        else:
            return  calc.bmr() * 1.27
    elif activity == 'veryActive':
        if current_user.gender == 'male':
            return calc.bmr() * 1.48
        else:
            return  calc.bmr() * 1.45

def send_email(user):
    FROM = 'noreply.healthy@gmail.com'
    password = 'EnchiladaSauce01!'

    TO = user.email
    SUBJECT = "Welcome To Healthy Weight Tracker"
    TEXT = """\
    Hi %s %s,
    Welcome to Healthy Weight Tracker. To get the most of this website, make sure you are logging
    your weight on a regular basis. This site is a work in progress with features being added regularly.
    We hope that you find this website to be useful and feedback is always welcome.

    Sincerely,
    Daniel Olivas
    dolivas10@gmail.com
    """ % (user.first_name, user.last_name)
    message = """FROM: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, TO, SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(FROM, password)
        server.sendmail(FROM, TO, message)
        server.close()
    except:
        print "<h1>Failure to email</h1>"

def compare_weight(cur_weight):
    first_weight = float(UserWeights.query.filter(UserWeights.user_id == current_user.id).order_by(UserWeights.date.asc()).first().weight)
    if cur_weight < first_weight:
        flash("You have lost " + str(int(first_weight - cur_weight))  + " lbs so far!")
    elif cur_weight > first_weight:
        flash("You have gained " + str(int(cur_weight - first_weight)) + " lbs so far!")
    else:
        flash("You weight the same as you first started!")
      

if __name__ == '__main__':
    app.run(debug=False)
