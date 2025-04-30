from flask import Flask, render_template, url_for, redirect, flash, request    # Flask functions
from flask_login import UserMixin, current_user, login_user, logout_user, login_required, LoginManager      # Login functions
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash        # Hashing functions
import sqlite3      # SQL queries
# import secrets    # Would be used for secret key
import smtplib      # sending emails
from email.mime.text import MIMEText        # necessary email module
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer     # Creating tokens for email confirmation
from datetime import date
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TechnologyRolsa1650'        # In proper deployment, secret key will be randomly generated for extra security (secrets.token_hex())
app.config['SECURITY_PASSWORD_SALT'] = 'SALTY'
log_manager = LoginManager(app)
log_manager.login_view = "login"

@log_manager.user_loader        # loads user info such as id
def load_user(user_id):
   con = sqlite3.connect('rolsa.db')
   curs = con.cursor()
   curs.execute("SELECT * from login where user_ID = (?)",[user_id])
   liUser = curs.fetchone()
   if liUser is None:
      return None
   else:
      return User(int(liUser[0]), liUser[1], liUser[2])
   

bcrypt = Bcrypt(app)

def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT']) #generates token using an email address

def confirm_token(token, expiration=1800):      # checks whether the token is authentic and not expired. Should expire after 30 minutes
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age = expiration)
    except:
        return False
    return email

@app.route('/')
def landing():
    return render_template("landing.html")

