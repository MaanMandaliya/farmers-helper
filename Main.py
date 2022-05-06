from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail
import json
import os
import math
from datetime import datetime


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
local_server = True
app.secret_key = 'super-secret-key'
app.config["upload_file"] = params["upload_location"]
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Register(db.Model):
    __tablename__ = "register"
    register_id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(15), nullable=False)
    lastname = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    occupation = db.Column(db.String(20), nullable=False)
    dateofbirth = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20),nullable=False)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50),nullable=False)
    message = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    email = db.Column(db.String(20), primary_key=True ,nullable=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/blog')
def blog():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "/blog"
        next = "/blog?page="+ str(page+1)
    elif(page==last):
        prev = "/blog?page=" + str(page - 1)
        next = "/blog"
    else:
        prev = "/blog?page=" + str(page - 1)
        next = "/blog?page=" + str(page + 1)

    return render_template('blog.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/services/<string:service>",methods=["GET"])
def services(service):
    if service == "disease":
        return render_template("disease.html")
    else:
        return render_template("index.html")

@app.route('/success', methods = ['GET','POST'])
def success():
    if request.method == 'POST':
        f = request.files['file1']
        f.save(os.path.join(app.config["upload_file"], secure_filename(f.filename)))
        from disease_detection import build
        filepath = os.path.join(app.config["upload_file"], secure_filename(f.filename))
        result = build(filepath)
        return result

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts = posts)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            #set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts = posts)
    return render_template('login.html', params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/userlogin", methods = ["GET","POST"])
def userlogin():
    if request.method=='POST':
        email = request.form.get('uname')
        password = request.form.get('pass')
        user = Register.query.filter_by(email=email).first()
        if not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('userlogin'))
        return redirect(url_for('home'))
    return render_template('userlogin.html',params=params)

@app.route("/userregister", methods=["GET","POST"])
def userregister():
    if (request.method == 'POST'):
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        gender = request.form.get('gender')
        occupation = request.form.get('occupation')
        dateofbirth = request.form.get('dob')
        address = request.form.get('address')
        contact = request.form.get('contact')
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)
        entry = Register(firstname=firstname, lastname=lastname, gender=gender, occupation=occupation,
                         dateofbirth=dateofbirth, address=address, contact=contact, email=email,
                         password=password_hash)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("Welcome to Farmer's helper",
                          sender='thefarmerhelper@gmail.com',
                          recipients=[email],
                          body="Hello " + firstname + " Thanks for registring with farmer's helper " + "please visit the website for more details http://127.0.0.1:5000/"
                          )
        return redirect(url_for('userlogin'))
    return render_template('userregister.html', title="register", params=params)

@app.route("/contact",methods=['GET','POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, subject=subject, message=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + email + ' about ' + subject,
                      sender='thefarmerhelper@gmail.com',
                      recipients=['dmakwana503@gmail.com'],
                      body=message + " from " + name
                      )
    return render_template('index.html',params=params)

@app.route("/newsletter",methods=['GET','POST'])
def newsletter():
    email = request.form.get('email')
    entry = Newsletter(email=email)
    db.session.add(entry)
    db.session.commit()
    return render_template('index.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

app.run(debug=False)
