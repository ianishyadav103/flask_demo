#docs: https://flask.palletsprojects.com/
#all the py files can be named anything
import secrets
from flask import Flask, render_template, request, redirect, jsonify, flash,url_for,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, current_user,login_required ,logout_user
from datetime import timedelta

app = Flask(__name__) #link: https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application

app.config['SECRET_KEY'] =  secrets.token_hex() #few features won't work without setting key, like: flash etc.
# app.permanent_session_lifetime = timedelta(minutes=5) #setting lifetime of session: calculated from last modified #default is 31 days

#database#############################################################################################
app.config ['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:0080@:3306/mydb'
db = SQLAlchemy(app) #creating instance of SQLAlchemy Class
#here connector neccesary for mysql: here using pip install mysql-connector-python but mysqlclient in better
#rest content in models.py
'''
sqlalchemy
link: https://flask-sqlalchemy.palletsprojects.com/ OR link:https://docs.sqlalchemy.org/
=>pip install flask-sqlalchemy: Using raw SQL in Flask web applications to perform CRUD operations on database can be tedious. Instead, SQLAlchemy, a Python toolkit is a powerful OR Mapper that gives application developers the full power and flexibility of SQL. 

'''
class User(UserMixin,db.Model): #UserMixin will add Flask-Login attributes to the model so that Flask-Login will be able to work with it.
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True,nullable=False)
    password = db.Column(db.String(100),nullable=False) #Note: Storing passwords in plaintext is considered a poor security practice. You will generally want a complex hashing algorithm and salt to keep passwords secure.
    name = db.Column(db.String(1000),nullable=False)
    to_do = db.relationship('Todo', backref='user') #for relationship:parent #backred allow access todo using user #Todo is class name not table name


from datetime import datetime
class Todo(db.Model):  #table nam = converting the CamelCase class name to snake_case.
    sno = db.Column(db.Integer,primary_key=True) #by default automincreament
    title = db.Column(db.String(150),nullable = False)
    desc = db.Column(db.String(600),nullable = False)
    status = db.Column(db.Boolean,nullable = False,default= False)
    date_created = db.Column(db.DateTime,default=datetime.now())
    user_idx = db.Column(db.Integer, db.ForeignKey('user.id'))#for relationship:children


    def __repr__(self) -> str: #what to see when object printed
        return f"{self.sno} - {self.title}"
    
    
    


'''
creating tables (same as migrating of django): 
# drop_all() exists

=>using flask shell
flask shell  
with app.app_context():
    db.create_all() #creates tables

----------------------

=>using python
python
from app import app,db
app.app_context().push()
db.create_all() #creates tables
'''
#FORMS + CSRF ######################################################################################

'''
FLASK FORM AND CSRF
pip intstall flask-wtf link:https://wtforms.readthedocs.io/
'''
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import (StringField,EmailField,PasswordField)
from wtforms.validators import InputRequired, Length
csrf = CSRFProtect(app) #not by default all forms should implement csrf_token else error
##flask form
class MySignupForm(FlaskForm): #see demo pf this in signup
    email = EmailField('Email address',validators=[InputRequired(), Length(min=10, max=100)])
    name    = StringField('Name', validators=[InputRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=10, max=100)])

##model form
#URLS + VEWS #######################################################################################

#auth: pip install flask-login =>manage user sessions
login_manager = LoginManager(app)
login_manager.login_view = 'loginx' #login page
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))# since the user_id is just the primary key of our user table, use it in the query for the user

@app.route("/")
@login_required #protecting route #should be below route decorator #send flash internally:('message', 'Please log in to access this page.')
def home():
    # return "Hello World" #returns text
    # temp_todo = Todo.query.all() #python list of objects returned
    temp_todo = Todo.query.filter_by(user_idx=current_user.id)
    print(temp_todo)

    # print(temp_todo[0].title) #accessing value
    
    return render_template("index.html",all_todo = temp_todo,hii="No Records",name=current_user.name) #passing data to template
    #htmlescaping is enabled by default
    ##add | safe like: {{ var | safe }} to disable htmlescaping for that var
    #link for templates jinja: https://jinja.palletsprojects.com



@app.route("/login")
def loginx():
    return render_template("login.html")


#issue when using same link: reload ask user whether they want to resubmit
@app.route("/signupx", methods=['POST','GET'])
def signupx_p():
    formy = MySignupForm() # form instance created
    if(request.method == 'POST' and formy.validate_on_submit()): #check valid #if invalid form instance filled with error messages
        temp_user = User(email=request.form['email'],name=request.form['name'],password = generate_password_hash(request.form['password'], method='sha256'))
        db.session.add(temp_user)
        try:
            db.session.commit()
        except IntegrityError:
            flash('Email address already exists')
            db.session.rollback() #actually this not doing much here as session is not required later in this function
            return render_template("signup.html",formx = formy)
        return redirect('/login')
        # return redirect(url_for('loginx')) #same as above
    
    return render_template("signup.html",formx = formy) #pasing form: with 'errors and filled data' OR 'empty form'



@app.route("/login_p", methods=['POST'])
def loginx_p():
    temp_user = User.query.filter_by(email=request.form['email']).first()
    if not temp_user or not check_password_hash(temp_user.password, request.form['password']):
        flash('Invalid Credentials')
        return redirect('/login')
    else:
        login_user(temp_user) #login user #remember: whther to remeber user after session expires :)
        return redirect(url_for('home'))
    

