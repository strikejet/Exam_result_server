import flask_login
import math
import random
from datetime import timedelta
from flask import Flask, request, flash, render_template, url_for, redirect, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)

app.secret_key = "shrikant"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:einstein1729@127.0.0.1:5432/result_server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# export mysql+pymysql://root:einstein1729@127.0.0.1:3306/result_server = postgres
# mysqldump -h<host> --compatible=postgresql -u<user> -p <database_name> > /tmp/my_dump.sql


db = SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = "Session time-out, please re-login"
login_manager.needs_refresh_message_category = "info"

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'pandhareshrikant99@gmail.com'
app.config['MAIL_PASSWORD'] = 'Shrikant@1999'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


class StudentInfo(UserMixin, db.Model):
    __tablename__ = "info"       # noqa
    name = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    student_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    password = Column(String(500), nullable=False)
    token = Column(Integer, nullable=True)
    role = Column(String(10), nullable=False)
    email = Column(String(50), nullable=False)
    marks = relationship("Marks", back_populates="studentinfo", lazy="joined")

    def __init__(self, name, gender, student_id, password, token, role, email):
        self.student_id = student_id
        self.name = name
        self.gender = gender
        self.token = token
        self.role = role
        self.email = email
        self.password = password

    def is_active(self):
        return True

    def get_id(self):
        return self.student_id

    def is_authenticated(self):
        return self.authenticated

    def __repr__(self):
        return '<User {}>'.format(self.student_id)


class Marks(db.Model):
    __tablename__ = 'marks'   # noqa
    aptitude = Column(Integer, nullable=True)
    coding = Column(Integer, nullable=True)
    mathematics = Column(Integer, nullable=True)
    verbal = Column(Integer, nullable=True)
    student_id = Column(Integer, ForeignKey("info.student_id"), primary_key=True, nullable=False)
    studentinfo = relationship("StudentInfo", back_populates="marks", lazy="joined")


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)


@login_manager.user_loader
def load_user(given_id):
    student = StudentInfo.query.join(Marks).filter(StudentInfo.student_id == given_id).first()
    if student:
        return student
    return None


@app.route('/result', methods=["GET"])
@login_required
def result():
    marks = current_user.marks
    return render_template('result.html', marks=marks)


@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        given_id = request.form.get('student_id', type=int)
        given_password = request.form.get('password', type=str)

        if given_id and given_password:
            # query = "SELECT * FROM info where stud_id=?
            student = StudentInfo.query.filter(
                StudentInfo.student_id == given_id and StudentInfo.password == given_password).first()
            if not student:
                flash("Give Proper Credentials")
                return render_template('login.html')

            if student.password == given_password:
                session["student_id"] = given_id
                session["student_email"] = student.email
                generated_otp = generate_otp()
                if generated_otp:
                    msg = Message(subject='OTP', sender='pandhareshrikant99@gmail.com',
                                  recipients=[session.get("student_email")])
                    session['otp'] = generated_otp
                    msg.body = "The OTP for Fynd Academy Exam Result is = " + generated_otp
                    mail.send(msg)
                    return redirect(url_for('validate_otp'))

        else:
            flash("Student ID should be a number")
            render_template('login.html')

    return render_template('login.html')


@app.route('/otp', methods=["GET", "POST"])
def validate_otp():
    if request.method == "POST":
        given_otp = request.form.get("otp", type=str)
        student = StudentInfo.query.filter(StudentInfo.student_id == session.get("student_id")).first()
        if given_otp == session.get("otp"):
            login_user(student)
            session["email"] = student.email
            return render_template('result.html', marks=student.marks)
        else:
            flash("You have entered wrong OTP. Try again with correct credentials")
            return redirect((url_for('login')))
    return render_template('otp.html')


@app.route('/students', methods=['GET'])
def get_all():
    return render_template('all_students.html', StudentInfo=StudentInfo)


def generate_otp():
    char_string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    otp = ""
    length = len(char_string)
    for i in range(4):
        otp = otp + char_string[math.floor(random.random() * length)]
    return otp


@app.route('/send_result', methods=["POST"])
@login_required
def send_result():
    attach_template = render_template('email_result.html')
    msg = Message(subject='OTP', sender='pandhareshrikant99@gmail.com', recipients=[session.get("student_email")])
    msg.body = "Your result for Fynd Academy Entrance Exam"
    msg.attach("Fynd_Result", content_type="text/html", data=attach_template)
    mail.send(msg)
    logout_user()
    session.clear()
    return redirect(url_for('login'))


# db.create_all()   ---- If you are using it for first time with no database creation
# db.session.commit()
app.run(port=5000, debug=True)