@app.route('/bookings')     # fetches all bookings which the user has made which are not out of date and sets them to a jinja variable for use in the html
@login_required
def bookings():
    con = sqlite3.connect('rolsa.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM bookings INNER JOIN products ON products.item_ID = bookings.item_ID WHERE user_ID = (?) AND date >= (?)", (current_user.get_id(),date.today()))
    records = cur.fetchall()
    cur.row_factory = None
    cur.execute("SELECT * FROM footprint WHERE user_ID = (?) AND date = (?)", (current_user.get_id(), date.today()))
    completed = cur.fetchone()
    cur.execute("SELECT * FROM energy WHERE user_ID = (?) AND date = (?)", (current_user.get_id(), date.today()))
    completed2 = cur.fetchone()
    if completed == None and completed2 == None:
        return render_template("bookings.html", records = records)
    elif completed != None and completed2 == None:
        return render_template("bookings.html", records = records, completed = True)
    elif completed == None and completed2 != None:
        return render_template("bookings.html", records = records, completed2 = True)
    else:
        return render_template("bookings.html", records = records, completed = True, completed2 = True)

@app.route('/products')     # fetches all products from database and sets them to a jinja variable for use in the html
@login_required
def products():
    con = sqlite3.connect('rolsa.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    return render_template("products.html", products = products)

@app.route('/order/<item>')     # depending on what item was chosen previously, the url will be different. based on the second part of the html, fetches related data and sets to a jinja variable for use in the html
@login_required
def order(item):
    con = sqlite3.connect('rolsa.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM products WHERE item_ID = (?)", (item,))
    product = cur.fetchone()
    return render_template("order.html", product = product)

@app.route('/order/<item>', methods=['POST'])       # when user completes form and submits, fetches all form values and puts them into the booking table in the database, which is referenced on the bookings page
@login_required
def order_confirmed(item):
    item = item
    user = current_user.get_id()
    bookdate = request.form["date"]
    address = request.form["address"]
    con = sqlite3.connect('rolsa.db')
    cur = con.cursor()
    cur.execute("INSERT INTO bookings (user_ID, date, item_ID, address) VALUES (?,?,?,?)", (user, bookdate, item, address))
    con.commit()
    return redirect(url_for("bookings"))

@app.route('/energy-consumption')       # fetches user's energy data for the chart on the energy page
@login_required
def energy():
    con = sqlite3.connect('rolsa.db')
    con.row_factory = lambda cursor, row: row[0]
    cur = con.cursor()
    cur.execute("SELECT * FROM energy WHERE user_ID = (?) AND date = (?)", (current_user.get_id(), date.today()))        # checks if there is a record for today
    completed = cur.fetchone()
    cur.execute("SELECT date FROM energy WHERE user_ID = (?)", (current_user.get_id(),))
    x = cur.fetchall()
    cur.execute("SELECT usage FROM energy WHERE user_ID = (?)", (current_user.get_id(),))
    y = cur.fetchall()
    print(completed)
    if completed == None:       # depending on whether there is a record for today, the html page will load differently
        return render_template("energy.html", x = x, y = y)
    else:
        return render_template("energy.html", completed = True, x = x, y = y)

@app.route('/energy-consumption', methods=['GET', 'POST'])      # fetches the values of the form inputs, if theres nothing in the first one, it gathers and totals all the values from the inputs the user can create, otherwise it just uses the first form's value as the reading for the day
@login_required
def ecalc():
    con = sqlite3.connect('rolsa.db')
    cur = con.cursor()
    reading0 = request.form.get('energy0')      # First form input
    reading1 = request.form.getlist('energy1')      # All the inputs created through javascript
    if reading0 == None:        # If First input is disabled use the others
        reading1 = request.form.getlist('energy1')
        newreading1 = []
        for i in reading1:
            if i != '':     # Creates a list with all the results by going through each tuple in reading1 and appending the value itself to newreading1
                newi = float(i)
                newreading1.append(newi)
        total = round(sum(newreading1), 2)      # totals and rounds the values
    else:
        total = reading0
    cur.execute("INSERT INTO energy (date, user_ID, usage) VALUES (?, ?, ?)", (date.today(), current_user.get_id(), total))
    con.commit()
    return redirect(url_for("energy"))

@app.route('/carbon-footprint')
@login_required
def footprint():
    con = sqlite3.connect('rolsa.db')
    con.row_factory = lambda cursor, row: row[0]
    cur = con.cursor()
    cur.execute("SELECT * FROM footprint WHERE user_ID = (?) AND date = (?)", (current_user.get_id(), date.today()))        # checks if there is a record for today
    completed = cur.fetchone()
    cur.execute("SELECT date FROM footprint WHERE user_ID = (?)", (current_user.get_id(),))     # fetches dates for use in chart in the footprint.html
    x = cur.fetchall()
    cur.execute("SELECT usage FROM footprint WHERE user_ID = (?)", (current_user.get_id(),))    # fetches footprint data for use in chart in the footprint.html
    y = cur.fetchall()
    if completed == None:       # depending on whether there is a record for today, the html page will load differently
        return render_template("footprint.html", x = x, y = y)
    else:
        return render_template("footprint.html", completed = True, x = x, y = y)

@app.route('/carbon-footprint', methods=['POST'])       # calculates the carbon emissions using carbon emission factors from https://www.carbonindependent.org/15.html as well as 
@login_required
def fcalc():
    con = sqlite3.connect('rolsa.db')
    cur = con.cursor()

    elec = request.form["electric"]
    elec = int(elec) * 0.22535
    gas = request.form["gas"]
    gas = int(gas) * 0.203
    coal = request.form["coal"]
    coal = int(coal)*3.26
    wood = request.form["wood"]
    wood = int(wood) * 0.10
    total = elec + gas + coal + wood

    cur.execute("INSERT INTO footprint (date, user_ID, usage) VALUES (?,?,?)", (date.today(), current_user.get_id(), total))
    con.commit()
    return redirect(url_for('footprint'))

class User(UserMixin):      # user class for logging in and staying logged in
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password
        self.authenticated = False
        def is_active(self):
            return self.is_active()
        def is_anonymous(self):
            return False
        def is_authenticated(self):
            return self.authenticated
        def is_active(self):
            return True
        def get_id(self):
            return self.id
        
@app.route('/register')
def registerscreen():
    return render_template("register.html")

@app.route('/register', methods=['POST'])       # Account registration
def register():
    password = request.form["password"]
    confirmpass = request.form["confirmpass"]
    if password != confirmpass:
        flash('Passwords are not the same, please try again')
        return render_template("register.html")
    email = request.form["email"]
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')       # Salts and hashes the password for security
    token = generate_token(email)       # Generate a token with the email for use with confirmation

    smtp_server = "smtp.gmail.com"      # Server used for Email
    smtp_port = 587
    
    msg = MIMEMultipart()       # Create Email
    msg['From'] = "rolsatechconfirmation@gmail.com"
    msg['To'] = email
    msg['Subject'] = "Email Confirmation"
    msg.attach(MIMEText(("Thank you for registering, please follow this link http://127.0.0.1:5000/confirm/"+str(token)+" and enter the following code into the space provided "+str(hashed_password))+". If this wasn't you, please ignore this Email", 'plain'))      # this is the email content
    server = smtplib.SMTP(smtp_server, smtp_port)       # Set up link to Email
    server.starttls()
    server.login('rolsatechconfirmation@gmail.com', 'bkrs fror pses ecgy')      # Login
    server.sendmail('rolsatechconfirmation@gmail.com', email, msg.as_string())
    server.quit()

    return redirect(url_for('loginscreen'))

@app.route('/confirm/<token>')
def confirm(token):
    return render_template("confirm.html", mail = token)

@app.route('/confirm/<token>', methods=['POST'])
def confirm_email(token):
    try:
        email = confirm_token(token)        # Checks whether token has expired (30 after initial creation)
    except:
        flash('Link is invalid or has expired')
        return redirect(url_for('registerscreen'))
    hash = request.form["pass_hash"]
    con = sqlite3.connect("rolsa.db")
    cur = con.cursor()
    cur.execute("INSERT INTO login (email, password) VALUES (?,?)", (email, hash))      # Registers user to database
    con.commit()
    return redirect(url_for('loginscreen'))

@app.route('/login')
def loginscreen():
    if current_user.is_authenticated:       # if already logged in, the user is just sent to the booking page
        return redirect(url_for('bookings'))
    else:
        return render_template("login.html")

@app.route('/login', methods=['GET','POST'])        # login
def login():
    email = request.form["email"]
    password = request.form["password"]
    con = sqlite3.connect("rolsa.db")
    curs = con.cursor()
    curs.execute("SELECT * FROM login WHERE email = (?)", (email,))
    details = curs.fetchone()       # checks whether email is in the database
    if details == None:
        flash('Email or Password may be incorrect. Please reattempt login')
        return render_template("login.html")
    user = list(details)
    liUser = User(int(user[0]), user[1], user[2])
    check = bcrypt.check_password_hash(liUser.password, password)
    if check and email == liUser.email:     # if email and password match the database it logs the user in
        login_user(liUser, remember=request.form.get('remember'))
        redirect(url_for('bookings'))
    else:
        flash('Email or Password may be incorrect. Please reattempt login')
        return render_template("login.html")
    return redirect(url_for('bookings'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))

app.debug = True
app.run()