@app.route("/logoutx")
def logoutx():
    session.pop('myvisit', None) # remove the myvisit from the session if it's there
    logout_user()
    return redirect('/login')

    
'''
SESSIONS
Types
-->Client-side - sessions are stored client-side in browser cookies(implemented in above func below and above) 
    #flask has built in supports to client side
    #limited by the size of the cookie (usually 4 KB)
    #cannot be immediately revoked by the Flask app
    #not suitable for sensitive data
-->Server-side - sessions are stored server-side (typically a session identifier is then created and stored client-side in browser cookies)
    #pip install
    #Increased complexity since session state must be managed
    #Sessions can easily be terminated by the Flask app
    #Sensitive data can be stored
'''

#form procesing
##manual
@app.route("/addnotes")
@login_required
def addnotes():
    c = session.get('myvisit') #default: None #accessing session myvisit
    if(c!=None):
        c+=1
        session['myvisit'] = c
    else:
        c= 1
        session['myvisit'] = c #setting session myvisit
    session.permanent=True #If set to True the session lives for permanent_session_lifetime seconds.If set to False (which is the default) the session will be deleted when the user closes the browser.
    return render_template("addnotes.html",name=current_user.name,youvisited=c)
''' 
 Be advised that modifications on mutable structures are not picked up automatically, in that situation you have to explicitly set the attribute to True. Here an example:
        # session['cart_items'].append(42)
        # session.modified = True
'''
    

@app.route("/savenotes", methods=['POST','GET']) #allowing only POST
@login_required
def savenotes():
    if(request.method == 'POST'):
        # temp_todo = Todo(title=request.form['title'],desc=request.form['desc'],user = current_user)
        temp_todo = Todo(title=request.form['title'],desc=request.form['desc'],user_idx = current_user.id) #works same as above commented
        db.session.add(temp_todo)
        db.session.commit()
        flash('Notes Added!', 'mysuccess') #whenver template returned, this will be returned
    return redirect('/')


#alternative of below: flask_restful
@app.route('/task/<string:op>/<int:idx>/') #url converters: <int:num>
@login_required
def edit_or_delete(op,idx):
    temp_todo = Todo.query.filter_by(sno=idx,user_idx=current_user.id).first() #primary key 
    #extra: get gives none if not found and get_one gives error
    if(temp_todo):
        if(op[0]=='e'):
            temp_todo.status= int(op[1])
            db.session.add(temp_todo)
            db.session.commit()
            return jsonify({'data': "e"})
        elif(op=='d'):
            db.session.delete(temp_todo)
            db.session.commit()
            return jsonify({'data': "d"})
    
    return jsonify({'data': "Some error Occured"}) 
'''
FLASK built in url converters:
string:	Accepts any text without a slash (the default: <op>).
int:	Accepts integers.
float:	Like int but for floating point values.
path:	Like string but accepts slashes.
'''


#Flask-Mail link: https://flask-mail.readthedocs.io
from flask_mail import Mail, Message
#cofigure
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'asianman78607@gmail.com'
app.config['MAIL_PASSWORD'] = 'vlok dzht bsqy oymz'
app.config['MAIL_USE_TLS'] = True

mail = Mail(app) # instantiate the mail class


'''
SIGNALS: Signals are a lightweight way to notify subscribers of certain events during the lifecycle of the application and each request. When an event occurs, it emits the signal, which calls each subscriber.
e.g->Sending mail to user when thier comment verified
'''
from blinker import Namespace


event_signals = Namespace()
speakers_modified = event_signals.signal('Your Comment App')#creating named signals

# @speakers_modified.connect #subscribing to signal using decrator
def send_mail(senderx,**kwargs):
   msg = Message(f'All Senders', sender = 'asianman78607@gmail.com', recipients = ['iavnishyadav07@gmail.com'])
   msg.body = "This ia Test mail for signal testing"
   mail.send(msg)
   return "Sent"

# @speakers_modified.connect
def send_mail2(senderx,**kwargs):
   msg = Message('Only 11', sender = 'asianman78607@gmail.com', recipients = ['iavnishyadav07@gmail.com'])
   msg.body = f"This ia Test mail for signal testing{kwargs}"
   mail.send(msg)
   return "Sent"


speakers_modified.connect(send_mail)#subscribing to signal without decorator args: (receiver*,sender=Any,weak=True) #triggered for all senders with speakers_modified.send
speakers_modified.connect(send_mail2,11) #triggered when sender is 11 with speakers_modified.send

#emitting signal: place these elsewhere else won't execute: we know that
# speakers_modified.send("Avnish")  args: (sender*,kwars_data) 
# speakers_modified.send(11,a="B",c=11)



#RUN###############################################################################################

# print(app.config) #FYIO

#this block of code should be at end
if __name__ == "__main__": 
    app.run(debug=True,port=8000)   
    #default porrt: 5000
    #when port chnaged resart server manually 


######################################################
# see for code spilitting: https://flask.palletsprojects.com/en/3.0.x/tutorial/layout/ and https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login and rememebr blueprint

'''
PRODUCTION
#Do not use the development server when deploying to production. 
link: https://flask.palletsprojects.com/en/3.0.x/deploying/gunicorn/
#pip install gunicorn
++++More to come

''' 